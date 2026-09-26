import random
from datetime import timedelta
from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_prose_editor.widgets import AdminProseEditorWidget
from .models import Comment, ADMIN_RESPONSE_EXTENSIONS, COMMENTS_EDITOR_EXTENSIONS


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
    submit_time = forms.DateTimeField(required=False, widget=forms.HiddenInput())
    captcha_answer = forms.IntegerField(required=False)

    class Meta:
        model = Comment
        fields = ["content", "parent", "author_name", "author_email", "notify_on_reply"]

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        page = kwargs.pop("page", None)
        super().__init__(*args, **kwargs)

        if page:
            self.fields["parent"].queryset = Comment.objects.filter(page=page)

        # -------------------------------------------------------------
        # ВОССТАНОВЛЕНИЕ ДАННЫХ ПРИ ОШИБКЕ ВАЛИДАЦИИ
        # -------------------------------------------------------------
        if not self.is_bound and self.request:
            saved_post = self.request.session.pop("invalid_comment_post", None)
            if saved_post:
                # Восстанавливаем текст комментария, имя, email и родителя
                self.fields["content"].initial = saved_post.get("content", "")
                self.fields["author_name"].initial = saved_post.get("author_name", "")
                self.fields["author_email"].initial = saved_post.get("author_email", "")
                self.fields["notify_on_reply"].initial = bool(saved_post.get("notify_on_reply"))
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
                self.request.session["comment_captcha_sum"] = n1 + n2

        self.fields["submit_time"].initial = timezone.now()
        self.fields["author_name"].widget.attrs["placeholder"] = _("Your name *")
        self.fields["author_email"].widget.attrs["placeholder"] = _("Email (private) *")
        self.fields["captcha_answer"].widget.attrs["placeholder"] = _("Answer")

    def clean_website_url(self):
        if self.cleaned_data.get("website_url"):
            raise forms.ValidationError("Spam detected.", code="honeypot")
        return ""

    def clean_submit_time(self):
        t = self.cleaned_data.get("submit_time")
        if not t or (timezone.now() - t < timedelta(seconds=3)):
            raise forms.ValidationError(_("Form submitted too quickly."), code="too_fast")
        return t

    def clean_captcha_answer(self):
        if self.request and not self.request.user.is_authenticated:
            correct = self.request.session.get("comment_captcha_sum")
            ans = self.cleaned_data.get("captcha_answer")
            if correct is None or ans != correct:
                raise forms.ValidationError(_("Incorrect captcha answer."), code="captcha_invalid")
        return self.cleaned_data.get("captcha_answer")

    def clean_content(self):
        c = (self.cleaned_data.get("content") or "").strip()
        if len(c) < 5:
            raise forms.ValidationError(_("Comment is too short."), code="too_short")
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
