"""Local stand-in for infra/worker (Cloudflare Worker): same auth/CORS/Range
rules, but reads from the local MinIO bucket instead of R2. Dev/QA only."""
import os

import boto3
import httpx
import jwt
from botocore.config import Config
from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse

AUDIENCE = "r2-worker"
SECRET = os.environ["MEDIA_JWT_SECRET"]
BUCKET = os.environ["S3_BUCKET"]
PUBLIC_PREFIXES = ("cover/", "imagen/")

s3 = boto3.client(
    "s3",
    endpoint_url=os.environ["S3_ENDPOINT"],
    aws_access_key_id=os.environ["S3_ACCESS_KEY"],
    aws_secret_access_key=os.environ["S3_SECRET_KEY"],
    region_name="auto",
    config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
)
app = FastAPI()
client = httpx.AsyncClient(timeout=None)


def cors(request: Request, public: bool) -> dict[str, str]:
    origin = request.headers.get("origin")
    h = {
        "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
        "Access-Control-Allow-Headers": "Authorization, Range, Content-Type",
        "Access-Control-Expose-Headers": "Content-Range, Content-Length, Accept-Ranges",
        "Cross-Origin-Resource-Policy": "cross-origin",
        "Vary": "Origin",
    }
    if public:
        h["Access-Control-Allow-Origin"] = "*"
    elif origin and ("localhost" in origin or "127.0.0.1" in origin):
        h["Access-Control-Allow-Origin"] = origin
    return h


@app.api_route("/{key:path}", methods=["GET", "HEAD", "OPTIONS"])
async def serve(key: str, request: Request):
    public = key.startswith(PUBLIC_PREFIXES)
    headers = cors(request, public)
    if request.method == "OPTIONS":
        return Response(status_code=204, headers=headers)
    if not public:
        auth = request.headers.get("authorization", "")
        token = auth[7:] if auth.startswith("Bearer ") else request.query_params.get("token")
        if not token:
            return Response("Unauthorized: missing token", 401, headers)
        try:
            claims = jwt.decode(token, SECRET, algorithms=["HS256"], audience=AUDIENCE)
        except jwt.PyJWTError:
            return Response("Unauthorized: invalid or expired token", 401, headers)
        if claims.get("key") != key:
            return Response("Forbidden: path does not match token key", 403, headers)

    url = s3.generate_presigned_url(
        "get_object", Params={"Bucket": BUCKET, "Key": key}, ExpiresIn=60
    )
    up_headers = {}
    if "range" in request.headers:
        up_headers["Range"] = request.headers["range"]
    req = client.build_request(request.method, url, headers=up_headers)
    upstream = await client.send(req, stream=True)
    if upstream.status_code == 404 or upstream.status_code == 403:
        await upstream.aclose()
        return Response("Not Found", 404, headers)
    for h in ("content-type", "content-length", "content-range", "accept-ranges"):
        if h in upstream.headers:
            headers[h] = upstream.headers[h]
    headers["Accept-Ranges"] = "bytes"
    headers["Cache-Control"] = "private, no-store"
    return StreamingResponse(
        upstream.aiter_raw(), status_code=upstream.status_code,
        headers=headers, background=None,
    )
