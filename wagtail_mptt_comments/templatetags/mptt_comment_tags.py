import nh3
from django import template
from django.utils.safestring import mark_safe
from wagtail_mptt_comments.forms import PublicCommentForm

register = template.Library()

@register.filter(is_safe=True)
def clean_comment_html(value):
    if not value:
        return ""

    allowed_tags = {'p', 'br', 'b', 'strong', 'i', 'em', 'u', 'strike', 'a', 'blockquote', 'ol', 'ul', 'li', 'code', 'pre'}
    allowed_attrs = {'a': {'href', 'title', 'target', 'rel'}}

    cleaned_html = nh3.clean(
        str(value),
        tags=allowed_tags,
        attributes=allowed_attrs,
        link_rel="noopener noreferrer" # Бонус: защита от фишинга по ссылкам от пользователей
    )
    return mark_safe(cleaned_html)

@register.simple_tag
def get_latest_comments(count=5):
    from wagtail_mptt_comments.models import Comment
    return Comment.objects.filter(is_approved=True).select_related("page", "user").order_by("-date_created")[:count]

@register.inclusion_tag('wagtail_mptt_comments/comments_block.html', takes_context=True)
def render_comments(context, page):
    """
    Рендерит дерево комментариев и форму добавления для конкретной страницы.
    Использование в шаблоне статьи: {% render_comments page %}
    """
    request = context.get('request')

    # Собираем комментарии
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
