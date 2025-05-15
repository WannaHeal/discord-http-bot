import logging
import typing

from starlette.requests import Request
from starlette.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from discord_http_bot.utils import verify_discord_signature

logger = logging.getLogger(__name__)


async def set_body(request: Request, body: bytes):
    async def receive() -> dict[str, typing.Any]:
        return {"type": "http.request", "body": body}

    request._receive = receive  # type: ignore


async def get_body(request: Request) -> bytes:
    body = await request.body()
    await set_body(request, body)
    return body


class CustomHeaderMiddleware(BaseHTTPMiddleware):
    _public_key: str

    def __init__(self, app: ASGIApp, public_key: str):
        super().__init__(app)
        self._public_key = public_key

    async def dispatch(
        self, request: Request, call_next: typing.Callable[[Request], typing.Awaitable[Response]]
    ) -> Response:
        if request.method != "POST":
            return await call_next(request)

        signature = request.headers.get("X-Signature-Ed25519")
        timestamp = request.headers.get("X-Signature-Timestamp")
        request_body = (await get_body(request)).decode()
        if (
            signature is None
            or timestamp is None
            or not verify_discord_signature(request_body, signature, timestamp, self._public_key)
        ):
            return Response("Bad request signature", status_code=401)
        response = await call_next(request)
        return response
