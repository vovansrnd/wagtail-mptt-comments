import logging
import random
import secrets
import time
from django import forms
from django.conf import settings
from django.core import signing
from django.utils.translation import gettext_lazy as _
from django_prose_editor.widgets import AdminProseEditorWidget
from .models import Comment, ADMIN_RESPONSE_EXTENSIONS, COMMENTS_EDITOR_EXTENSIONS

CAPTCHA_SALT = "wagtail_mptt_comments.captcha"
logger = logging.getLogger(__name__)


class PublicCommentForm(forms.ModelForm):
    parent = forms.ModelChoiceField(
        queryset=Comment.objects.none(),
        widget=forms.HiddenInput(),
        required=False,
    )
    website_url = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"tabindex": "-1", "autocomplete": "off"}),
    )
    form_token = forms.CharField(required=False, widget=forms.HiddenInput())
    captcha_answer = forms.IntegerField(required=False)
    # Подписанный токен с правильной суммой капчи: не пишет в сессию,
    # чтобы каждый GET страницы с формой не создавал строку в django_session.
    captcha_token = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = Comment
        fields = ["content", "parent", "author_name", "author_email", "notify_on_reply"]

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        page = kwargs.pop("page", None)
        self.page = page
        self.page_id = getattr(page, "pk", None)
        self._validated_form_nonce = None
        self._validated_captcha_nonce = None
        super().__init__(*args, **kwargs)

        if page:
            # Only allow replies to already visible comments.
            self.fields["parent"].queryset = Comment.objects.filter(
                page=page, is_approved=True
            )

        # -------------------------------------------------------------
        # ВОССТАНОВЛЕНИЕ ДАННЫХ ПРИ ОШИБКЕ ВАЛИДАЦИИ
        # -------------------------------------------------------------
        if not self.is_bound and self.request:
            saved_post = self.request.session.pop(f"invalid_comment_post_{self.page_id}", None)
            if saved_post:
                # Восстанавливаем текст комментария, имя, email и родителя
                self.fields["content"].initial = saved_post.get("content", "")
                self.fields["author_name"].initial = saved_post.get("author_name", "")
                self.fields["author_email"].initial = saved_post.get("author_email", "")
                self.fields["notify_on_reply"].initial = saved_post.get("notify_on_reply") in (
                    True, "True", "true", "on", "1",
                )
                if saved_post.get("parent"):
                    self.fields["parent"].initial = saved_post.get("parent")

        # Настройки для авторизованных
        if self.request and self.request.user.is_authenticated:
            self.fields["author_name"].widget = forms.HiddenInput()
            self.fields["author_email"].widget = forms.HiddenInput()
            self.fields["captcha_answer"].widget = forms.HiddenInput()
            self.fields["captcha_answer"].required = False
        else:
            self.fields["author_name"].required = True
            self.fields["author_email"].required = True

            # Генерируем новую капчу
            if not self.is_bound and self.request:
                n1, n2 = random.randint(1, 10), random.randint(1, 10)
                self.fields["captcha_answer"].label = f"{n1} + {n2} = ?"
                self.fields["captcha_token"].initial = signing.dumps(
                    {
                        "sum": n1 + n2,
                        "page_id": self.page_id,
                        "nonce": secrets.token_urlsafe(18),
                        "issued_at": time.time(),
                    },
                    salt=CAPTCHA_SALT,
                    compress=True,
                )

        if not self.is_bound and self.request:
            self.fields["form_token"].initial = signing.dumps(
                {
                    "page_id": self.page_id,
                    "nonce": secrets.token_urlsafe(18),
                    "issued_at": time.time(),
                },
                salt="wagtail_mptt_comments.form",
                compress=True,
            )
        self.fields["author_name"].widget.attrs["placeholder"] = _("Your name *")
        self.fields["author_email"].widget.attrs["placeholder"] = _("Email (private) *")
        self.fields["captcha_answer"].widget.attrs["placeholder"] = _("Answer")

    def clean_website_url(self):
        if self.cleaned_data.get("website_url"):
            raise forms.ValidationError(_("Spam detected."), code="honeypot")
        return ""

    def clean_form_token(self):
        token = self.cleaned_data.get("form_token")
        max_age = int(getattr(settings, "COMMENTS_FORM_TOKEN_MAX_AGE", 2 * 60 * 60))
        if not token:
            raise forms.ValidationError(_("Form verification token is missing."), code="token_missing")
        try:
            payload = signing.loads(token, salt="wagtail_mptt_comments.form", max_age=max_age)
            issued_at = float(payload["issued_at"])
            nonce = str(payload["nonce"])
            token_page_id = payload.get("page_id")
        except (signing.BadSignature, KeyError, TypeError, ValueError, AttributeError):
            raise forms.ValidationError(_("Form verification failed. Please refresh the page."), code="token_invalid")
        age = time.time() - issued_at
        if token_page_id != self.page_id:
            raise forms.ValidationError(_("This form belongs to another page."), code="wrong_page")
        if age < 3 or age > max_age:
            raise forms.ValidationError(_("Form submitted too quickly or the form has expired."), code="too_fast_or_expired")
        # Do not consume the nonce here: other fields may still fail validation,
        # and the user should be able to correct those fields without refreshing.
        self._validated_form_nonce = nonce
        return token

    def clean_captcha_answer(self):
        if self.request and not self.request.user.is_authenticated:
            ans = self.cleaned_data.get("captcha_answer")
            token = self.cleaned_data.get("captcha_token") or self.data.get("captcha_token")
            max_age = getattr(settings, "COMMENTS_CAPTCHA_MAX_AGE", 2 * 60 * 60)
            try:
                payload = signing.loads(token, salt=CAPTCHA_SALT, max_age=max_age)
            except (signing.BadSignature, TypeError, ValueError):
                payload = None
            if not isinstance(payload, dict):
                raise forms.ValidationError(_("Incorrect captcha answer."), code="captcha_invalid")
            if payload.get("page_id") != self.page_id or payload.get("sum") != ans:
                raise forms.ValidationError(_("Incorrect captcha answer."), code="captcha_invalid")
            nonce = payload.get("nonce")
            if not isinstance(nonce, str) or not nonce:
                raise forms.ValidationError(_("Incorrect captcha answer."), code="captcha_invalid")
            self._validated_captcha_nonce = nonce
        return self.cleaned_data.get("captcha_answer")

    def clean(self):
        cleaned_data = super().clean()
        # A public page may be cached by a proxy/CDN. A global one-time cache key
        # would make the same cached HTML token fail for unrelated visitors, so
        # replay tracking is scoped to the submitting session and only written
        # after all other form fields validate successfully.
        if self.errors or not self.request:
            return cleaned_data
        tokens = []
        if self._validated_form_nonce:
            tokens.append("form:" + self._validated_form_nonce)
        if self._validated_captcha_nonce:
            tokens.append("captcha:" + self._validated_captcha_nonce)
        if not tokens:
            return cleaned_data
        session_key = "wagtail_mptt_comments_used_nonces"
        used = self.request.session.get(session_key, [])
        if not isinstance(used, list):
            used = []
        if any(token in used for token in tokens):
            raise forms.ValidationError(
                _("This form verification has already been used. Please refresh the page."),
                code="token_replayed",
            )
        self.request.session[session_key] = (used + tokens)[-100:]
        return cleaned_data

    def clean_content(self):
        c = (self.cleaned_data.get("content") or "").strip()
        if len(c) < 5:
            raise forms.ValidationError(_("Comment is too short."), code="too_short")
        if len(c) > getattr(settings, "COMMENTS_MAX_LENGTH", 20000):
            raise forms.ValidationError(_("Comment is too long."), code="too_long")
        return c


class AdminCommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = [
            "page", "parent", "user", "author_name", "author_email",
            "content", "response", "is_approved", "notify_on_reply"
        ]
        widgets = {
            "content": AdminProseEditorWidget(config={"extensions": COMMENTS_EDITOR_EXTENSIONS}, preset="configurable"),
            "response": AdminProseEditorWidget(config={"extensions": ADMIN_RESPONSE_EXTENSIONS}, preset="configurable"),
        }
