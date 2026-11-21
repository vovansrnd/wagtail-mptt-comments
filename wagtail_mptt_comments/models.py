import logging
import threading
import uuid
from django.core.mail import send_mail
from django.core.cache import cache
from django.conf import settings
from django.db import connections, models, transaction
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django_prose_editor.fields import ProseEditorField
from modelcluster.fields import ParentalKey
from mptt.managers import TreeManager
from mptt.models import MPTTModel, TreeForeignKey

logger = logging.getLogger(__name__)

_LATEST_COMMENTS_EPOCH_KEY = "wagtail_mptt_comments:latest_comments_epoch"


def invalidate_latest_comments_cache():
    """Invalidate cached widget data after the surrounding DB transaction commits.

    A fresh opaque epoch avoids relying on FileBasedCache.incr(), which is not
    an inter-process atomic operation. ``on_commit`` also prevents a reader from
    refilling the cache from pre-commit database state under the new epoch.
    """
    def bump_epoch():
        try:
            cache.set(_LATEST_COMMENTS_EPOCH_KEY, uuid.uuid4().hex, timeout=None)
        except Exception:
            logger.exception("Could not bump latest-comments cache epoch")

    transaction.on_commit(bump_epoch)

COMMENTS_EDITOR_EXTENSIONS = {
    "Bold": True,
    "Italic": True,
    "Blockquote": True,
    "BulletList": True,
    "ListItem": True,
    "OrderedList": True,
    "Link": {"enableTarget": True, "protocols": ["http", "https", "mailto"]},
    "Code": True,
    "CodeBlock": True,
}

ADMIN_RESPONSE_EXTENSIONS = COMMENTS_EDITOR_EXTENSIONS | {
    "Heading": {"levels": [2, 3]},
    "Strike": True,
    "Underline": True,
    "HorizontalRule": True,
}

# Роли автора комментария. Порядок важен: от самой "весомой" к самой обычной.
ROLE_ADMIN = "admin"
ROLE_MODERATOR = "moderator"
ROLE_MEMBER = "member"
ROLE_GUEST = "guest"

ROLE_LABELS = {
    ROLE_ADMIN: _("Админ"),
    ROLE_MODERATOR: _("Модератор"),
    ROLE_MEMBER: _("Участник"),
    ROLE_GUEST: _("Гость"),
}

# Единственная SVG-иконка человечка для всех "безымянных" аватаров.
# fill="currentColor" — цвет наследуется из CSS родителя, поэтому иконка
# всегда контрастна к фону вне зависимости от темы сайта (в отличие от PNG).
_AVATAR_SVG = (
    '<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor" '
    'aria-hidden="true"><path d="M12 12c2.7 0 4.9-2.2 4.9-4.9S14.7 2.2 12 2.2 '
    '7.1 4.4 7.1 7.1 9.3 12 12 12zm0 2.5c-3.3 0-9.8 1.6-9.8 4.9v2.4h19.6v-2.4c0-3.3-6.5-4.9-9.8-4.9z"/></svg>'
)


def _schedule_notification(callback):
    """Run email work only after commit and close thread-local DB connections."""
    def run_notification():
        # This worker owns its thread-local connections; close them unconditionally
        # so persistent-connection settings cannot leak a connection after it exits.
        connections.close_all()
        try:
            callback()
        finally:
            connections.close_all()

    def start_thread():
        threading.Thread(target=run_notification, daemon=True).start()

    transaction.on_commit(start_thread)


class CommentQuerySet(models.QuerySet):
    def approved(self):
        return self.filter(is_approved=True)

    def update(self, **kwargs):
        """Bulk-обновления (модерация через QuerySet.update и admin bulk
        actions) минуют сигналы — инвалидируем кеш виджета последних
        комментариев явно. invalidate_latest_comments_cache() безопасна и
        внутри atomic (deferred on_commit), и в autocommit (немедленно)."""
        result = super().update(**kwargs)
        invalidate_latest_comments_cache()
        return result


class CommentManager(TreeManager.from_queryset(CommentQuerySet)):
    def approved(self):
        qs = self.get_queryset()
        if hasattr(qs, "approved"):
            return qs.approved().select_related("user", "page")
        return qs.filter(is_approved=True)


class Comment(MPTTModel):
    MAX_DEPTH = 10

    page = models.ForeignKey(
        "wagtailcore.Page",
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name=_("Page"),
    )
    parent = TreeForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
        verbose_name=_("Parent comment"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="wagtail_mptt_comments",
        verbose_name=_("Author (User)"),
    )
    author_name = models.CharField(max_length=255, blank=True, verbose_name=_("Your name"))
    author_email = models.EmailField(blank=True, verbose_name=_("Your Email"))

    content = ProseEditorField(
        extensions=COMMENTS_EDITOR_EXTENSIONS,
        sanitize=True,
        verbose_name=_("Comment text"),
    )
    response = ProseEditorField(
        extensions=ADMIN_RESPONSE_EXTENSIONS,
        blank=True,
        sanitize=True,
        verbose_name=_("Admin response"),
    )

    date_created = models.DateTimeField(default=timezone.now, verbose_name=_("Created at"))
    notify_on_reply = models.BooleanField(default=False, verbose_name=_("Notify on reply"))
    is_approved = models.BooleanField(default=False, verbose_name=_("Approved"))

    objects = CommentManager()

    class MPTTMeta:
        order_insertion_by = ["date_created"]

    class Meta:
        indexes = [
            models.Index(fields=["page", "is_approved", "date_created"]),
        ]
        verbose_name = _("Comment")
        verbose_name_plural = _("Comments")

    def __str__(self):
        content_preview = (self.content or "").strip()[:50]
        return f"{self.display_author_name()} on '{self.page}': '{content_preview}...'"

    @property
    def admin_preview(self):
        return str(self)

    def display_author_name(self):
        if self.user:
            return self.user.get_full_name() or self.user.username
        return self.author_name or _("Anonymous")

    def display_author_email(self):
        return self.user.email if self.user else self.author_email

    # ------------------------------------------------------------------
    # Роль автора: используется для бейджа "Админ/Модератор/Участник/Гость".
    # Список модераторских групп задаётся в settings проекта, т.к. плагин
    # не может знать заранее структуру групп конкретного сайта:
    #
    #   COMMENTS_MODERATOR_GROUPS = ["Moderators"]
    #
    # ------------------------------------------------------------------
    def get_author_role(self):
        if not self.user_id:
            return ROLE_GUEST
        if self.user.is_superuser or self.user.is_staff:
            return ROLE_ADMIN
        moderator_groups = getattr(settings, "COMMENTS_MODERATOR_GROUPS", None)
        # Use the related manager's prefetched group cache when the caller has
        # selected it. A fresh .filter(...).exists() would bypass that cache and
        # issue one SQL query per displayed comment in moderation lists.
        if moderator_groups and any(
            group.name in moderator_groups for group in self.user.groups.all()
        ):
            return ROLE_MODERATOR
        return ROLE_MEMBER

    def get_author_role_label(self):
        return ROLE_LABELS.get(self.get_author_role(), ROLE_LABELS[ROLE_GUEST])

    # ------------------------------------------------------------------
    # Аватар: реальная картинка из профиля пользователя, если она есть,
    # иначе — нейтральная SVG-иконка, которая красится в акцентный цвет
    # темы сайта через currentColor (а не зашитый чёрный PNG-силуэт).
    # ------------------------------------------------------------------
    def get_avatar_url(self):
        if self.user_id:
            try:
                profile = self.user.profile
                if profile.avatar:
                    return profile.avatar.url
            except Exception:
                pass
        return None

    @property
    def avatar_tag(self):
        from django.utils.html import format_html

        url = self.get_avatar_url()
        if url:
            return format_html('<img src="{}" class="comment-avatar" alt="">', url)
        role = self.get_author_role()
        return format_html(
            '<span class="comment-avatar comment-avatar--fallback '
            'comment-avatar--{}">{}</span>',
            role,
            mark_safe(_AVATAR_SVG),
        )

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if self.parent and self.parent.level >= self.MAX_DEPTH - 1:
            current_parent = self.parent
            while current_parent and current_parent.level >= self.MAX_DEPTH - 1:
                current_parent = current_parent.parent
            self.parent = current_parent

        super().save(*args, **kwargs)
        # Инвалидация кеша здесь НЕ нужна: super().save() уже вызвал
        # post_save-ресивер (_invalidate_latest_comments_after_save).
        # Дублирующий bump удваивал сброс кеша при каждом сохранении.

        if not is_new:
            return

        # Уведомление админам о новом комментарии
        if getattr(settings, "COMMENTS_NOTIFY_ADMINS", False):
            def send_admin_notification():
                try:
                    status = "APPROVED" if self.is_approved else "MODERATION NEEDED"
                    page_title = self.page.title if self.page else "Unknown page"
                    msg_subject = f"[{getattr(settings, 'SITE_NAME', 'Site')}] New comment: {status}"
                    msg_body = (
                        f"New comment posted.\n\n"
                        f"Page: {page_title}\n"
                        f"Author: {self.display_author_name()}\n"
                        f"Content:\n{self.content}\n"
                    )
                    send_mail(
                        subject=msg_subject,
                        message=msg_body,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[getattr(settings, "COMMENTS_NOTIFY_EMAIL", settings.DEFAULT_FROM_EMAIL)],
                        fail_silently=True,
                    )
                except Exception as e:
                    logger.error(f"Error sending admin notification: {e}")

            # Запускаем в фоновом потоке, не блокируя воркер Apache
            _schedule_notification(send_admin_notification)

        # Уведомление автору родительского комментария об ответе.
        if self.parent_id and self.parent.notify_on_reply:
            recipient = self.parent.display_author_email()
            if recipient:
                def send_reply_notification():
                    try:
                        page_url = getattr(self.page, "full_url", "") or ""
                        send_mail(
                            subject=f"Новый ответ на ваш комментарий на сайте {getattr(settings, 'SITE_NAME', '')}",
                            message=(
                                f"Здравствуйте!\n\n"
                                f"На ваш комментарий на странице «{self.page.title}» получен ответ:\n\n"
                                f"{self.content}\n\n"
                                f"Ссылка: {page_url}#comment-{self.id}\n"
                            ),
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            recipient_list=[recipient],
                            fail_silently=True,
                        )
                    except Exception as e:
                        logger.error(f"Error sending reply notification: {e}")

                # Запускаем в фоновом потоке
                _schedule_notification(send_reply_notification)


class ConsumedCommentNonce(models.Model):
    """One-time token use, scoped to a browser CSRF secret.

    The unique HMAC permits atomic replay detection without storing the CSRF
    secret or nonce. Scoping by CSRF secret keeps a cached token usable by
    separate visitors while rejecting duplicate submissions from one browser.
    """

    nonce_hash = models.CharField(max_length=64, primary_key=True)
    expires_at = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Consumed comment form nonce"
        verbose_name_plural = "Consumed comment form nonces"


class CommentRateLimitBucket(models.Model):
    """Atomic per-identity rate-limit window for public comment submissions.

    The key is a SHA-256 digest; raw client IPs and user identifiers are not
    stored. Counter changes use conditional SQL UPDATEs (F expressions), so
    concurrent requests cannot all pass the same remaining slot.
    """

    key_hash = models.CharField(max_length=64, primary_key=True)
    window_started_at = models.DateTimeField(db_index=True)
    count = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Comment rate-limit bucket"
        verbose_name_plural = "Comment rate-limit buckets"


# QuerySet deletion and cascading page deletion bypass model.delete(); signals cover them.
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from wagtail.models import PageViewRestriction, Site
from wagtail.signals import page_published, page_unpublished, page_slug_changed, post_page_move


# Про bulk_create: Django НЕ шлёт post_save при bulk_create. Стандартный
# bulk_create НЕ ПОДДЕРЖИВАЕТСЯ django-mptt для этой модели — он обходит
# формирование дерева, tree-поля (lft/rght/level/tree_id) остаются NULL и
# INSERT падает с NOT NULL constraint failed на lft (проверено эмпирически).
# Обходные вставки (ручной SQL или INSERT с заранее заполненными tree-
# полями) НЕ поддерживаются и гарантию инвалидации кеша НЕ дают: рассчитывать
# на инвалидацию при них нельзя. Поддерживаемый путь создания —
# instance.save(), покрытый post_save. bulk_update группирует обновления
# через QuerySet.update() (Django 4.2+), поэтому покрыт переопределённым
# CommentQuerySet.update().

@receiver(post_save, sender=Comment)
def _invalidate_latest_comments_after_save(sender, instance, **kwargs):
    # Любое сохранение комментария (создание, approve/unapprove, правка в
    # админке) сбрасывает кеш. Всегда, а не только при смене is_approved:
    # узкие эвристики по полям молча пропускают сохранения из хост-проекта
    # и MPTT-операций, а ложная инвалидация безвредна.
    invalidate_latest_comments_cache()


@receiver(post_delete, sender=Comment)
def _invalidate_latest_comments_after_delete(sender, instance, **kwargs):
    invalidate_latest_comments_cache()


@receiver(page_published)
@receiver(page_unpublished)
@receiver(page_slug_changed)
@receiver(post_page_move)
def _invalidate_latest_comments_after_page_change(sender, instance, **kwargs):
    invalidate_latest_comments_cache()


@receiver(post_save, sender=PageViewRestriction)
@receiver(post_delete, sender=PageViewRestriction)
def _invalidate_latest_comments_after_page_restriction_change(sender, instance, **kwargs):
    invalidate_latest_comments_cache()


@receiver(post_save, sender=Site)
@receiver(post_delete, sender=Site)
def _invalidate_latest_comments_after_site_change(sender, instance, **kwargs):
    invalidate_latest_comments_cache()
