from django.conf import settings
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.db import DatabaseError
from unittest.mock import patch

from .models import Comment, ConsumedCommentNonce
from .views import _client_ip


class ClientIPResolutionTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @override_settings(COMMENTS_TRUST_PROXY_HEADERS=True, COMMENTS_TRUSTED_PROXY_IPS=())
    def test_ignores_forwarded_header_without_proxy_allowlist(self):
        request = self.factory.get(
            "/", REMOTE_ADDR="203.0.113.10",
            HTTP_X_FORWARDED_FOR="198.51.100.44",
        )
        self.assertEqual(_client_ip(request), "203.0.113.10")

    @override_settings(
        COMMENTS_TRUST_PROXY_HEADERS=True,
        COMMENTS_TRUSTED_PROXY_IPS=("10.0.0.0/8",),
    )
    def test_walks_forwarded_chain_from_right_and_skips_trusted_proxies(self):
        request = self.factory.get(
            "/", REMOTE_ADDR="10.0.0.8",
            HTTP_X_FORWARDED_FOR="198.51.100.44, 10.0.0.7",
        )
        self.assertEqual(_client_ip(request), "198.51.100.44")

    @override_settings(
        COMMENTS_TRUST_PROXY_HEADERS=True,
        COMMENTS_TRUSTED_PROXY_IPS=("10.0.0.0/8",),
    )
    def test_ignores_header_from_untrusted_remote_peer(self):
        request = self.factory.get(
            "/", REMOTE_ADDR="203.0.113.10",
            HTTP_X_FORWARDED_FOR="198.51.100.44",
        )
        self.assertEqual(_client_ip(request), "203.0.113.10")

    @override_settings(
        COMMENTS_TRUST_PROXY_HEADERS=True,
        COMMENTS_TRUSTED_PROXY_IPS=("10.0.0.0/8",),
    )
    def test_malformed_forwarded_chain_falls_back_to_remote_addr(self):
        request = self.factory.get(
            "/", REMOTE_ADDR="10.0.0.8",
            HTTP_X_FORWARDED_FOR="not-an-ip, 198.51.100.44",
        )
        self.assertEqual(_client_ip(request), "10.0.0.8")


class CommentEndpointAccessTests(TestCase):
    """Форма и добавление комментария доступны только для live, public страниц
    ТЕКУЩЕГО Wagtail Site (координатор, 2026-11-05).

    Тесты предполагают запуск в хост-проекте: URLs /comments/* включены в
    urlconf (vsproject/urls.py), дефолтный Wagtail Site из миграций
    перепривязывается на hostname 'testserver' (хост тестового клиента).
    """

    @classmethod
    def setUpTestData(cls):
        from django.contrib.auth import get_user_model
        from wagtail.models import Page, PageViewRestriction, Site

        User = get_user_model()
        cls.user = User.objects.create_user(
            username="commenter", password="commenter-pass"
        )

        # Дефолтный сайт из миграций Wagtail -> hostname тестового клиента,
        # корневая страница остаётся штатной "Welcome to your new Wagtail site!"
        cls.site = Site.objects.get(is_default_site=True)
        cls.site.hostname = "testserver"
        cls.site.save()
        cls.root = cls.site.root_page

        cls.public_page = Page(title="Public page", slug="public-page", live=True)
        cls.root.add_child(instance=cls.public_page)

        cls.draft_page = Page(title="Draft page", slug="draft-page", live=False)
        cls.root.add_child(instance=cls.draft_page)

        cls.restricted_page = Page(
            title="Restricted page", slug="restricted-page", live=True
        )
        cls.root.add_child(instance=cls.restricted_page)
        PageViewRestriction.objects.create(
            page=cls.restricted_page, restriction_type="login"
        )

        # Второй сайт с собственной корневой страницей (страница "чужого" сайта)
        other_root = Page(title="Other site root", slug="other-root", live=True)
        Page.get_first_root_node().add_child(instance=other_root)
        cls.other_site = Site.objects.create(
            hostname="other.example.com",
            root_page=other_root,
            is_default_site=False,
            site_name="Other site",
        )
        cls.other_page = Page(title="Other site page", slug="other-page", live=True)
        other_root.add_child(instance=cls.other_page)

    def _form_token(self, page_id):
        """GET формы -> значение hidden input form_token (подписанный токен)
        и сам ответ (для проверки 200)."""
        import re

        response = self.client.get(f"/comments/form/{page_id}/")
        m = re.search(r'name="form_token"[^>]*value="([^"]+)"', response.content.decode())
        return (m.group(1) if m else None), response

    def _backdated_form_token(self, page_id, age_seconds=10):
        """Управляемое время вместо физического sleep.

        clean_form_token отклоняет токены с age < 4 c («отправлено слишком
        быстро»). Вместо ожидания подписываем валидный токен с issued_at в
        прошлом — та же соль и структура payload, что у PublicCommentForm
        (forms.py, salt="wagtail_mptt_comments.form").
        """
        # Establish the per-browser CSRF secret used to scope replay nonces.
        self.client.get(f"/comments/form/{page_id}/")
        import secrets
        import time

        from django.core import signing

        return signing.dumps(
            {
                "page_id": page_id,
                "nonce": secrets.token_urlsafe(18),
                "issued_at": time.time() - age_seconds,
            },
            salt="wagtail_mptt_comments.form",
        )

    # --- GET /comments/form/<page_id>/ ---

    def test_lazy_form_fragment_ensures_csrf_cookie(self):
        response = self.client.get(f"/comments/form/{self.public_page.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(settings.CSRF_COOKIE_NAME, response.cookies)

    @override_settings(COMMENTS_RATE_LIMIT=0)
    def test_invalid_rate_limit_configuration_fails_closed_with_503(self):
        self.client.force_login(self.user)
        token = self._backdated_form_token(self.public_page.pk)
        response = self.client.post(
            f"/comments/add/{self.public_page.pk}/",
            {"content": "Valid comment", "parent": "", "form_token": token},
        )
        self.assertEqual(response.status_code, 503)
        self.assertFalse(Comment.objects.filter(page_id=self.public_page.pk, content="Valid comment").exists())

    @patch("wagtail_mptt_comments.views._rate_limited", side_effect=DatabaseError("rate table unavailable"))
    def test_rate_limit_storage_error_fails_closed_with_503(self, _mock_rate_limit):
        self.client.force_login(self.user)
        token = self._backdated_form_token(self.public_page.pk)
        response = self.client.post(
            f"/comments/add/{self.public_page.pk}/",
            {"content": "Valid comment", "parent": "", "form_token": token},
        )
        self.assertEqual(response.status_code, 503)
        self.assertFalse(Comment.objects.filter(page_id=self.public_page.pk, content="Valid comment").exists())

    def test_form_on_public_page_of_current_site_200(self):
        response = self.client.get(f"/comments/form/{self.public_page.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("form_token", response.content.decode())

    def test_form_on_restricted_page_404(self):
        response = self.client.get(f"/comments/form/{self.restricted_page.pk}/")
        self.assertEqual(response.status_code, 404)

    def test_form_on_unpublished_page_404(self):
        response = self.client.get(f"/comments/form/{self.draft_page.pk}/")
        self.assertEqual(response.status_code, 404)

    def test_form_on_other_site_page_404(self):
        response = self.client.get(f"/comments/form/{self.other_page.pk}/")
        self.assertEqual(response.status_code, 404)

    def test_form_on_nonexistent_page_404(self):
        response = self.client.get("/comments/form/999999/")
        self.assertEqual(response.status_code, 404)

    # --- POST /comments/add/<page_id>/ ---

    def test_add_comment_on_public_page_still_works(self):
        """Обычная отправка комментария на публичной странице текущего сайта."""
        self.client.force_login(self.user)
        token = self._backdated_form_token(self.public_page.pk)
        response = self.client.post(
            f"/comments/add/{self.public_page.pk}/",
            {"content": "Тест комментария", "parent": "", "form_token": token},
        )
        # success -> redirect на страницу (302); ошибки валидации -> 302 + has_errors=1
        self.assertEqual(response.status_code, 302)
        self.assertNotIn(b"has_errors=1", response["Location"].encode())
        self.assertTrue(
            Comment.objects.filter(page_id=self.public_page.pk, content="Тест комментария").exists()
        )

    def test_add_comment_on_restricted_page_404(self):
        """Подстановка page_id закрытой страницы не создаёт комментарий."""
        self.client.force_login(self.user)
        response = self.client.post(
            f"/comments/add/{self.restricted_page.pk}/",
            {"content": "не должно сохраниться", "parent": "", "form_token": "x"},
        )
        self.assertEqual(response.status_code, 404)
        self.assertFalse(Comment.objects.filter(page_id=self.restricted_page.pk).exists())

    def test_add_comment_on_other_site_page_404(self):
        """Подстановка page_id страницы другого сайта -> 404."""
        self.client.force_login(self.user)
        response = self.client.post(
            f"/comments/add/{self.other_page.pk}/",
            {"content": "не должно сохраниться", "parent": "", "form_token": "x"},
        )
        self.assertEqual(response.status_code, 404)
        self.assertFalse(Comment.objects.filter(page_id=self.other_page.pk).exists())

    def test_invalid_fields_do_not_consume_valid_form_token(self):
        """A typo in another field must not force the visitor to reload the form."""
        self.client.force_login(self.user)
        token = self._backdated_form_token(self.public_page.pk)
        invalid = self.client.post(
            f"/comments/add/{self.public_page.pk}/",
            {"content": "bad", "parent": "", "form_token": token},
        )
        self.assertEqual(invalid.status_code, 302)
        self.assertIn("has_errors=1", invalid["Location"])
        self.assertEqual(ConsumedCommentNonce.objects.count(), 0)

        valid = self.client.post(
            f"/comments/add/{self.public_page.pk}/",
            {"content": "Исправленный комментарий", "parent": "", "form_token": token},
        )
        self.assertEqual(valid.status_code, 302)
        self.assertNotIn("has_errors=1", valid["Location"])
        self.assertTrue(
            Comment.objects.filter(
                page_id=self.public_page.pk,
                content="Исправленный комментарий",
            ).exists()
        )
        self.assertEqual(ConsumedCommentNonce.objects.count(), 1)

    def test_add_comment_replay_same_form_token_rejected(self):
        """Повторная отправка с тем же form_token отклоняется (session nonces)."""
        self.client.force_login(self.user)
        token = self._backdated_form_token(self.public_page.pk)
        payload = {"content": "первый", "parent": "", "form_token": token}
        first = self.client.post(f"/comments/add/{self.public_page.pk}/", payload)
        self.assertEqual(first.status_code, 302)
        self.assertNotIn(b"has_errors=1", first["Location"].encode())
        replay = self.client.post(f"/comments/add/{self.public_page.pk}/", payload)
        self.assertEqual(replay.status_code, 302)  # ошибка token_replayed -> redirect has_errors=1
        self.assertIn(b"has_errors=1", replay["Location"].encode())
        self.assertEqual(
            Comment.objects.filter(page_id=self.public_page.pk, content="первый").count(), 1
        )
