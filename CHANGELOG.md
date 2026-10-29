# Changelog — wagtail-mptt-comments

All notable changes for this package are documented here. Version numbers below are **prepared release candidates** in this audit bundle; they are not a claim that those versions have already been uploaded to PyPI.

## [0.2.5] — 2026-10-29 — prepared, not yet published

- Harden site-scoped latest-comment queries and HTML rendering; preserve transaction-safe notifications; expand deployment and multi-site guidance.
- Expanded installation, security, troubleshooting, storage/integration and multi-language documentation.
- Added translated README files for English, Russian, German, Spanish, French, Italian, Brazilian Portuguese, Dutch, Polish, Turkish, Simplified Chinese, Japanese and Korean.
- Static syntax/packaging checks are included in the release bundle. Complete Django/Wagtail integration tests and live storage/permission checks remain a release gate.

## Previous releases

See the package's release history on PyPI and its source repository, where available.

## 2026-10-29 — follow-up audit

- Signed page-bound form and captcha tokens; added expiry, per-session replay checks, and per-page draft keys.
- Made the latest-comments widget site-scoped, version-cached, and invalidated on changes.
- Sanitized comment HTML and forced `nofollow ugc noopener noreferrer` on links.
- Prefetched moderation-list profile/group data and batched MPTT rebuilds after bulk deletion.

A runtime test pass on the host's Django/Wagtail versions is still required.
