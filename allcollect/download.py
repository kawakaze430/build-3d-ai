"""Bounded download of genuine GLB output from a private GPU backend."""
from __future__ import annotations

import os
import tempfile

import httpx

from .glb_validation import GLBInspection, GLBValidationError, MAX_GLB_BYTES, inspect_glb
from .upstream import UpstreamError, UpstreamGateway


class ArtifactTooLarge(Exception):
    """An upstream asset exceeded the configured download limit."""


async def fetch_verified_glb(
    gateway: UpstreamGateway, job_id: str, *, max_bytes: int = MAX_GLB_BYTES
) -> tuple[str, GLBInspection]:
    """Download to a private temporary file, then validate *before* responding.

    The caller owns the successful returned file and must unlink it after it
    has been served. On any error this function removes its own partial file.
    """
    client, response = await gateway.open_download(job_id)
    path: str | None = None
    success = False
    try:
        try:
            reported = int(response.headers["content-length"])
        except (KeyError, ValueError):
            reported = None
        if reported is not None and reported > max_bytes:
            raise ArtifactTooLarge("Artifact exceeds configured size limit")

        with tempfile.NamedTemporaryFile(mode="w+b", suffix=".glb", delete=False) as tmp:
            path = tmp.name
            count = 0
            async for chunk in response.aiter_bytes(chunk_size=256 * 1024):
                count += len(chunk)
                if count > max_bytes:
                    raise ArtifactTooLarge("Artifact exceeds configured size limit")
                tmp.write(chunk)
            tmp.flush()
            report = inspect_glb(tmp, max_bytes=max_bytes)
        success = True
        return path, report
    except GLBValidationError as exc:
        raise UpstreamError(f"3D engine returned invalid GLB: {exc}") from exc
    except (httpx.HTTPError, OSError) as exc:
        raise UpstreamError("3D engine download could not be completed") from exc
    finally:
        try:
            await response.aclose()
        finally:
            await client.aclose()
        if not success and path is not None:
            try:
                os.unlink(path)
            except FileNotFoundError:
                pass
