import logging

import nh3
from django import template
from django.core.cache import cache
from django.utils.safestring import mark_safe
from wagtail.models import Page, Site
from wagtail_mptt_comments.forms import PublicCommentForm
from wagtail_mptt_comments.models import Comment, _LATEST_COMMENTS_EPOCH_KEY

register = template.Library()
logger = logging.getLogger(__name__)


def _user_prefetch_paths():
    """
    Related-object prefetch paths that exist on this project's user model.
    ``profile`` is a OneToOne defined by the host project (accounts app),
    so it is only prefetched when actually present.
    """
    from django.contrib.auth import get_user_model

    accessors = {r.get_accessor_name() for r in get_user_model()._meta.related_objects}
    paths = ["user__groups"]
    if "profile" in accessors:
        paths.append("user__profile")
    return paths

_BASE_TAGS = {
    'p', 'br', 'b', 'strong', 'i', 'em', 'u', 'strike', 's', 'del',
    'a', 'blockquote', 'ol', 'ul', 'li', 'code', 'pre',
}
# Tags the admin-response editor may legitimately produce.
_EXT_TAGS = _BASE_TAGS | {'h2', 'h3', 'hr'}

# "rel" управляется самим nh3 через link_rel, в allowed_attrs его передавать нельзя
_BASE_ATTRS = {'a': {'href', 'title', 'target'}}


@register.filter(is_safe=True)
def clean_comment_html(value, variant="base"):
    """Second line of defence on top of ProseEditorField(sanitize=True).

    Usage: {{ node.content|clean_comment_html }} or, for admin responses
    written with the extended editor, {{ node.response|clean_comment_html:"extended" }}.
    """
    if not value:
        return ""

    tags = _EXT_TAGS if variant == "extended" else _BASE_TAGS
    cleaned_html = nh3.clean(
        str(value),
        tags=tags,
        attributes=_BASE_ATTRS,
        link_rel="nofollow ugc noopener noreferrer",
    )
    return mark_safe(cleaned_html)


@register.simple_tag(takes_context=True)
def get_latest_comments(context, count=5):
    """Return recent approved comments for the current Wagtail Site only.

    Fail closed: a missing request or unresolved Site must never turn this
    widget into a cross-site query. ``count`` is bounded because this tag is
    also usable from templates.
    """
    request = context.get("request")
    if request is None:
        return []

    try:
        site = Site.find_for_request(request)
    except Exception:
        logger.warning("Could not resolve Site for get_latest_comments", exc_info=True)
        return []
    if site is None:
        return []

    try:
        count = max(1, min(int(count), 100))
    except (TypeError, ValueError):
        count = 5

    epoch = cache.get(_LATEST_COMMENTS_EPOCH_KEY, 0)
    cache_key = f"latest_comments_site_{site.pk}_{count}_{epoch}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    qs = Comment.objects.filter(
        is_approved=True,
        page__in=Page.objects.in_site(site),
    )
    comments = list(
        qs.select_related("page", "user")
        .prefetch_related(*_user_prefetch_paths())
        .order_by("-date_created")[:count]
    )
    cache.set(cache_key, comments, 300)
    return comments


@register.inclusion_tag('wagtail_mptt_comments/comments_block.html', takes_context=True)
def render_comments(context, page):
    """
    Рендерит дерево комментариев и форму добавления для конкретной страницы.
    """
    request = context.get('request')

    if page.id and hasattr(page, "comments"):
        # prefetch_related kills the per-comment queries for avatars
        # (user.profile) and role badges (user.groups).
        comment_roots = (
            page.comments.filter(is_approved=True)
            .select_related("user")
            .prefetch_related(*_user_prefetch_paths())
            .order_by("tree_id", "lft")
        )
        # The full tree is rendered anyway, so materialize once and count in
        # Python instead of issuing COUNT(*) followed by SELECT of the same rows.
        comment_roots = list(comment_roots)
        comments_count = len(comment_roots)
    else:
        comment_roots = []
        comments_count = 0

    return {
        'page': page,
        'request': request,
        'messages': context.get('messages'),
        'comment_roots': comment_roots,
        'comments_count': comments_count,
        'comment_form': PublicCommentForm(request=request, page=page),
    }
