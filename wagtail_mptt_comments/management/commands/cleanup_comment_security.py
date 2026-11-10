from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from wagtail_mptt_comments.models import CommentRateLimitBucket, ConsumedCommentNonce


class Command(BaseCommand):
    help = "Remove expired comment replay nonces and stale rate-limit buckets."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days", type=int, default=2,
            help="Remove buckets whose window started more than this many days ago (default: 2).",
        )
        parser.add_argument(
            "--batch-size", type=int, default=1000,
            help="Maximum rows per delete batch (default: 1000).",
        )

    def handle(self, *args, **options):
        days = options["days"]
        batch_size = options["batch_size"]
        if days < 1:
            raise CommandError("--days must be at least 1")
        if batch_size < 1 or batch_size > 10000:
            raise CommandError("--batch-size must be between 1 and 10000")

        now = timezone.now()
        configured_window = max(1, int(getattr(settings, "COMMENTS_RATE_WINDOW", 300)))
        minimum_retention = max(timedelta(days=days), timedelta(seconds=configured_window))
        cutoff = now - minimum_retention
        total_rate_rows = 0
        while True:
            ids = list(
                CommentRateLimitBucket.objects
                .filter(window_started_at__lt=cutoff)
                .order_by("window_started_at")
                .values_list("key_hash", flat=True)[:batch_size]
            )
            if not ids:
                break
            deleted, _details = CommentRateLimitBucket.objects.filter(key_hash__in=ids).delete()
            total_rate_rows += deleted
            if len(ids) < batch_size:
                break

        total_nonce_rows = 0
        while True:
            ids = list(
                ConsumedCommentNonce.objects
                .filter(expires_at__lt=timezone.now())
                .order_by("expires_at")
                .values_list("nonce_hash", flat=True)[:batch_size]
            )
            if not ids:
                break
            deleted, _details = ConsumedCommentNonce.objects.filter(nonce_hash__in=ids).delete()
            total_nonce_rows += deleted
            if len(ids) < batch_size:
                break

        self.stdout.write(self.style.SUCCESS(
            f"Deleted {total_rate_rows} stale rate-limit rows and {total_nonce_rows} expired nonce rows."
        ))
