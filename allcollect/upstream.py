"""API client for self-hosted FishWoWater/3DAIGC-API.

All model generation is performed by the real upstream GPU service.
No fake meshes, model fallbacks or hidden public AI APIs.
"""

from __future__ import annotations

import httpx


class UpstreamError(Exception):
    """Operational failure of the remote model service."""


class UpstreamGateway:
    def __init__(
        self,
        base_url: str,
        bearer_token: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/") + "/"
        self.bearer_token = bearer_token
        self.transport = transport

    def _client(self) -> httpx.AsyncClient:
        headers = {}
        if self.bearer_token:
            headers["Authorization"] = f"Bearer {self.bearer_token}"
        return httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=httpx.Timeout(90.0, connect=10.0),
            transport=self.transport,
            follow_redirects=False,
        )

    async def request_json(self, method: str, path: str, **kwargs: object) -> object:
        try:
            async with self._client() as client:
                response = await client.request(method, path.lstrip("/"), **kwargs)
                if response.status_code >= 400:
                    raise UpstreamError(
                        f"3D engine rejected request (HTTP {response.status_code})"
                    )
                return response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise UpstreamError("3D engine unavailable or returned invalid JSON") from exc

    async def list_models(self) -> object:
        return await self.request_json("GET", "api/v1/system/models")

    async def status(self) -> object:
        return await self.request_json("GET", "api/v1/system/status/")

    async def text_to_3d(self, prompt: str, model_preference: str | None) -> object:
        payload: dict[str, object] = {
            "text_prompt": prompt,
            "output_format": "glb",
        }
        if model_preference:
            payload["model_preference"] = model_preference
        return await self.request_json(
            "POST", "api/v1/mesh-generation/text-to-textured-mesh", json=payload
        )

    async def image_to_3d(
        self, data: bytes, mime: str, model_preference: str | None
    ) -> object:
        uploaded = await self.request_json(
            "POST",
            "api/v1/file-upload/image",
            files={"file": ({"image/png": "reference.png", "image/jpeg": "reference.jpg", "image/webp": "reference.webp"}[mime], data, mime)},
        )
        if not isinstance(uploaded, dict) or not isinstance(uploaded.get("file_id"), str):
            raise UpstreamError("3D engine did not return a valid image file_id")
        payload: dict[str, object] = {
            "image_file_id": uploaded["file_id"],
            "output_format": "glb",
        }
        if model_preference:
            payload["model_preference"] = model_preference
        return await self.request_json(
            "POST", "api/v1/mesh-generation/image-to-textured-mesh", json=payload
        )

    async def job(self, job_id: str) -> object:
        return await self.request_json("GET", f"api/v1/system/jobs/{job_id}")

    async def open_download(self, job_id: str) -> tuple[httpx.AsyncClient, httpx.Response]:
        """Caller MUST close both response and client after stream completion."""
        client = self._client()
        try:
            req = client.build_request("GET", f"api/v1/system/jobs/{job_id}/download")
            response = await client.send(req, stream=True)
            if response.status_code >= 400:
                await response.aclose()
                await client.aclose()
                raise UpstreamError(
                    f"3D engine cannot download this result (HTTP {response.status_code})"
                )
            return client, response
        except httpx.HTTPError as exc:
            await client.aclose()
            raise UpstreamError("Unable to stream a result from the 3D engine") from exc
