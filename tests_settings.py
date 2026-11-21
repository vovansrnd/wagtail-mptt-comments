"""Минимальные настройки тестового набора wagtail-mptt-comments.

По умолчанию sqlite in-memory; PostgreSQL включается через TEST_DB_ENGINE
(см. блок DATABASES ниже) — нужен для конкурентных тестов лимитера и nonce.
"""
import os
SECRET_KEY = "mptt-tests-audit"
DEBUG = True
USE_TZ = True
ALLOWED_HOSTS = ["*"]
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "mptt",
    "taggit",
    "wagtail",
    "wagtail.admin",
    "wagtail.documents",
    "wagtail.images",
    "wagtail.sites",
    "wagtail.users",
    "wagtail.snippets",
    "wagtail.contrib.forms",
    "wagtail_mptt_comments",
]
MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [], "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]
# БД тестового набора. По умолчанию sqlite in-memory; конкурентные тесты
# (ConcurrentCommentRateLimitTests, ConcurrentCommentNonceTests) требуют
# PostgreSQL и запускаются при TEST_DB_ENGINE=postgresql (учётные данные
# только из окружения, без захардкоженных идентификаторов):
#   TEST_DB_ENGINE=postgresql TEST_DB_NAME=... TEST_DB_USER=... TEST_DB_PASSWORD=...
#   [TEST_DB_HOST=...] [TEST_DB_PORT=...]
if os.environ.get("TEST_DB_ENGINE") == "postgresql":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ["TEST_DB_NAME"],
            "USER": os.environ["TEST_DB_USER"],
            "PASSWORD": os.environ["TEST_DB_PASSWORD"],
            "HOST": os.environ.get("TEST_DB_HOST", "127.0.0.1"),
            "PORT": os.environ.get("TEST_DB_PORT", "5432"),
        }
    }
else:
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
ROOT_URLCONF = "runtests_urls"
STATIC_URL = "static/"
WAGTAILADMIN_BASE_URL = "http://tests.local"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
