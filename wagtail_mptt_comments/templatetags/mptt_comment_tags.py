import nh3
from django import template
from django.utils.safestring import mark_safe
from wagtail.models import Page, Site
from wagtail_mptt_comments.forms import PublicCommentForm
from wagtail_mptt_comments.models import Comment

register = template.Library()


@register.filter(is_safe=True)
def clean_comment_html(value):
    if not value:
        return ""

    allowed_tags = {
        'p', 'br', 'b', 'strong', 'i', 'em', 'u', 'strike',
        'a', 'blockquote', 'ol', 'ul', 'li', 'code', 'pre'
    }
    allowed_attrs = {'a': {'href', 'title', 'target', 'rel'}}

    cleaned_html = nh3.clean(
        str(value),
        tags=allowed_tags,
        attributes=allowed_attrs,
        link_rel="noopener noreferrer"
    )
    return mark_safe(cleaned_html)


@register.simple_tag(takes_context=True)
def get_latest_comments(context, count=5):
    """
    Возвращает последние комментарии.
    Если передан context (Wagtail Multi-site), фильтрует строго по страницам текущего домена.
    """
    qs = Comment.objects.filter(is_approved=True)

    request = context.get("request")
    if request:
        try:
            site = Site.find_for_request(request)
            if site:
                qs = qs.filter(page__in=Page.objects.in_site(site))
        except Exception:
            pass

    return qs.select_related("page", "user").order_by("-date_created")[:count]


@register.inclusion_tag('wagtail_mptt_comments/comments_block.html', takes_context=True)
def render_comments(context, page):
    """
    Рендерит дерево комментариев и форму добавления для конкретной страницы.
    """
    request = context.get('request')

    if page.id and hasattr(page, "comments"):
        comment_roots = (
            page.comments.filter(is_approved=True)
            .select_related("user")
            .order_by("tree_id", "lft")
        )
        comments_count = comment_roots.count()
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
