# wagtail-mptt-comments

**Threaded comments and moderation for Wagtail CMS.** The package stores comments as a nested MPTT tree, includes guest anti-spam controls, provides a Wagtail admin moderation interface, and exposes template tags for the comment form/tree and recent-comment widgets.

Use this package for article/page comments. It is not a forum engine and does not provide topics, sections, or private messages.

[English](README.md) · [Русский](README.ru.md) · [Deutsch](README.de.md) · [Español](README.es.md) · [Français](README.fr.md) · [Italiano](README.it.md) · [Português (Brasil)](README.pt-BR.md) · [Nederlands](README.nl.md) · [Polski](README.pl.md) · [Türkçe](README.tr.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [한국어](README.ko.md)

![Comment tree](comments-tree-preview.png)

## Features

- Nested replies powered by `django-mptt`, with configurable depth.
- Guest anti-spam checks: honeypot, a signed page-bound form token, a signed math challenge, browser-scoped replay detection, and a database-backed atomic per-IP/account rate limiter. These are layered friction/rate-limit controls, not a replacement for a WAF or abuse monitoring.
- Optional moderation for new comments and email notifications to administrators.
- User, guest, moderator, and administrator badges; optional notification to a comment author when someone replies.
- Wagtail admin list and tree views, bulk approve/delete actions, and administrator responses.
- Template tags for rendering a page's comments and a latest-comments sidebar.
- Multi-site filtering so page comments and recent-comment widgets are restricted to the current Wagtail Site.
- CSS variables for front-end theming, and a Prose-based editor for comment/admin-response content.


## Compatibility

The package metadata declares a minimum of `wagtail>=6.0`; that is the
supported floor, not the full test matrix. The two tested configurations
differ in kind: Wagtail 8.0.1 is covered by integration tests of the
originating project with editable installs of this package, while
Wagtail 8.1 was tested against the target production stack with clean
wheel and sdist installs — both with Django 6.0.9 on Python 3.14.
Other combinations may work but are not covered by the test suite.

## Requirements and installation

Package metadata declares `wagtail>=6.0`, `django-mptt>=0.16.0`, `django-prose-editor>=0.26`, and `nh3>=0.2.14`.

```bash
pip install wagtail-mptt-comments==0.2.9
```

```bash
python -m pip install .
```



Add the app after its dependencies:

```python
INSTALLED_APPS = [
    # ... Django and Wagtail apps ...
    "mptt",
    "django_prose_editor",
    "wagtail_mptt_comments",
]
```

Include the URL namespace:

```python
from django.urls import include, path

urlpatterns = [
    # ...
    path("comments/", include("wagtail_mptt_comments.urls")),
]
```

Apply the package migrations:

```bash
python manage.py migrate wagtail_mptt_comments
```

The package does not require a custom Wagtail Page model. Your commentable page is passed to the template tag.

## Render comments in a page template

```django
{% load mptt_comment_tags %}

<h1>{{ page.title }}</h1>
{% render_comments page %}
```

`render_comments` supplies the approved comment tree and form. Avoid preparing the same tree/count/form in `Page.get_context()` as well; duplicate preparation causes repeated database work and can diverge from plugin behavior.

## Recent-comments widget

```django
{% load mptt_comment_tags wagtailcore_tags %}

{% get_latest_comments 5 as latest_comments %}
<ul>
  {% for comment in latest_comments %}
    <li>
      <a href="{% pageurl comment.page %}#comment-{{ comment.id }}">
        <strong>{{ comment.display_author_name }}</strong>:
        {{ comment.content|striptags|truncatewords:10 }}
      </a>
    </li>
  {% endfor %}
</ul>
```

The latest-comments widget cache is invalidated after page publish/unpublish, page visibility restriction changes, page moves/slug changes, and Site changes. Its short cache lifetime also bounds any missed invalidation. The template tag is intended for the current Wagtail Site. It returns only approved comments attached to live, public pages of that Site. Keep it in a request context where the current `request` and Site are available. If your project has custom domain routing or serves content outside a configured Wagtail Site, verify that the widget returns no cross-site comments rather than broadening to all sites. The cache stores only integer comment IDs rather than Comment/User model instances; on every call the IDs are resolved back to full Comment instances after re-checking the same eligibility predicates (approved, live public page of the current Site), so a stale ID can never surface a hidden, unapproved, or foreign-site comment.

## Settings

All settings are optional. Current defaults in the package source are:

| Setting | Default | Meaning |
|---|---:|---|
| `COMMENTS_MODERATION` | `True` | Guest comments require moderation by default. |
| `COMMENTS_NOTIFY_ADMINS` | `False` | Email administrators about new comments. |
| `COMMENTS_MODERATOR_GROUPS` | `None` | Django group names whose members receive the moderator badge/role. |
| `COMMENTS_MAX_LENGTH` | `20000` | Maximum comment text length. |
| `COMMENTS_RATE_LIMIT` | `10` | Maximum public comment POSTs per IP/account in one rate window. |
| `COMMENTS_RATE_WINDOW` | `300` seconds | Rolling-window length for the public comment limiter. |
| `COMMENTS_CAPTCHA_MAX_AGE` | `7200` seconds | Maximum age of the signed math-captcha token. |
| `COMMENTS_FORM_TOKEN_MAX_AGE` | `7200` seconds | Maximum age of the signed page-bound form token. |
| `COMMENTS_TRUST_PROXY_HEADERS` | `False` | Allow reading a forwarded client-IP chain, but only when `REMOTE_ADDR` matches a trusted proxy network. |
| `COMMENTS_TRUSTED_PROXY_IPS` | `()` | Comma-separated IP addresses/CIDRs of trusted reverse proxies. Never use `0.0.0.0/0` or `::/0`. |
| `SITE_NAME` | project-dependent | Site name used in messages where needed. |
| `DEFAULT_FROM_EMAIL` | Django default | Sender address for notifications. |

Example:

```python
COMMENTS_MODERATION = True
COMMENTS_NOTIFY_ADMINS = True
COMMENTS_MODERATOR_GROUPS = ["Moderators"]
COMMENTS_MAX_LENGTH = 20_000
COMMENTS_RATE_LIMIT = 10
COMMENTS_RATE_WINDOW = 300
COMMENTS_TRUST_PROXY_HEADERS = False  # keep false until proxy behavior is verified
COMMENTS_TRUSTED_PROXY_IPS = ()  # e.g. ("10.0.0.10/32",) after confirmation
DEFAULT_FROM_EMAIL = "noreply@example.com"
```

Set up Django email delivery if notifications are enabled. Review the content and privacy requirements for storing commenter names, email addresses, IP-derived rate-limit data, and notification preferences.

**Reverse proxy / rate limiting:** keep `COMMENTS_TRUST_PROXY_HEADERS=False` unless the hosting provider confirms the proxy address range and confirms that `X-Forwarded-For` is overwritten or appended safely. Then set `COMMENTS_TRUST_PROXY_HEADERS=True` and list only the provider proxy IPs/CIDRs in `COMMENTS_TRUSTED_PROXY_IPS`. The package ignores forwarded headers from untrusted peers and walks the chain from right to left. Do not trust arbitrary client-supplied XFF headers.

## Styling

Load the package's `comments.css` and override CSS custom properties in your theme stylesheet. For example:

```css
.article-comments {
  --mptt-bg: #1c2226;
  --mptt-card-bg: #1c2226;
  --mptt-accent: #0e8a86;
  --mptt-accent-hover: #26b5a9;
  --mptt-text: #eaeef0;
  --mptt-border: #2c3437;
}
```

Use your actual wrapper selector, and load the override after the plugin stylesheet.

## Security and operations

- Keep `nh3` and the package dependencies updated. Do not render user-authored HTML with `|safe` in custom templates.
- Test guest posting, CSRF, replay attempts from the same browser, concurrent replay, moderation, reply links, email, and collection/site separation with normal users, moderators, and administrators. Replay records are stored as HMACs scoped to the browser's CSRF secret, so the same cached form token can be used by different browsers without allowing repeated submissions from one browser.
- The database-backed rate limiter applies per client IP for anonymous visitors and per account for authenticated visitors. It does not replace an upstream WAF. The lazy comment-form endpoint sets a CSRF cookie even when a theme overrides the fragment template; custom form templates must still render `{% csrf_token %}` inside the POST form.
- **Rate-limit policy (intended behaviour):** every POST to the comment endpoint consumes one limiter slot *before* form validation. Invalid or spam-shaped submissions are therefore not free — repeated invalid POSTs exhaust the visitor's quota exactly like valid ones. (The form nonce is only consumed on a validated submission, so a visitor can correct a typo without reloading the form, as long as the rate window is not exhausted.) Counters use conditional SQL UPDATEs, so parallel requests on PostgreSQL cannot pass the same remaining slot, and a window resets exactly when `window_started_at <= now - COMMENTS_RATE_WINDOW`. If you need "only valid submissions count", that is a separate change request, not the current policy.
- Run `python manage.py cleanup_comment_security --days 2` periodically (for example, once a day) to remove expired nonce records and stale rate-limit buckets. A bucket is retained for at least the configured `COMMENTS_RATE_WINDOW`, even when that window exceeds `--days`. The command does not touch comments or media.
- When using multiple Wagtail Sites, test the latest-comments widget on every domain, including an unknown/unconfigured host.
- The source distribution includes the package regression tests. Run the full Django/Wagtail suite, apply migrations in a disposable database, and smoke-test against your exact dependencies before upgrading. The package's published compatibility statement still describes the versions actually tested, not every version allowed by `wagtail>=6.0`.

## Recommended combinations

- **`wagtail-prose-editor-images`** is useful if administrator responses or related Prose fields need the Wagtail Image Chooser. The packages are separately installable; test the exact field configuration.
- **`wagtail-image-directories`** complements this package only when the site also needs structured image storage; comments themselves do not require it.
- Use **`wagtail-simple-forum`** for discussion boards and private messages, not as a replacement for article comments.

## License and support

MIT. Source and issue tracker: [GitHub](https://github.com/vovansrnd/wagtail-mptt-comments). Do not include commenter personal data, production tokens, or private URLs in bug reports.
