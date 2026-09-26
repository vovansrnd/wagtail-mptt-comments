import logging
from django.conf import settings
from django.utils.translation import gettext as _
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from wagtail.models import Page
from .forms import PublicCommentForm
from .models import Comment

logger = logging.getLogger(__name__)


@require_POST
@csrf_protect
def add_comment_to_page(request, page_id):
    page = get_object_or_404(Page, id=page_id).specific
    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"
    form = PublicCommentForm(request.POST, request=request, page=page)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.page = page

        if request.user.is_authenticated:
            comment.user = request.user
            comment.is_approved = True
        else:
            needs_moderation = getattr(settings, "COMMENTS_MODERATION", True)
            comment.is_approved = not needs_moderation

        comment.save()

        # Очищаем временные данные и капчу при успехе
        request.session.pop("comment_captcha_sum", None)
        request.session.pop("invalid_comment_post", None)

        msg = _("Your comment has been published successfully.") if comment.is_approved else _("Thank you! Your comment has been sent for moderation.")

        if is_ajax:
            return JsonResponse({"success": True, "message": msg, "is_approved": comment.is_approved})

        messages.success(request, msg)
        base_url = page.get_url(request)
        anchor = f"#comment-{comment.id}" if comment.is_approved else "#comment-form-anchor"
        return redirect(f"{base_url}?success=1{anchor}")

    # ========================================================
    # ЕСЛИ ФОРМА НЕВАЛИДНА (ОШИБКА КАПЧИ, КОРОТКИЙ ТЕКСТ И Т.Д.)
    # ========================================================
    if is_ajax:
        return JsonResponse({"success": False, "errors": form.errors}, status=400)

    # 1. Сохраняем черновик введенных полей в сессию (чтобы ничего не пропало!)
    request.session["invalid_comment_post"] = request.POST.dict()

    # 2. Показываем подробные ошибки в плашке сообщений
    error_list = []
    for field, errs in form.errors.items():
        for e in errs:
            error_list.append(f"{e}")
    error_msg = " ".join(error_list) if error_list else _("Please check the form for errors.")
    messages.error(request, error_msg)

    # 3. Возвращаем пользователя ровно к форме
    return redirect(page.get_url(request) + "?has_errors=1#comment-form-anchor")


@require_POST
@permission_required("wagtailadmin.access_admin")
def comment_action(request):
    action = request.POST.get("action")
    comment_ids = request.POST.getlist("ids[]")
    if not action or not comment_ids:
        return JsonResponse({"success": False, "error": _("No items selected.")}, status=400)

    comments = Comment.objects.filter(pk__in=comment_ids)
    if action == "approve":
        cnt = comments.update(is_approved=True)
        return JsonResponse({"success": True, "message": _("Approved %(count)s comments.") % {'count': cnt}})
    elif action == "delete":
        # ИЗМЕНЕНИЕ ЗДЕСЬ: используем _deleted вместо _, чтобы не ломать переводчик!
        cnt, _deleted = comments.delete()
        return JsonResponse({"success": True, "message": _("Deleted %(count)s comments.") % {'count': cnt}})
    return JsonResponse({"success": False, "error": _("Invalid action.")}, status=400)
