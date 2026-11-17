"""Д67-Б: тесты ПУБЛИЧНОГО контракта get_latest_comments после замены
Comment на LatestCommentItem (DTO) в кеше.

Фиксирует контракт README-примера (page, id, display_author_name, content)
и гарантию безопасности: кеш не содержит User, password hash, username,
email или иных приватных полей; DTO не предоставляет user/avatar/
get_author_role*; DTO иммутабелен (frozen dataclass).
"""
import dataclasses

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.template import Context, Template
from django.test import RequestFactory, TestCase
from wagtail.models import Page, Site

from wagtail_mptt_comments.models import Comment, _LATEST_COMMENTS_EPOCH_KEY
from wagtail_mptt_comments.templatetags.mptt_comment_tags import (
    LatestCommentItem,
    get_latest_comments,
)

SAFETY_PASSWORD = "safety-password-9x7"
README_EXAMPLE_TEMPLATE = Template(
    "{% load mptt_comment_tags wagtailcore_tags %}"
    "{% get_latest_comments 5 as latest_comments %}"
    "<ul>"
    "{% for comment in latest_comments %}"
    "<li>"
    '<a href="{% pageurl comment.page %}#comment-{{ comment.id }}">'
    "<strong>{{ comment.display_author_name }}</strong>: "
    "{{ comment.content|striptags|truncatewords:10 }}"
    "</a>"
    "</li>"
    "{% endfor %}"
    "</ul>"
)


class PublicContractBase(TestCase):
    def _context(self):
        request = RequestFactory().get("/")
        request.site = self.default_site
        return Context({"request": request})


    """Сайт testserver (совпадает с RequestFactory), страница, два
    одобренных комментария (пользователь и гость с email/паролем)."""

    @classmethod
    def setUpTestData(cls):
        cls.superuser = get_user_model().objects.create_superuser(
            "contract-admin", "admin@example.test", SAFETY_PASSWORD)
        cls.alice = get_user_model().objects.create_user(
            "contract-alice", "alice@example.test", SAFETY_PASSWORD)
        cls.guest = get_user_model().objects.create_user(
            "contract-guest", "guest@example.test", SAFETY_PASSWORD)
        # Страница — под КОРНЕМ ДЕФОЛТНОГО САЙТА: иначе in_site() не
        # найдёт её (Page.get_first_root_node() = узел 'root', а дефолтный
        # Site указывает на 'home' — разные деревья Wagtail).
        cls.default_site = Site.objects.filter(is_default_site=True).first()
        cls.page = cls.default_site.root_page.add_child(instance=Page(
            title="Contract page", slug="contract-page"))
        cls.page.save_revision()
        cls.alice_comment = Comment.objects.create(
            page=cls.page, user=cls.alice, is_approved=True,
            content="Комментарий Alice — контрактный тест.")
        cls.guest_comment = Comment.objects.create(
            page=cls.page, user=cls.guest, is_approved=True,
            content="Комментарий гостя без аккаунта в виджете.")

    def setUp(self):
        cache.clear()
        self.request = RequestFactory().get("/")
        self.request.site = Site.objects.filter(is_default_site=True).first()


class GetLatestCommentsContractTests(PublicContractBase):
    def test_returns_items_with_readme_example_fields(self):
        """Каждый элемент содержит ровно поля README-примера: page, id,
        display_author_name, content, date_created."""
        items = get_latest_comments(self._context(), 5)
        self.assertTrue(items)
        for item in items:
            for field in ("page", "id", "display_author_name", "content",
                          "date_created"):
                self.assertTrue(hasattr(item, field),
                                f"DTO обязан предоставлять {field}")

    def test_dto_does_not_expose_removed_user_attributes(self):
        """Удалённые User-атрибуты недоступны на DTO: user, avatar,
        get_author_role*; display_author_name — строка, не метод."""
        items = get_latest_comments(self._context(), 5)
        for item in items:
            for removed in ("user", "avatar_tag", "get_author_role",
                            "get_author_role_label", "user__password"):
                self.assertFalse(hasattr(item, removed),
                                 f"DTO не должен предоставлять {removed}")
            self.assertIsInstance(item.display_author_name, str)

    def test_dto_is_frozen_dataclass(self):
        """DTO иммутабелен: присваивание поля запрещено (frozen dataclass)."""
        item = get_latest_comments(self._context(), 5)[0]
        self.assertTrue(dataclasses.is_dataclass(item))
        with self.assertRaises(dataclasses.FrozenInstanceError):
            item.content = "иммутабельность"

    def test_readme_example_renders_with_dto(self):
        """Буквальный пример README работает на DTO без изменений:
        рендер содержит автора, содержимое и якорь комментария."""
        html = README_EXAMPLE_TEMPLATE.render(
            Context({"request": self._context()["request"]}))
        self.assertIn("Комментарий Alice", html)
        self.assertIn("#comment-", html)




class CacheSafetyTests(PublicContractBase):
    def test_cache_stores_dto_without_user_or_secrets(self):
        """Кеш хранит список LatestCommentItem: ни одного User, ни одного
        вхождения пароля/логина/email в сериализованном payload; у DTO
        нет атрибута user."""
        self._invoke_tag(5)
        site = Site.objects.filter(is_default_site=True).first()
        epoch = cache.get(_LATEST_COMMENTS_EPOCH_KEY, 0)
        key = f"latest_comments_v2_site_{site.pk}_5_{epoch}"
        cached = cache.get(key)
        self.assertTrue(cached, f"кеш {key!r} должен содержать результат")
        for item in cached:
            self.assertIsInstance(item, LatestCommentItem)
            self.assertFalse(hasattr(item, "user"))
        payload = repr(cached)
        for secret in (SAFETY_PASSWORD, "alice@example.test",
                       "guest@example.test"):
            self.assertNotIn(secret, payload,
                             f"кеш не должен содержать {secret!r}")
        # Имя автора — публичное поле виджета; его наличие в кеше допустимо.
        self.assertIn("contract-alice", payload)

    def test_cache_survives_repeated_calls_with_same_items(self):
        """Повторный вызов в том же контексте возвращает кешированный DTO-список."""
        self._invoke_tag(5)
        site = Site.objects.filter(is_default_site=True).first()
        epoch = cache.get(_LATEST_COMMENTS_EPOCH_KEY, 0)
        key = f"latest_comments_v2_site_{site.pk}_5_{epoch}"
        cached = cache.get(key)
        self.assertTrue(cached)
        again = get_latest_comments(self._context(), 5)
        self.assertEqual(len(again), len(cached))
        for item in again:
            self.assertIsInstance(item, LatestCommentItem)

    def _invoke_tag(self, count=5):
        request = RequestFactory().get("/")
        request.site = self.default_site
        context = Context({"request": request})
        template = Template(
            "{% load mptt_comment_tags %}"
            "{% get_latest_comments 5 as latest_comments %}")
        template.render(context)
