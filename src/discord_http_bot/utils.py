from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError


def verify_discord_signature(
    request_body: str,
    signature: str,
    timestamp: str,
    public_key: str,
) -> bool:
    try:
        verify_key = VerifyKey(bytes.fromhex(public_key))
        verify_key.verify(f'{timestamp}{request_body}'.encode(), bytes.fromhex(signature))
        return True
    except BadSignatureError:
        return False
