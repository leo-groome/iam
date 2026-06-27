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

function getRequestOrigin(request: Request): string | null {
  const origin = request.headers.get("Origin");
  if (origin) return origin;
  const referer = request.headers.get("Referer");
  if (referer) {
    try {
      return new URL(referer).origin;
    } catch {
      return null;
    }
  }
  return null;
}

function originAllowed(request: Request, env: Env): boolean {
  const allowedOrigins = getAllowedOrigins(env);
  if (allowedOrigins.size === 0) return true;
  const origin = getRequestOrigin(request);
  if (!origin) return false;
  return allowedOrigins.has(origin);
}

/** Add CORS headers so the browser accepts the response from a different origin. */
function addCorsHeaders(
  headers: Headers,
  request: Request,
  env: Env,
  isPublic: boolean = false
): void {
  const origin = getRequestOrigin(request);
  const allowedOrigins = getAllowedOrigins(env);
  if (isPublic) {
    headers.set("Access-Control-Allow-Origin", "*");
  } else if (origin && allowedOrigins.has(origin)) {
    headers.set("Access-Control-Allow-Origin", origin);
  }
  headers.set("Access-Control-Allow-Methods", "GET, HEAD, OPTIONS");
  headers.set("Access-Control-Allow-Headers", "Authorization, Range, Content-Type");
  headers.set("Access-Control-Expose-Headers", "Content-Range, Content-Length, Accept-Ranges");
  headers.set("Cross-Origin-Resource-Policy", "cross-origin");
  headers.set("Vary", "Origin");
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

// Paths that are publicly accessible without a token.
// Covers and images are course thumbnails shown in the catalog to everyone.
// Videos and PDFs are gated by enrollment + play-token.
const PUBLIC_PREFIXES = ["cover/", "imagen/"];

function isPublicPath(key: string): boolean {
  return PUBLIC_PREFIXES.some((prefix) => key.startsWith(prefix));
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    // Extract the R2 key from the URL path (strip leading slash and query params)
    const url = new URL(request.url);
    const requestedKey = url.pathname.replace(/^\//, "");
    const isPublic = isPublicPath(requestedKey);

    // Handle CORS preflight (OPTIONS) — browser sends this before the real request
    if (request.method === "OPTIONS") {
      const preflight = new Headers();
      addCorsHeaders(preflight, request, env, isPublic);
      return new Response(null, { status: 204, headers: preflight });
    }

    // Public paths (covers, images) bypass origin + token checks.
    // They are shown to all users in the catalog and <img> tags don't send Origin headers.
    if (!isPublic) {
      if (!originAllowed(request, env)) {
        return new Response("Forbidden: hotlinking not allowed", { status: 403 });
      }

      // Token resolution order:
      // 1. Authorization: Bearer header (preferred — used by mediaFetch/PDF flows)
      // 2. ?token= query param (fallback — native <video> elements cannot send custom headers)
      let token: string | null = null;
      const authHeader = request.headers.get("Authorization");
      if (authHeader?.startsWith("Bearer ")) {
        token = authHeader.slice(7);
      } else {
        token = url.searchParams.get("token");
      }

      if (!token) {
        return new Response("Unauthorized: missing token", { status: 401 });
      }

      const claims = await verifyToken(token, env.MEDIA_JWT_SECRET);
      if (!claims) {
        return new Response("Unauthorized: invalid or expired token", { status: 401 });
      }

      if (requestedKey !== claims.key) {
        return new Response("Forbidden: path does not match token key", { status: 403 });
      }
    }

    // Parse Range header for partial content support (HTTP 206)
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

    // For public paths we use requestedKey directly (no claims).
    // For protected paths, claims.key was already validated to equal requestedKey above.
    const r2Key = requestedKey;
    const object = await env.R2_BUCKET.get(r2Key, r2Options);

    if (!object) {
      return new Response("Not Found", { status: 404 });
    }

    const headers = new Headers();
    object.writeHttpMetadata(headers);
    headers.set("Accept-Ranges", "bytes");
    headers.set("Cache-Control", "private, no-store");
    addCorsHeaders(headers, request, env, isPublic);

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
