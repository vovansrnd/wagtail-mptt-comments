from django.urls import path
from . import views

app_name = "wagtail_mptt_comments"

urlpatterns = [
    path("add/<int:page_id>/", views.add_comment_to_page, name="add_comment_to_page"),
    path("action/", views.comment_action, name="comment_action"),
]
