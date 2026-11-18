"""Bound request bodies before multipart spooling, including chunked uploads."""
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse

from .images import MAX_IMAGE_BYTES


class BodyLimitMiddleware:
    def __init__(self, app, max_bytes=MAX_IMAGE_BYTES + 128 * 1024):
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        for key, value in scope.get("headers", []):
            if key == b"content-length":
                try:
                    length = int(value)
                except ValueError:
                    length = -1
                if length < 0 or length > self.max_bytes:
                    response = JSONResponse({"detail": "Invalid or oversized request body"},
                                            status_code=413 if length > self.max_bytes else 400)
                    return await response(scope, receive, send)
        received = 0

        async def bounded_receive():
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_bytes:
                    raise HTTPException(413, "Request body exceeds upload limit")
            return message

        return await self.app(scope, bounded_receive, send)
