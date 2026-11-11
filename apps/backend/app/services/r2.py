from __future__ import annotations

import re
import uuid

import aioboto3

from app.config import settings

_VALID_SCOPES = frozenset({"video", "pdf", "imagen", "cover", "audio"})
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


MAX_UPLOAD_BYTES: dict[str, int] = {
    "video": 500 * 1024 * 1024,
    "pdf": 50 * 1024 * 1024,
    "audio": 50 * 1024 * 1024,
    "imagen": 10 * 1024 * 1024,
    "cover": 5 * 1024 * 1024,
}

# Firmas (magic bytes) por scope: (offset, bytes). Basta con que coincida una.
_MAGIC: dict[str, tuple[tuple[int, bytes], ...]] = {
    "pdf": ((0, b"%PDF-"),),
    "imagen": ((0, b"\xff\xd8\xff"), (0, b"\x89PNG\r\n\x1a\n"), (8, b"WEBP")),
    "video": ((4, b"ftyp"), (0, b"\x1a\x45\xdf\xa3")),
    "audio": ((0, b"ID3"), (0, b"\xff\xfb"), (0, b"\xff\xf3"), (0, b"\xff\xf2"), (4, b"ftyp")),
}


def matches_magic(scope: str, head: bytes) -> bool:
    return any(head[off : off + len(sig)] == sig for off, sig in _MAGIC.get(scope, ()))


async def inspect_object(key: str, scope: str) -> str | None:
    """Verifica que el objeto exista, respete el tamaño máximo y tenga magic bytes válidos.

    Devuelve un mensaje de error o None si todo está bien.
    """
    endpoint = settings.r2_endpoint_url or f"https://{settings.r2_account_id}.r2.cloudflarestorage.com"
    async with _get_session().client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=settings.r2_access_key_id,
        aws_secret_access_key=settings.r2_secret_access_key,
        region_name="auto",
    ) as s3:
        try:
            head = await s3.head_object(Bucket=settings.r2_bucket, Key=key)
            if head["ContentLength"] > MAX_UPLOAD_BYTES.get(scope, 0):
                return "El archivo excede el tamaño máximo permitido."
            obj = await s3.get_object(Bucket=settings.r2_bucket, Key=key, Range="bytes=0-15")
            first = await obj["Body"].read()
        except s3.exceptions.NoSuchKey:
            return "El archivo no existe en el almacenamiento."
        except Exception as exc:  # noqa: BLE001 — 404/403 de S3 llegan como ClientError
            if getattr(exc, "response", {}).get("Error", {}).get("Code") in {"404", "NoSuchKey", "NotFound"}:
                return "El archivo no existe en el almacenamiento."
            raise
    if not matches_magic(scope, first):
        return "El contenido del archivo no corresponde a su tipo."
    return None


async def generate_upload_url(
    key: str, content_type: str, expires_in: int = 600, content_length: int | None = None
) -> str:
    endpoint = settings.r2_endpoint_url or f"https://{settings.r2_account_id}.r2.cloudflarestorage.com"
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
                **({"ContentLength": content_length} if content_length is not None else {}),
            },
            ExpiresIn=expires_in,
        )
    return url


async def count_pdf_pages(key: str) -> int:
    """Descarga el PDF de R2 y cuenta sus páginas con pypdf (autoritativo, lado servidor)."""
    import asyncio
    import io

    from pypdf import PdfReader

    endpoint = settings.r2_endpoint_url or f"https://{settings.r2_account_id}.r2.cloudflarestorage.com"
    async with _get_session().client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=settings.r2_access_key_id,
        aws_secret_access_key=settings.r2_secret_access_key,
        region_name="auto",
    ) as s3:
        obj = await s3.get_object(Bucket=settings.r2_bucket, Key=key)
        data = await obj["Body"].read()
    if len(data) > MAX_UPLOAD_BYTES["pdf"]:
        raise ValueError("PDF demasiado grande")
    return await asyncio.get_running_loop().run_in_executor(
        None, lambda: len(PdfReader(io.BytesIO(data)).pages)
    )
