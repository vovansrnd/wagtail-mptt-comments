from django.urls import path
from . import views

app_name = "wagtail_mptt_comments"

urlpatterns = [
    path("add/<int:page_id>/", views.add_comment_to_page, name="add_comment_to_page"),
    path("form/<int:page_id>/", views.comment_form_fragment, name="comment_form_fragment"),
    path("action/", views.comment_action, name="comment_action"),
]
