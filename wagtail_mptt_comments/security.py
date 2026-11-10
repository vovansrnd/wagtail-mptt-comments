import hashlib
import hmac

from django.conf import settings
from django.db import IntegrityError, transaction

from .models import ConsumedCommentNonce


class CommentNonceReplayError(Exception):
    """Raised when a form/captcha nonce was already consumed in this browser."""


def consume_comment_nonces(nonces, csrf_secret):
    """Atomically record ``(purpose, nonce, expires_at)`` tuples.

    The caller must include this operation in the same transaction as comment
    creation. Each digest is unique in the database and is scoped to the CSRF
    secret, not globally: visitors receiving the same cached form token do not
    invalidate one another, while parallel replays in one browser race on the
    unique primary key and only one can succeed.
    """
    if not csrf_secret:
        raise CommentNonceReplayError("The form session is missing. Reload the form.")

    with transaction.atomic():
        for purpose, nonce, expires_at in nonces:
            material = f"{purpose}\0{nonce}\0{csrf_secret}".encode("utf-8")
            digest = hmac.new(
                settings.SECRET_KEY.encode("utf-8"),
                material,
                hashlib.sha256,
            ).hexdigest()
            try:
                # Savepoint lets us translate only the expected unique-key
                # collision without poisoning the surrounding transaction.
                with transaction.atomic():
                    ConsumedCommentNonce.objects.create(
                        nonce_hash=digest,
                        expires_at=expires_at,
                    )
            except IntegrityError as exc:
                raise CommentNonceReplayError from exc
