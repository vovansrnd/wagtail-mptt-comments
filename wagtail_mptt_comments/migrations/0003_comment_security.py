from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wagtail_mptt_comments", "0002_alter_comment_page"),
    ]

    operations = [
        migrations.CreateModel(
            name="ConsumedCommentNonce",
            fields=[
                ("nonce_hash", models.CharField(max_length=64, primary_key=True, serialize=False)),
                ("expires_at", models.DateTimeField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "Consumed comment form nonce",
                "verbose_name_plural": "Consumed comment form nonces",
            },
        ),
        migrations.CreateModel(
            name="CommentRateLimitBucket",
            fields=[
                ("key_hash", models.CharField(max_length=64, primary_key=True, serialize=False)),
                ("window_started_at", models.DateTimeField(db_index=True)),
                ("count", models.PositiveIntegerField(default=0)),
            ],
            options={
                "verbose_name": "Comment rate-limit bucket",
                "verbose_name_plural": "Comment rate-limit buckets",
            },
        ),
    ]
