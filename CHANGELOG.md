## [0.2.9] — unreleased candidate

- Restrict the latest-comments widget to approved comments on live, public pages
  belonging to the current Wagtail Site. Cache a small display DTO instead of
  serializing complete Comment/User objects.
- Replace the cache get/set comment limiter with a database-backed conditional
  counter. The unique bucket and atomic updates keep concurrent requests from
  exceeding the configured limit across workers. Database errors fail closed
  with HTTP 503 rather than silently disabling the limiter.
- Keep replay-state writes out of form validation and perform them after the
  comment row is saved inside the same transaction. A unique database HMAC
  scoped to the browser's CSRF secret rejects concurrent replays while keeping
  the same cached form token usable in distinct browsers.
- Invalidate latest-comment cache after page publication, unpublishing, URL/site
  changes, and page-visibility restriction changes; use a new cache namespace so
  pre-upgrade Comment/User objects cannot be served from old cache entries.
- Add a cleanup command for stale rate-limit buckets and expired replay nonces,
  plus regression tests for visibility, CSRF setup, cache payloads, rate-window
  expiry, cleanup batching, and concurrent PostgreSQL use.

## [0.2.8] — 2026-11-05

- Synced the published package with the repository code that production now
  requires: the `comments/form/<page_id>/` endpoint (`comment_form_fragment`)
  for lazy-loaded comment forms and the safe redirect fix after comment POST
  (`page.get_url()` returning None no longer 500s). PyPI's 0.2.7 predates
  both; discovered during the Wagtail 8.1 production rollout when the newly
  deployed lazy comment templates started requesting the missing endpoint.

## [0.2.7] — earlier release

# Changelog — wagtail-mptt-comments

All notable changes for this package are documented here. PyPI availability is tracked per release: entries below describe the package state at that version; publication happens separately once approved.

## [0.2.5] — 2026-10-29

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
