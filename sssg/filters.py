import base64
import hashlib
import hmac
import os


def thumbor_signed(url: str):
    use_key: str | None = None
    if "SSSG_THUMBOR_KEY" in os.environ:
        use_key = os.environ["SSSG_THUMBOR_KEY"]
    if not use_key:
        print("SSSG_THUMBOR_KEY not found, falling back to unsafe")
        return "unsafe/" + url

    return (
        base64.urlsafe_b64encode(
            hmac.new(
                use_key.encode("utf-8"),
                url.encode("utf-8"),
                hashlib.sha1,
            ).digest()
        ).decode("utf-8")
        + "/"
        + url
    )
