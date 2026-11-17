#!/usr/bin/env python
"""Д67-Б: раннер тестов wagtail-mptt-comments с гарантией site-packages-импорта.

Падает, если wagtail_mptt_comments импортирован из каталога исходников,
а не из wheel в site-packages.

    python runtests.py
"""
import os
import sys

_repo_root = os.path.dirname(os.path.abspath(__file__))
# Корень репо НЕ должен затенять установленный wheel: убираем его из
# sys.path целиком (иначе wagtail_mptt_comments импортируется из исходников).
sys.path[:] = [p for p in sys.path
               if os.path.abspath(p or ".") != _repo_root]
# tests_settings.py живёт в корне репо — вернуть ТОЛЬКО его после чистки
sys.path.append(_repo_root)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests_settings")

import django  # noqa: E402

django.setup()

import wagtail_mptt_comments  # noqa: E402

_pkg = wagtail_mptt_comments.__file__.replace(os.sep, "/")
if "site-packages" not in _pkg:
    sys.exit(f"ОШИБКА: импортирован НЕ wheel: {_pkg}")
print("проверяемый пакет (wheel):", _pkg)

import django.conf  # noqa: E402
from django.test.utils import get_runner  # noqa: E402

runner = get_runner(django.conf.settings)(interactive=False, verbosity=1)
# Явные метки модулей: discovery по каталогу пакета спотыкается о
# двойной импорт tests (unittest/loader.py: "module incorrectly imported").
# Публично-контрактные тесты — модуль в корне репо (импортируются после
# установки wheel из site-packages; корень добавлен в sys.path последним).
failures = runner.run_tests([
    "wagtail_mptt_comments.tests",
    "wagtail_mptt_comments.tests_security",
    "public_contract_tests",
])
sys.exit(bool(failures))
