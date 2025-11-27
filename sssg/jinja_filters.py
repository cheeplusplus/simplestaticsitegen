import base64
import hashlib
import hmac
import os
from collections.abc import Callable


def b64encode(text: str) -> str:
    return base64.b64encode(text.encode("utf-8")).decode("utf-8")


def b64decode(text: str) -> str:
    return base64.b64decode(text).decode("utf-8")


def urlsafe_b64encode(text: str) -> str:
    return base64.urlsafe_b64encode(text.encode("utf-8")).decode("utf-8")


def urlsafe_b64decode(text: str) -> str:
    return base64.urlsafe_b64decode(text).decode("utf-8")


def sign_sha1(value: str) -> str:
    use_key: str | None = None
    if "SSSG_SIGN_KEY" in os.environ:
        use_key = os.environ["SSSG_SIGN_KEY"]
    if not use_key:
        raise Exception("SSSG_SIGN_KEY not found")

    return base64.urlsafe_b64encode(
        hmac.new(
            use_key.encode("utf-8"),
            value.encode("utf-8"),
            hashlib.sha1,
        ).digest()
    ).decode("utf-8")


def add_custom_filters(filters: dict[str, Callable[[str], str]]):
    filters["b64decode"] = b64decode
    filters["b64encode"] = b64encode
    filters["sign_sha1"] = sign_sha1
    filters["urlsafe_b64decode"] = urlsafe_b64decode
    filters["urlsafe_b64encode"] = urlsafe_b64encode
