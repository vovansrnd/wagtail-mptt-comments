"""Д67-Б: тесты ПУБЛИЧНОГО контракта get_latest_comments.

Контракт: в кеше хранятся ТОЛЬКО целочисленные ID комментариев; функция
возвращает полноценные Comment instances с прежним API (user,
display_author_name(), get_author_role(), avatar_tag). Гарантии
безопасности: кеш не содержит User, password hash, username, email или
иных приватных полей; при разрешении ID заново применяются eligibility-
предикаты (approved + live/public/в текущем Site), поэтому устаревший ID
не возвращает скрытый или чужой-site комментарий.
"""
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.template import Context, Template
from django.test import RequestFactory, TestCase
from wagtail.models import Page, Site

from wagtail_mptt_comments.models import Comment, _LATEST_COMMENTS_EPOCH_KEY
from wagtail_mptt_comments.templatetags.mptt_comment_tags import (
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


    def _context(self):
        request = RequestFactory().get("/")
        request.site = self.default_site
        return Context({"request": request})

    def test_returns_comment_instances_with_full_api(self):
        """Результат — Comment-модели: полный прежний API (user,
        display_author_name(), get_author_role*) доступен на каждом элементе."""
        items = get_latest_comments(self._context(), 5)
        self.assertTrue(items)
        for item in items:
            self.assertIsInstance(item, Comment)
            self.assertTrue(hasattr(item, "user"))
            self.assertTrue(callable(getattr(item, "display_author_name")))
            self.assertTrue(callable(getattr(item, "get_author_role")))
            self.assertTrue(hasattr(item, "page"))

    def test_readme_example_renders_with_comment_models(self):
        """Буквальный пример README работает на Comment-моделях без изменений."""
        html = README_EXAMPLE_TEMPLATE.render(
            Context({"request": self._context()["request"]}))
        self.assertIn("Комментарий Alice", html)
        self.assertIn("#comment-", html)


class CacheSafetyTests(PublicContractBase):
    def test_cache_payload_contains_only_integer_ids(self):
        """Кеш хранит ТОЛЬКО список целочисленных ID: ни Comment, ни User,
        ни email, ни пароля/его хеша в сериализованном payload."""
        self._invoke_tag(5)
        site = Site.objects.filter(is_default_site=True).first()
        epoch = cache.get(_LATEST_COMMENTS_EPOCH_KEY, 0)
        key = f"latest_comment_ids_site_{site.pk}_5_{epoch}"
        cached = cache.get(key)
        self.assertTrue(cached, f"кеш {key!r} должен содержать результат")
        self.assertTrue(all(isinstance(v, int) for v in cached),
                         f"в кеше должны быть только int ID: {cached!r}")
        payload = repr(cached)
        for secret in (SAFETY_PASSWORD, "contract-alice", "contract-guest",
                       "alice@example.test", "guest@example.test"):
            self.assertNotIn(secret, payload,
                             f"кеш не должен содержать {secret!r}")

    def test_cached_ids_resolve_to_comments_in_order(self):
        """Кешированные ID разрешаются обратно в Comment в кешированном
        порядке (порядок -date_created сохраняется)."""
        self._invoke_tag(5)
        site = Site.objects.filter(is_default_site=True).first()
        epoch = cache.get(_LATEST_COMMENTS_EPOCH_KEY, 0)
        key = f"latest_comment_ids_site_{site.pk}_5_{epoch}"
        cached_ids = cache.get(key)
        self.assertTrue(cached_ids)
        by_id = {c.pk: c for c in Comment.objects.filter(pk__in=cached_ids)
                 .order_by("-date_created")}
        ordered = [by_id[i] for i in cached_ids]
        dates = [c.date_created for c in ordered]
        self.assertEqual(dates, sorted(dates, reverse=True),
                         "порядок кеша должен сохранять -date_created")

    def _invoke_tag(self, count=5):
        request = RequestFactory().get("/")
        request.site = self.default_site
        context = Context({"request": request})
        template = Template(
            "{% load mptt_comment_tags %}"
            "{% get_latest_comments 5 as latest_comments %}")
        template.render(context)

    def _invoke_tag(self, count=5):
        request = RequestFactory().get("/")
        request.site = self.default_site
        context = Context({"request": request})
        template = Template(
            "{% load mptt_comment_tags %}"
            "{% get_latest_comments 5 as latest_comments %}")
        template.render(context)
