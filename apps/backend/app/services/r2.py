from __future__ import annotations

import re
import uuid

import aioboto3

from app.config import settings

_VALID_SCOPES = frozenset({"video", "pdf", "imagen", "cover"})
_SLUG_RE = re.compile(r"[^a-z0-9.\-]")

_session: aioboto3.Session | None = None


def _get_session() -> aioboto3.Session:
    global _session
    if _session is None:
        _session = aioboto3.Session()
    return _session


def _slug(filename: str) -> str:
    name = filename.lower().replace(" ", "-")
    return _SLUG_RE.sub("", name)[:120] or "file"


async def build_key(scope: str, filename: str) -> str:
    if scope not in _VALID_SCOPES:
        raise ValueError(f"Invalid scope: {scope!r}. Must be one of {sorted(_VALID_SCOPES)}")
    return f"{scope}/{uuid.uuid4()}/{_slug(filename)}"


async def generate_upload_url(key: str, content_type: str, expires_in: int = 600) -> str:
    endpoint = f"https://{settings.r2_account_id}.r2.cloudflarestorage.com"
    session = _get_session()
    async with session.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=settings.r2_access_key_id,
        aws_secret_access_key=settings.r2_secret_access_key,
        region_name="auto",
    ) as s3:
        url: str = await s3.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": settings.r2_bucket,
                "Key": key,
                "ContentType": content_type,
            },
            ExpiresIn=expires_in,
        )
    return url
