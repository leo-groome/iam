import { jwtVerify } from "jose";

export interface Env {
  R2_BUCKET: R2Bucket;
  MEDIA_JWT_SECRET: string;
  ALLOWED_ORIGINS: string;
}

const AUDIENCE = "r2-worker";

function getAllowedOrigins(env: Env): Set<string> {
  return new Set(
    env.ALLOWED_ORIGINS.split(",")
      .map((o) => o.trim())
      .filter(Boolean)
  );
}

function originAllowed(request: Request, env: Env): boolean {
  const allowedOrigins = getAllowedOrigins(env);
  if (allowedOrigins.size === 0) {
    return true;
  }

  const origin = request.headers.get("Origin");
  const referer = request.headers.get("Referer");

  if (origin) {
    return allowedOrigins.has(origin);
  }
  if (referer) {
    try {
      const refererOrigin = new URL(referer).origin;
      return allowedOrigins.has(refererOrigin);
    } catch {
      return false;
    }
  }
  return false;
}

async function verifyToken(
  token: string,
  secret: string
): Promise<{ key: string } | null> {
  try {
    const keyBytes = new TextEncoder().encode(secret);
    const { payload } = await jwtVerify(token, keyBytes, {
      algorithms: ["HS256"],
      audience: AUDIENCE,
    });
    const key = payload["key"];
    if (typeof key !== "string" || !key) return null;
    return { key };
  } catch {
    return null;
  }
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    if (!originAllowed(request, env)) {
      return new Response("Forbidden: hotlinking not allowed", { status: 403 });
    }

    // Extract token from Authorization header only. Query-string tokens leak via logs.
    let token: string | null = null;
    const authHeader = request.headers.get("Authorization");
    if (authHeader?.startsWith("Bearer ")) {
      token = authHeader.slice(7);
    }

    if (!token) {
      return new Response("Unauthorized: missing token", { status: 401 });
    }

    const claims = await verifyToken(token, env.MEDIA_JWT_SECRET);
    if (!claims) {
      return new Response("Unauthorized: invalid or expired token", {
        status: 401,
      });
    }

    // Validate that the requested path matches the token's key claim
    const url = new URL(request.url);
    const requestedKey = url.pathname.replace(/^\//, "");
    if (requestedKey !== claims.key) {
      return new Response("Forbidden: path does not match token key", {
        status: 403,
      });
    }

    // Parse Range header for partial content support
    const rangeHeader = request.headers.get("Range");
    const r2Options: R2GetOptions = {};
    if (rangeHeader) {
      const match = /bytes=(\d+)-(\d*)/.exec(rangeHeader);
      if (match) {
        const start = parseInt(match[1], 10);
        const end = match[2] ? parseInt(match[2], 10) : undefined;
        r2Options.range =
          end !== undefined
            ? { offset: start, length: end - start + 1 }
            : { offset: start };
      }
    }

    const object = await env.R2_BUCKET.get(claims.key, r2Options);

    if (!object) {
      return new Response("Not Found", { status: 404 });
    }

    const headers = new Headers();
    object.writeHttpMetadata(headers);
    headers.set("Accept-Ranges", "bytes");
    headers.set("Cache-Control", "private, no-store");

    if (rangeHeader && object.range) {
      const range = object.range as { offset: number; length: number };
      const totalSize = object.size;
      const start = range.offset;
      const end = start + range.length - 1;
      headers.set("Content-Range", `bytes ${start}-${end}/${totalSize}`);
      headers.set("Content-Length", String(range.length));
      return new Response(object.body, { status: 206, headers });
    }

    headers.set("Content-Length", String(object.size));
    return new Response(object.body, { status: 200, headers });
  },
};
