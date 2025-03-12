from django.core.signing import TimestampSigner
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

signer = TimestampSigner()


def generate_verification_token(user) -> str:
    user_id_encoded = urlsafe_base64_encode(force_bytes(user.pk))
    signed_token = signer.sign(user_id_encoded)
    return signed_token
