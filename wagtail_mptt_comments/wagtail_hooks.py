from django.core.paginator import Paginator
from django.db.models import Case, CharField, When
from django.templatetags.static import static
from django.urls import include, path, reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from wagtail import hooks
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import IndexView, SnippetViewSet
from .forms import AdminCommentForm
from .models import Comment
from .views import comment_action


@hooks.register("register_admin_urls")
def register_comment_admin_urls():
    return [
        # Только модерация под замком админки:
        path("comments/action/", comment_action, name="comment_action_admin"),
    ]


@hooks.register("insert_global_admin_js")
def insert_comment_admin_js():
    return format_html(
        '<script src="{}" defer></script>\n'
        '<script src="{}" defer></script>',
        static("wagtail_mptt_comments/js/admin_comments.js"),
        static("wagtail_mptt_comments/js/prose_editor_codeblock.js"),
    )


@hooks.register("insert_global_admin_css")
def insert_comment_admin_css():
    return format_html(
        '<link rel="stylesheet" href="{}">',
        static("wagtail_mptt_comments/css/admin_comments.css"),
    )


class CommentIndexView(IndexView):
    model = Comment

    def get_template_names(self):
        return ["wagtail_mptt_comments/admin_comments.html"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if hasattr(self, 'get_breadcrumbs_items'):
                    context['breadcrumbs_items'] = self.get_breadcrumbs_items()
        view_type = self.request.GET.get("view", "list")
        page_id = self.request.GET.get("page_id")
        sort_by = self.request.GET.get("sort", "-date_created")
        status_filter = self.request.GET.get("status", "all")

        comments_qs = self.model.objects.select_related("page", "user").all()
        if page_id:
            try:
                comments_qs = comments_qs.filter(page_id=int(page_id))
            except (ValueError, TypeError):
                pass

        if status_filter == "unapproved":
            comments_qs = comments_qs.filter(is_approved=False)

        if sort_by == "author":
            comments_qs = comments_qs.annotate(
                sort_name=Case(
                    When(user__username__isnull=False, then="user__username"),
                    default="author_name",
                    output_field=CharField(),
                )
            ).order_by("sort_name")
        else:
            comments_qs = comments_qs.order_by("-date_created")

        def get_edit_url(obj):
            try:
                return reverse("wagtailsnippets_wagtail_mptt_comments_comment:edit", args=[obj.pk])
            except Exception:
                return reverse("wagtailsnippets:edit", args=["wagtail_mptt_comments", "comment", obj.pk])

        if view_type == "tree":
            root_qs = comments_qs.filter(parent__isnull=True).order_by("-date_created")
            paginator = Paginator(root_qs, 20)
            page_obj = paginator.get_page(self.request.GET.get("page", 1))
            tree_ids = [r.tree_id for r in page_obj.object_list]
            tree_nodes = list(comments_qs.filter(tree_id__in=tree_ids).order_by("tree_id", "lft"))
            for c in tree_nodes:
                c.edit_url = get_edit_url(c)
            context["comment_queryset"] = tree_nodes
            context["page_obj"] = page_obj
        else:
            paginator = Paginator(comments_qs, 50)
            page_obj = paginator.get_page(self.request.GET.get("page", 1))
            for c in page_obj.object_list:
                c.edit_url = get_edit_url(c)
            context["page_obj"] = page_obj

        context.update({
            "view_type": view_type,
            "total_comments": self.model.objects.count(),
            "unapproved_count": self.model.objects.filter(is_approved=False).count(),
            "current_page_id": page_id,
            "sort_by": sort_by,
            "status_filter": status_filter,
        })
        return context


@register_snippet
class CommentAdmin(SnippetViewSet):
    model = Comment
    icon = "comment"
    menu_label = _("Comments")
    menu_order = 240
    add_to_admin_menu = True

    index_view_class = CommentIndexView
    base_form_class = AdminCommentForm

    list_display = ("avatar_tag", "display_author_name", "content", "page", "date_created", "is_approved")
    list_filter = ("is_approved", "date_created")
    search_fields = ("content", "author_name", "author_email", "user__username")
