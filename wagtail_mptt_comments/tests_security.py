from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from unittest import mock, skipUnless

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.core.management import call_command
from django.db import close_old_connections, connection
from django.test import RequestFactory, TestCase, TransactionTestCase, override_settings
from django.utils import timezone
from wagtail.models import Page, PageViewRestriction, Site

from .models import (Comment, CommentRateLimitBucket, ConsumedCommentNonce,
                     ROLE_MEMBER, _LATEST_COMMENTS_EPOCH_KEY)
from .templatetags.mptt_comment_tags import get_latest_comments
from .views import _rate_limited
from .security import CommentNonceReplayError, consume_comment_nonces


class AtomicCommentRateLimitTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def request(self, ip="203.0.113.10", user=None):
        request = self.factory.post("/comments/add/1/", REMOTE_ADDR=ip)
        request.user = user or AnonymousUser()
        return request

    def test_exact_limit_is_allowed_and_next_request_is_limited(self):
        request = self.request()
        results = [
            _rate_limited(request, "post-test", limit=3, window=60)
            for _ in range(4)
        ]
        self.assertEqual(results, [False, False, False, True])
        bucket = CommentRateLimitBucket.objects.get()
        self.assertEqual(bucket.count, 3)

    def test_expired_window_resets_atomically(self):
        request = self.request()
        self.assertFalse(_rate_limited(request, "post-test", limit=2, window=60))
        bucket = CommentRateLimitBucket.objects.get()
        CommentRateLimitBucket.objects.filter(pk=bucket.pk).update(
            window_started_at=timezone.now() - timedelta(seconds=61),
            count=2,
        )

        self.assertFalse(_rate_limited(request, "post-test", limit=2, window=60))
        bucket.refresh_from_db()
        self.assertEqual(bucket.count, 1)
        self.assertGreater(bucket.window_started_at, timezone.now() - timedelta(seconds=2))

    def test_anonymous_clients_have_separate_hashed_buckets(self):
        first = self.request(ip="203.0.113.10")
        second = self.request(ip="203.0.113.11")
        self.assertFalse(_rate_limited(first, "post-test", limit=1, window=60))
        self.assertFalse(_rate_limited(second, "post-test", limit=1, window=60))
        self.assertEqual(CommentRateLimitBucket.objects.count(), 2)
        self.assertTrue(all(len(row.key_hash) == 64 for row in CommentRateLimitBucket.objects.all()))

    def test_authenticated_accounts_are_separate_even_when_sharing_an_ip(self):
        User = get_user_model()
        first_user = User.objects.create_user(username="rate-one", password="pw")
        second_user = User.objects.create_user(username="rate-two", password="pw")
        first = self.request(ip="203.0.113.60", user=first_user)
        second = self.request(ip="203.0.113.60", user=second_user)
        self.assertFalse(_rate_limited(first, "post-test", limit=1, window=60))
        self.assertFalse(_rate_limited(second, "post-test", limit=1, window=60))
        self.assertEqual(CommentRateLimitBucket.objects.count(), 2)

    def test_same_authenticated_user_cannot_bypass_limit_by_changing_ip(self):
        User = get_user_model()
        user = User.objects.create_user(username="rate-mobile", password="pw")
        first = self.request(ip="203.0.113.62", user=user)
        second = self.request(ip="203.0.113.63", user=user)
        self.assertFalse(_rate_limited(first, "post-test", limit=1, window=60))
        self.assertTrue(_rate_limited(second, "post-test", limit=1, window=60))
        self.assertEqual(CommentRateLimitBucket.objects.count(), 1)


@skipUnless(connection.vendor == "postgresql", "Concurrent counter test requires PostgreSQL row/unique-index semantics")
class CascadeFlushMixin:
    """Flush с CASCADE: легаси-таблица blog_comment (сирота относительно
    sqlflush) ломает стандартный flush TransactionTestCase на postgres.
    Копия FlushCascadeMixin ядра (blog/tests_replay_http.py)."""

    def _fixture_teardown(self):
        from django.core.management import call_command
        call_command(
            "flush", verbosity=0, interactive=False,
            database=self._databases_names()[0],
            reset_sequences=False, allow_cascade=True,
        )


class ConcurrentCommentRateLimitTests(CascadeFlushMixin, TransactionTestCase):
    reset_sequences = True

    def test_parallel_requests_cannot_exceed_remaining_slots(self):
        workers = 8
        barrier = Barrier(workers)

        def submit():
            close_old_connections()
            try:
                request = RequestFactory().post(
                    "/comments/add/1/", REMOTE_ADDR="203.0.113.77"
                )
                request.user = AnonymousUser()
                barrier.wait(timeout=10)
                return _rate_limited(request, "parallel-test", limit=3, window=60)
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=workers) as pool:
            limited = list(pool.map(lambda _n: submit(), range(workers)))

        self.assertEqual(limited.count(False), 3)
        self.assertEqual(limited.count(True), workers - 3)
        bucket = CommentRateLimitBucket.objects.get()
        self.assertEqual(bucket.count, 3)


class CommentNonceStorageTests(TestCase):
    def test_same_nonce_is_one_time_per_csrf_secret(self):
        expires_at = timezone.now() + timedelta(hours=1)
        token = [("form", "random-nonce-value", expires_at)]

        consume_comment_nonces(token, "browser-csrf-secret-a")
        with self.assertRaises(CommentNonceReplayError):
            consume_comment_nonces(token, "browser-csrf-secret-a")

        # A shared/cached form token must remain usable by another browser.
        consume_comment_nonces(token, "browser-csrf-secret-b")
        self.assertEqual(ConsumedCommentNonce.objects.count(), 2)

    def test_multiple_nonce_insert_is_all_or_nothing(self):
        expires_at = timezone.now() + timedelta(hours=1)
        first = [("form", "first", expires_at)]
        consume_comment_nonces(first, "browser-csrf-secret")
        before = ConsumedCommentNonce.objects.count()

        # First token is new in this combined batch, second is a replay. The
        # savepoint/outer transaction must roll back the new first-token row.
        with self.assertRaises(CommentNonceReplayError):
            consume_comment_nonces(
                [
                    ("captcha", "new-captcha", expires_at),
                    ("form", "first", expires_at),
                ],
                "browser-csrf-secret",
            )
        self.assertEqual(ConsumedCommentNonce.objects.count(), before)


@skipUnless(connection.vendor == "postgresql", "Concurrent nonce test requires PostgreSQL unique-index behavior")
class ConcurrentCommentNonceTests(CascadeFlushMixin, TransactionTestCase):
    reset_sequences = True

    def test_parallel_replay_has_exactly_one_winner_per_csrf_secret(self):
        workers = 8
        barrier = Barrier(workers)
        expires_at = timezone.now() + timedelta(hours=1)

        def submit():
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                try:
                    consume_comment_nonces(
                        [("form", "same-nonce", expires_at)],
                        "same-browser-csrf-secret",
                    )
                    return True
                except CommentNonceReplayError:
                    return False
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=workers) as pool:
            outcomes = list(pool.map(lambda _n: submit(), range(workers)))

        self.assertEqual(outcomes.count(True), 1)
        self.assertEqual(outcomes.count(False), workers - 1)
        self.assertEqual(ConsumedCommentNonce.objects.count(), 1)


class CommentSecurityCleanupCommandTests(TestCase):
    def test_cleanup_removes_only_stale_buckets_and_expired_nonces_in_batches(self):
        now = timezone.now()
        old_started = now - timedelta(days=3)
        fresh_started = now - timedelta(minutes=1)
        CommentRateLimitBucket.objects.create(
            key_hash="a" * 64, window_started_at=old_started, count=3
        )
        CommentRateLimitBucket.objects.create(
            key_hash="b" * 64, window_started_at=fresh_started, count=1
        )
        ConsumedCommentNonce.objects.create(
            nonce_hash="c" * 64, expires_at=now - timedelta(seconds=1)
        )
        ConsumedCommentNonce.objects.create(
            nonce_hash="d" * 64, expires_at=now + timedelta(hours=1)
        )

        call_command("cleanup_comment_security", days=2, batch_size=1, verbosity=0)

        self.assertEqual(
            list(CommentRateLimitBucket.objects.order_by("key_hash").values_list("key_hash", flat=True)),
            ["b" * 64],
        )
        self.assertEqual(
            list(ConsumedCommentNonce.objects.values_list("nonce_hash", flat=True)),
            ["d" * 64],
        )

    @override_settings(COMMENTS_RATE_WINDOW=7 * 24 * 60 * 60)
    def test_cleanup_keeps_buckets_inside_a_long_configured_window(self):
        CommentRateLimitBucket.objects.create(
            key_hash="e" * 64,
            window_started_at=timezone.now() - timedelta(days=3),
            count=1,
        )
        call_command("cleanup_comment_security", days=2, batch_size=10, verbosity=0)
        self.assertTrue(CommentRateLimitBucket.objects.filter(key_hash="e" * 64).exists())


class LatestCommentsWidgetVisibilityTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_user(
            username="latest-writer", password="secret-password-hash-test"
        )
        cls.site = Site.objects.get(is_default_site=True)
        cls.site.hostname = "testserver"
        cls.site.save()
        cls.root = cls.site.root_page

        cls.public_page = Page(title="Visible article", slug="visible-article", live=True)
        cls.root.add_child(instance=cls.public_page)
        cls.draft_page = Page(title="Draft article", slug="draft-article", live=False)
        cls.root.add_child(instance=cls.draft_page)
        cls.restricted_page = Page(title="Private article", slug="private-article", live=True)
        cls.root.add_child(instance=cls.restricted_page)
        PageViewRestriction.objects.create(
            page=cls.restricted_page, restriction_type="login"
        )

        other_root = Page(title="Other root", slug="other-root", live=True)
        Page.get_first_root_node().add_child(instance=other_root)
        cls.other_site = Site.objects.create(
            hostname="other.example.test",
            root_page=other_root,
            is_default_site=False,
            site_name="Other site",
        )
        cls.other_page = Page(title="Other article", slug="other-article", live=True)
        other_root.add_child(instance=cls.other_page)

        cls.public_comment = Comment.objects.create(
            page=cls.public_page,
            user=cls.user,
            content="Public approved comment",
            is_approved=True,
        )
        cls.draft_comment = Comment.objects.create(
            page=cls.draft_page,
            user=cls.user,
            content="Draft page comment",
            is_approved=True,
        )
        cls.restricted_comment = Comment.objects.create(
            page=cls.restricted_page,
            user=cls.user,
            content="Restricted page comment",
            is_approved=True,
        )
        cls.other_comment = Comment.objects.create(
            page=cls.other_page,
            user=cls.user,
            content="Other site comment",
            is_approved=True,
        )

    def setUp(self):
        cache.clear()
        cache.set(_LATEST_COMMENTS_EPOCH_KEY, 1, timeout=None)

    def test_only_live_public_pages_of_current_site_are_returned(self):
        request = RequestFactory().get("/", HTTP_HOST="testserver")
        result = get_latest_comments({"request": request}, count=10)
        self.assertEqual([item.id for item in result], [self.public_comment.pk])
        self.assertEqual(result[0].page.pk, self.public_page.pk)

    def test_legacy_cache_namespace_is_not_reused(self):
        request = RequestFactory().get("/", HTTP_HOST="testserver")
        site = Site.find_for_request(request)
        # 0.2.8 cached complete Comment instances (including related User data)
        # under this key. 0.2.9 must never return those objects after upgrade.
        cache.set(
            f"latest_comments_site_{site.pk}_10_1",
            [self.draft_comment],
            timeout=300,
        )
        result = get_latest_comments({"request": request}, count=10)
        self.assertEqual([item.pk for item in result], [self.public_comment.pk])
        self.assertTrue(all(isinstance(item, Comment) for item in result))

    def test_cached_widget_is_invalidated_when_page_becomes_restricted(self):
        request = RequestFactory().get("/", HTTP_HOST="testserver")
        before = get_latest_comments({"request": request}, count=10)
        self.assertEqual([item.pk for item in before], [self.public_comment.pk])

        with self.captureOnCommitCallbacks(execute=True):
            PageViewRestriction.objects.create(
                page=self.public_page,
                restriction_type="login",
            )

        after = get_latest_comments({"request": request}, count=10)
        self.assertEqual(after, [])

    def test_cache_contains_ids_not_comment_or_user_models(self):
        """Кеш хранит ТОЛЬКО целочисленные ID: Comment/User/Page не попадают
        в кеш (ID разрешаются обратно в Comment на каждом вызове)."""
        request = RequestFactory().get("/", HTTP_HOST="testserver")
        result = get_latest_comments({"request": request}, count=10)
        self.assertEqual(len(result), 1)
        item = result[0]
        self.assertIsInstance(item, Comment)
        self.assertFalse(hasattr(item, "password"))
        self.assertEqual(item.display_author_name(), "latest-writer")

        site = Site.find_for_request(request)
        epoch = cache.get(_LATEST_COMMENTS_EPOCH_KEY, 0)
        cache_key = f"latest_comment_ids_site_{site.pk}_10_{epoch}"
        cached = cache.get(cache_key)
        self.assertTrue(cached)
        self.assertEqual(list(cached), [result[0].pk])
        self.assertTrue(all(isinstance(value, int) for value in cached))
        payload = repr(cached)
        self.assertNotIn("latest-writer", payload)

class LatestCommentsCacheRegressionTests(TestCase):
    """Ревью 0.2.9: кеш виджета последних комментариев должен инвалидироваться
    при ЛЮБОМ изменении данных, от которого зависит результат, — сразу после
    мутации результат виджета соответствует БД, без опоры на TTL.

    Покрываемые пути: approve/unapprove через instance.save() (post_save),
    QuerySet.update (bulk-модерация и admin bulk actions — сигналы молчат),
    удаление (одно и bulk), unpublish/публикация страницы, снятие ограничения,
    перенос корня Site, а также гарантия, что устаревшие ID из кеша прежней
    эпохи не могут выдать комментарий, который больше не одобрен.
    """

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.author = User.objects.create_user(
            username="cache-writer",
            password="pw",
            first_name="Cache",
            last_name="Writer",
        )
        cls.site = Site.objects.get(is_default_site=True)
        cls.site.hostname = "testserver"
        cls.site.save()
        cls.root = cls.site.root_page

        cls.public_page = Page(title="Cache article", slug="cache-article", live=True)
        cls.root.add_child(instance=cls.public_page)

        cls.other_root = Page(title="Cache other root", slug="cache-other-root", live=True)
        Page.get_first_root_node().add_child(instance=cls.other_root)

    def setUp(self):
        cache.clear()
        cache.set(_LATEST_COMMENTS_EPOCH_KEY, 1, timeout=None)

    # ---------------------------------------------------------------- helpers
    def _make_comment(self, approved=True, page=None, content="Cache regression comment"):
        return Comment.objects.create(
            page=page or self.public_page,
            user=self.author,
            content=content,
            is_approved=approved,
        )

    def _request(self):
        return RequestFactory().get("/", HTTP_HOST="testserver")

    def _latest(self):
        return get_latest_comments({"request": self._request()}, count=10)

    def _prime_cache(self, expected_pks):
        """Два вызова: первый наполняет кеш, второй идёт по кеш-хиту."""
        first = self._latest()
        self.assertEqual([item.pk for item in first], expected_pks)
        second = self._latest()
        self.assertEqual([item.pk for item in second], expected_pks)
        return first

    def _cache_key_for_current_epoch(self):
        site = Site.find_for_request(self._request())
        epoch = cache.get(_LATEST_COMMENTS_EPOCH_KEY, 0)
        return f"latest_comment_ids_site_{site.pk}_10_{epoch}"

    # ------------------------------------------------------------- cache hit
    def test_cache_hit_returns_comment_with_full_public_api(self):
        comment = self._make_comment()
        self._prime_cache([comment.pk])
        self.assertTrue(self._latest())  # третий вызов — тоже по кешу

        result = self._latest()
        item = result[0]
        self.assertIsInstance(item, Comment)
        self.assertFalse(hasattr(item, "password"))
        # прежний публичный API Comment сохранён на кеш-хите
        self.assertEqual(item.user, self.author)
        self.assertEqual(item.display_author_name(), "Cache Writer")
        self.assertEqual(item.get_author_role(), ROLE_MEMBER)
        self.assertTrue(item.avatar_tag)  # property, не метод
        self.assertEqual(item.page.pk, self.public_page.pk)
        # кеш-хит действительно состоялся: под текущим ключом лежат ID
        cached = cache.get(self._cache_key_for_current_epoch())
        self.assertEqual(list(cached), [comment.pk])

    # ------------------------------------------------- approve/unapprove: save
    def test_approve_via_save_invalidates_immediately(self):
        comment = self._make_comment(approved=False)
        self._prime_cache([])

        with self.captureOnCommitCallbacks(execute=True):
            comment.is_approved = True
            comment.save()

        self.assertEqual([item.pk for item in self._latest()], [comment.pk])

    def test_unapprove_via_save_invalidates_immediately(self):
        comment = self._make_comment()
        self._prime_cache([comment.pk])

        with self.captureOnCommitCallbacks(execute=True):
            comment.is_approved = False
            comment.save()

        self.assertEqual(self._latest(), [])

    # ----------------------------------------------- approve/unapprove: update
    def test_queryset_update_invalidate_immediately_both_directions(self):
        """Bulk-модерация через QuerySet.update НЕ вызывает сигналов —
        инвалидация обязана происходить и здесь (admin bulk actions)."""
        approved = self._make_comment(approved=False)
        self._prime_cache([])

        with self.captureOnCommitCallbacks(execute=True):
            Comment.objects.filter(pk=approved.pk).update(is_approved=True)
        self.assertEqual([item.pk for item in self._latest()], [approved.pk])

        with self.captureOnCommitCallbacks(execute=True):
            Comment.objects.approved().filter(pk=approved.pk).update(is_approved=False)
        self.assertEqual(self._latest(), [])

    # ---------------------------------------------------------------- deletion
    def test_single_delete_and_bulk_delete_invalidate_immediately(self):
        first = self._make_comment(content="first")
        second = self._make_comment(content="second")
        # явный порядок по -date_created: auto_now_add даёт совпадающие
        # времена, и сортировка становится неоднозначной
        now = timezone.now()
        Comment.objects.filter(pk=first.pk).update(date_created=now - timedelta(minutes=1))
        Comment.objects.filter(pk=second.pk).update(date_created=now - timedelta(minutes=2))
        self._prime_cache([first.pk, second.pk])

        with self.captureOnCommitCallbacks(execute=True):
            first.delete()
        self.assertEqual([item.pk for item in self._latest()], [second.pk])

        # bulk-удаление (queryset.delete()) тоже обязано инвалидировать
        with self.captureOnCommitCallbacks(execute=True):
            Comment.objects.filter(pk=second.pk).delete()
        self.assertEqual(self._latest(), [])

    # ------------------------------------------------------------ page status
    def test_page_unpublish_and_republish_invalidate_immediately(self):
        comment = self._make_comment()
        self._prime_cache([comment.pk])

        with self.captureOnCommitCallbacks(execute=True):
            self.public_page.unpublish()
        self.assertEqual(self._latest(), [])

        with self.captureOnCommitCallbacks(execute=True):
            # ревизия для publish: страница уже имеет ревизию после unpublish
            self.public_page.save_revision().publish()
        self.assertEqual([item.pk for item in self._latest()], [comment.pk])

    def test_restriction_removal_returns_comment_immediately(self):
        restricted = Page(title="Cache restricted", slug="cache-restricted", live=True)
        self.root.add_child(instance=restricted)
        comment = self._make_comment(page=restricted)
        PageViewRestriction.objects.create(page=restricted, restriction_type="login")
        self._prime_cache([])

        with self.captureOnCommitCallbacks(execute=True):
            PageViewRestriction.objects.get(page=restricted).delete()
        self.assertEqual([item.pk for item in self._latest()], [comment.pk])

    # -------------------------------------------------------------- site move
    def test_site_root_change_invalidates_immediately(self):
        comment = self._make_comment()
        self._prime_cache([comment.pk])

        with self.captureOnCommitCallbacks(execute=True):
            self.site.root_page = self.other_root
            self.site.save()
        # страница комментария выпала из дерева сайта — виджет обязан опустеть
        self.assertEqual(self._latest(), [])

    # ----------------------------------------------------------- stale IDs
    def test_stale_ids_from_previous_epoch_can_resurface_unapproved(self):
        """ID прежней эпохи не читаются: даже если под СТАРЫМ ключом лежит
        устаревший ID (как при гипотетическом refill до commit), виджет
        вычисляет ключ из ТЕКУЩЕЙ эпохи и разрешает комментарий из БД."""
        comment = self._make_comment()
        self._prime_cache([comment.pk])
        stale_key = self._cache_key_for_current_epoch()
        stale_epoch = cache.get(_LATEST_COMMENTS_EPOCH_KEY)

        with self.captureOnCommitCallbacks(execute=True):
            comment.is_approved = False
            comment.save()
        new_epoch = cache.get(_LATEST_COMMENTS_EPOCH_KEY)
        self.assertNotEqual(new_epoch, stale_epoch)

        # симуляция гонки: конкурентный читатель вернул устаревший ID под СТАРЫЙ ключ
        cache.set(stale_key, [comment.pk], timeout=300)
        # виджет читает ключ новой эпохи и разрешает комментарий заново из БД:
        # не одобрен — не возвращается ни при каком раскладе
        self.assertEqual(self._latest(), [])

class RateLimitWindowBoundaryTests(TestCase):
    """Ревью 0.2.9: сброс окна лимитера происходит ровно на границе
    window_started_at <= now - window (включительно). На микросекунду
    свежее границы окно ещё активно. Время управляемое (mock timezone.now),
    без физических ожиданий."""

    def setUp(self):
        self.factory = RequestFactory()

    def _request(self, ip="203.0.113.90"):
        request = self.factory.post("/comments/add/1/", REMOTE_ADDR=ip)
        request.user = AnonymousUser()
        return request

    def test_reset_happens_exactly_at_window_boundary(self):
        request = self._request()
        self.assertFalse(_rate_limited(request, "boundary", limit=2, window=60))
        self.assertFalse(_rate_limited(request, "boundary", limit=2, window=60))
        self.assertTrue(_rate_limited(request, "boundary", limit=2, window=60))
        bucket = CommentRateLimitBucket.objects.get()

        T = timezone.now()
        CommentRateLimitBucket.objects.filter(pk=bucket.pk).update(
            window_started_at=T - timedelta(seconds=60)
        )
        with mock.patch.object(timezone, "now", return_value=T):
            self.assertFalse(_rate_limited(request, "boundary", limit=2, window=60))
        bucket.refresh_from_db()
        self.assertEqual(bucket.count, 1)
        self.assertEqual(bucket.window_started_at, T)

    def test_microsecond_inside_window_does_not_reset(self):
        request = self._request()
        self.assertFalse(_rate_limited(request, "boundary-inside", limit=2, window=60))
        self.assertFalse(_rate_limited(request, "boundary-inside", limit=2, window=60))
        bucket = CommentRateLimitBucket.objects.get()
        self.assertEqual(bucket.count, 2)

        T = timezone.now()
        CommentRateLimitBucket.objects.filter(pk=bucket.pk).update(
            window_started_at=T - timedelta(seconds=60) + timedelta(microseconds=1)
        )
        with mock.patch.object(timezone, "now", return_value=T):
            self.assertTrue(_rate_limited(request, "boundary-inside", limit=2, window=60))
        bucket.refresh_from_db()
        self.assertEqual(bucket.count, 2)
