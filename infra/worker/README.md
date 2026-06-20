# IAM Media Worker

Cloudflare Worker that validates short-lived HS256 JWTs issued by the backend and proxies R2 object reads with full HTTP Range support.

## Setup

```bash
cd infra/worker
pnpm install
```

## Secrets

Never commit `MEDIA_JWT_SECRET`. Set it via CLI:

```bash
wrangler secret put MEDIA_JWT_SECRET
# Paste the same value as MEDIA_JWT_SECRET in the backend .env
```

## Development

```bash
pnpm dev
```

## Deploy

```bash
pnpm deploy
```

## R2 bucket binding

The `R2_BUCKET` binding in `wrangler.toml` points to bucket `iam-media`. Make sure the bucket exists in your Cloudflare account before deploying:

```bash
wrangler r2 bucket create iam-media
```

## Allowed origins

Set `ALLOWED_ORIGINS` as a comma-separated list of origins in `wrangler.toml` `[vars]` (or as a secret for production):

```
ALLOWED_ORIGINS = "https://app.iam.example,https://staging.iam.example"
```
