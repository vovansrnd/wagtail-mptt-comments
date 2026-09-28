# wagtail-mptt-comments

Nested, threaded comments with MPTT hierarchy, multi-layer anti-spam protection, and an AJAX bulk moderation dashboard for Wagtail CMS.

![Wagtail Comments Tree Preview](https://raw.githubusercontent.com/vovansrnd/wagtail-mptt-comments/main/comments-tree-preview.png)
![Wagtail Comments Form Preview](https://raw.githubusercontent.com/vovansrnd/wagtail-mptt-comments/main/comment-form.png)

## Features

- **Hierarchical Threading**: Fast nested comment trees powered by `django-mptt`, with a configurable max nesting depth.
- **Wagtail Multi-Site Support**: Built-in support for multi-domain setups. Sidebar widgets and listings automatically isolate comments per site without data leaking between domains.
- **Three-Layer Spam Protection**:
  - Transparent honeypot traps.
  - Form submission speed verification (blocks instant bot auto-fillers).
  - Built-in lightweight math captcha for guest commentators.
- **Author Roles & Badges**: Automatically distinguishes guests, registered members, moderators, and admins based on `is_staff`/`is_superuser` and configurable moderator groups — rendered as a role badge next to each comment.
- **Theme-Aware Avatars**: Uses the user's profile picture when available, or a neutral inline SVG placeholder that inherits its color via `currentColor` — so it stays readable on any background, light or dark, instead of a hardcoded PNG silhouette.
- **Deep Linking**: Every comment gets a real `id="comment-<pk>"` anchor, so links like `/page/#comment-42` (used after posting a reply, or shared directly) actually scroll to and highlight the right comment.
- **Reply Notifications**: Optional "notify me on reply" checkbox — when someone replies to a comment, its author gets an email if they opted in.
- **Wagtail Admin Dashboard**:
  - List and interactive tree moderation views.
  - AJAX bulk approval and deletion.
  - In-place admin responses, shown publicly beneath the original comment.
  - Fully theme-aware admin UI — respects Wagtail's light/dark theme instead of imposing its own palette.
- **WYSIWYG Rich Text**: Integrated with `django-prose-editor` (bold, italics, quotes, lists, links, code blocks).
- **Ready-to-use Frontend Styles**: Clean, modular CSS themed entirely through CSS custom properties (`--mptt-accent`, `--mptt-bg`, etc.) — override them from your own stylesheet to match your site's palette in a couple of lines.

![Admin Moderation Dashboard](https://raw.githubusercontent.com/vovansrnd/wagtail-mptt-comments/main/admin-moderation-preview.png)
![Admin Moderation Dashboard Tree](https://raw.githubusercontent.com/vovansrnd/wagtail-mptt-comments/main/admin-moderation-preview-tree.png)

## Installation

```bash
pip install wagtail-mptt-comments
```

Add required apps to `INSTALLED_APPS` in your `settings.py`:

```python
INSTALLED_APPS = [
    ...
    "mptt",
    "wagtail_mptt_comments",
    ...
]
```

Include URLs in `urls.py`:

```python
from django.urls import include, path

urlpatterns = [
    ...
    path("comments/", include("wagtail_mptt_comments.urls")),
    ...
]
```

Run database migrations:

```bash
python manage.py migrate
```

### Optional settings

```python
# settings.py

# Send an email to DEFAULT_FROM_EMAIL whenever a new comment is posted.
COMMENTS_NOTIFY_ADMINS = True

# Auto-approve guest comments instead of sending them to moderation.
# Authenticated users are always auto-approved.
COMMENTS_MODERATION = True  # default: True (guests go to moderation)

# Group names whose members get the "Moderator" badge on their comments.
COMMENTS_MODERATOR_GROUPS = ["Moderators"]

SITE_NAME = "My Site"
DEFAULT_FROM_EMAIL = "noreply@example.com"
```

## Rendering in Templates

### 1. Comments Block on Page
In your page template (e.g. `blog_page.html`), simply load the tags and call `render_comments`:

```html
{% extends "base.html" %}
{% load mptt_comment_tags %}

{% block content %}
    <h1>{{ page.title }}</h1>
    
    <!-- This tag automatically loads the comment tree and the reply form -->
    {% render_comments page %}
{% endblock %}
```

### 2. Latest Comments Sidebar Widget
To display recent comments in a sidebar or footer (automatically filtered by the current site in multi-site setups):

```html
{% load mptt_comment_tags wagtailcore_tags %}

{% get_latest_comments 5 as latest_comments %}
<ul class="latest-comments-widget">
    {% for comment in latest_comments %}
        <li>
            <a href="{% pageurl comment.page %}#comment-{{ comment.id }}">
                <strong>{{ comment.display_author_name }}</strong>:
                <span>{{ comment.content|striptags|truncatewords:10 }}</span>
            </a>
        </li>
    {% endfor %}
</ul>
```

### Theming

Override the CSS custom properties from your own stylesheet (loaded *after* `comments.css`) to match your site's design — no need to touch the plugin's files:

```css
.article-container {
    --mptt-bg: #1c2226;
    --mptt-card-bg: #1c2226;
    --mptt-accent: #0e8a86;
    --mptt-accent-hover: #26b5a9;
    --mptt-text: #eaeef0;
    --mptt-border: #2c3437;
}
```

## Recommended Complementary Packages

- **[wagtail-prose-editor-images](https://github.com/vovansrnd/wagtail-prose-editor-images)**: Add a native Wagtail Image Chooser button to the prose editor.

![Wagtail Prose Editor with Image Chooser](https://raw.githubusercontent.com/vovansrnd/wagtail-prose-editor-images/main/prose-editor-preview.png)

- **[wagtail-image-directories](https://github.com/vovansrnd/wagtail-image-directories)**: Organize uploaded images into structured `year/slug` folders on disk.

![Wagtail Image Navigator Dashboard](https://raw.githubusercontent.com/vovansrnd/wagtail-image-directories/main/navigator-preview.png)

## Case Study & Background

Read the full story behind the migration and architecture on our blog: [Vs-Svet.ru](https://vs-svet.ru/) / [ZenWay.ru](https://zenway.ru/).
