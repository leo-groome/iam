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

    const r2Key = requestedKey;
    const objectHead = await env.R2_BUCKET.head(r2Key);

    if (!objectHead) {
      return new Response("Not Found", { status: 404 });
    }

    // Parse Range header for partial content support (HTTP 206)
    const rangeHeader = request.headers.get("Range");
    const r2Options: R2GetOptions = {};
    let isRangeSatisfiable = true;
    let start = 0;
    let end = objectHead.size - 1;

    if (rangeHeader) {
      const match = /bytes=(\d+)-(\d*)/.exec(rangeHeader);
      if (match) {
        start = parseInt(match[1], 10);
        const endVal = match[2] ? parseInt(match[2], 10) : undefined;
        
        if (start >= objectHead.size) {
          isRangeSatisfiable = false;
        } else {
          end = endVal !== undefined ? Math.min(endVal, objectHead.size - 1) : objectHead.size - 1;
          r2Options.range = { offset: start, length: end - start + 1 };
        }
      }
    }

    const headers = new Headers();
    objectHead.writeHttpMetadata(headers);
    headers.set("Accept-Ranges", "bytes");
    headers.set("Cache-Control", "private, no-store");
    addCorsHeaders(headers, request, env, isPublic);

    if (!isRangeSatisfiable) {
      headers.set("Content-Range", `bytes */${objectHead.size}`);
      return new Response("Range Not Satisfiable", { status: 416, headers });
    }

    // Handle HEAD request
    if (request.method === "HEAD") {
      if (rangeHeader) {
        headers.set("Content-Range", `bytes ${start}-${end}/${objectHead.size}`);
        headers.set("Content-Length", String(end - start + 1));
        return new Response(null, { status: 206, headers });
      }
      headers.set("Content-Length", String(objectHead.size));
      return new Response(null, { status: 200, headers });
    }

    // Fetch the object body from R2
    const object = await env.R2_BUCKET.get(r2Key, r2Options);
    if (!object) {
      return new Response("Not Found", { status: 404 });
    }

    if (rangeHeader) {
      headers.set("Content-Range", `bytes ${start}-${end}/${objectHead.size}`);
      headers.set("Content-Length", String(end - start + 1));
      return new Response(object.body, { status: 206, headers });
    }

    headers.set("Content-Length", String(objectHead.size));
    return new Response(object.body, { status: 200, headers });
  },
};
