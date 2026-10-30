import hashlib
import ipaddress
import logging

from django.conf import settings
from django.contrib.auth.decorators import permission_required
from django.contrib import messages
from django.core.cache import cache
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext as _
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from wagtail.models import Page, Site

from .forms import PublicCommentForm
from .models import Comment

logger = logging.getLogger(__name__)

# Draft values kept in the session after a failed submit (anti-bloat cap).
_DRAFT_MAX_LEN = 20_000


def _client_ip(request):
    """Return the client IP without trusting arbitrary X-Forwarded-For input.

    Proxy headers are considered only when REMOTE_ADDR belongs to an explicitly
    configured trusted proxy CIDR. Walk the chain from right to left and skip
    trusted proxies; the first untrusted address is the client candidate.
    Hosts must configure the proxy CIDRs only after verifying that their proxy
    overwrites or correctly appends X-Forwarded-For.
    """
    remote_raw = (request.META.get("REMOTE_ADDR") or "").strip()
    try:
        remote_ip = ipaddress.ip_address(remote_raw)
    except ValueError:
        return "unknown"

    if not getattr(settings, "COMMENTS_TRUST_PROXY_HEADERS", False):
        return str(remote_ip)

    raw_networks = getattr(settings, "COMMENTS_TRUSTED_PROXY_IPS", ()) or ()
    if isinstance(raw_networks, str):
        raw_networks = [part.strip() for part in raw_networks.split(",") if part.strip()]

    trusted_networks = []
    for value in raw_networks:
        try:
            trusted_networks.append(ipaddress.ip_network(str(value), strict=False))
        except ValueError:
            logger.warning("Ignoring invalid COMMENTS_TRUSTED_PROXY_IPS entry: %r", value)

    def is_trusted(address):
        return any(
            address.version == network.version and address in network
            for network in trusted_networks
        )

    # An empty allowlist or an untrusted direct peer means XFF is ignored.
    if not trusted_networks or not is_trusted(remote_ip):
        return str(remote_ip)

    forwarded = (request.META.get("HTTP_X_FORWARDED_FOR") or "").strip()
    if not forwarded:
        return str(remote_ip)

    try:
        chain = [ipaddress.ip_address(part.strip()) for part in forwarded.split(",")]
    except ValueError:
        # A malformed chain is not partially trusted.
        return str(remote_ip)

    chain.append(remote_ip)
    for address in reversed(chain):
        if not is_trusted(address):
            return str(address)

    # A chain containing only trusted proxies is not enough to identify a client.
    return str(remote_ip)


def _rate_limited(request, bucket, limit, window):
    """Cache-based flood control; False means the request is allowed."""
    if request.user.is_authenticated:
        ident = f"u_{request.user.pk}"
    else:
        ident = "ip_" + hashlib.md5(_client_ip(request).encode()).hexdigest()[:10]
    key = f"comments_rl_{bucket}_{ident}"
    current = cache.get(key, 0)
    if current >= limit:
        return True
    if current == 0:
        cache.set(key, 1, window)
    else:
        try:
            cache.incr(key)
        except Exception:
            cache.set(key, current + 1, window)
    return False


@require_POST
@csrf_protect
def add_comment_to_page(request, page_id):
    # Only comment on pages belonging to the current Wagtail Site. Without
    # this filter a forged page_id could post into another domain's comments.
    site = Site.find_for_request(request)
    if site is None:
        from django.http import Http404
        raise Http404("No Wagtail Site is configured for this host")
    page = get_object_or_404(
        Page.objects.live().public().in_site(site), id=page_id
    ).specific

    if _rate_limited(request, "post", limit=10, window=300):
        too_fast = _("You are posting comments too quickly. Please wait a bit.")
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": False, "error": too_fast}, status=429)
        messages.error(request, too_fast)
        return redirect(page.get_url(request) + "?has_errors=1#comment-form-anchor")

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
        request.session.pop(f"invalid_comment_post_{page.pk}", None)

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
    draft = request.POST.dict()
    if draft.get("content"):
        draft["content"] = draft["content"][:_DRAFT_MAX_LEN]
    request.session[f"invalid_comment_post_{page.pk}"] = draft

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
@permission_required("wagtail_mptt_comments.change_comment", raise_exception=True)
def comment_action(request):
    action = request.POST.get("action")
    raw_ids = request.POST.getlist("ids[]")
    comment_ids = [int(i) for i in raw_ids if str(i).isdigit()]
    if not action or not comment_ids:
        return JsonResponse({"success": False, "error": _("No items selected.")}, status=400)

    comments = Comment.objects.filter(pk__in=comment_ids)
    if action == "approve":
        cnt = comments.update(is_approved=True)
        if cnt:
            from .models import invalidate_latest_comments_cache
            invalidate_latest_comments_cache()
        return JsonResponse({"success": True, "message": _("Approved %(count)s comments.") % {'count': cnt}})
    elif action == "delete":
        if not request.user.has_perm("wagtail_mptt_comments.delete_comment"):
            return JsonResponse({"success": False, "error": _("Access denied.")}, status=403)
        # Materialize before mutating the tree. Delete selected descendants first
        # so a selected parent does not cascade-delete an object still pending in
        # the loop. MPTT updates are disabled inside the transaction and each
        # affected surviving tree is rebuilt once afterwards.
        ordered_comments = list(comments.order_by("-level", "tree_id", "lft"))
        tree_ids = {comment.tree_id for comment in ordered_comments if comment.tree_id}
        cnt = 0
        with transaction.atomic():
            with Comment.objects.disable_mptt_updates():
                for comment in ordered_comments:
                    # Descendants are ordered before ancestors. Delete each selected
                    # row once; avoiding an exists() query here matters for bulk actions.
                    comment.delete()
                    cnt += 1
            for tree_id in sorted(tree_ids):
                if Comment.objects.filter(tree_id=tree_id).exists():
                    Comment.objects.partial_rebuild(tree_id)
        return JsonResponse({"success": True, "message": _("Deleted %(count)s comments.") % {"count": cnt}})
    return JsonResponse({"success": False, "error": _("Invalid action.")}, status=400)
