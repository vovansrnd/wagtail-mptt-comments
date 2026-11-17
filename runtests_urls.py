"""URLConf тестового набора: comment-эндпоинты плагина, как в ядре."""
from django.urls import include, path

urlpatterns = [
    path("comments/", include("wagtail_mptt_comments.urls")),
]
