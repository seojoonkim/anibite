"""Cache-Control for anonymous catalog reads.

Only GET requests without an Authorization header on public catalog paths get a
shared cache header; anything personalised stays `private, no-store`-free (left
untouched) so user-specific data is never cached by intermediaries.
"""
from starlette.types import ASGIApp, Message, Receive, Scope, Send

PUBLIC_PREFIXES = (
    "/api/anime",
    "/api/characters",
    "/api/search",
    "/api/genres",
)
PUBLIC_VALUE = b"public, max-age=60, s-maxage=300, stale-while-revalidate=600"


class PublicCacheMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http" or scope["method"] != "GET" or not scope["path"].startswith(PUBLIC_PREFIXES):
            return await self.app(scope, receive, send)
        headers = dict(scope.get("headers") or [])
        if b"authorization" in headers or b"cookie" in headers:
            return await self.app(scope, receive, send)

        async def send_with_cache(message: Message):
            if message["type"] == "http.response.start" and message["status"] == 200:
                raw = [(k, v) for k, v in message.get("headers", []) if k.lower() != b"cache-control"]
                raw.append((b"cache-control", PUBLIC_VALUE))
                raw.append((b"vary", b"Authorization, Accept-Encoding"))
                message["headers"] = raw
            await send(message)

        return await self.app(scope, receive, send_with_cache)
