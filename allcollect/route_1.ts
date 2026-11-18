import { clearSessionKey, productFetch, readSessionKey } from "@/lib/server-product-api";
import { readBoundedBody, RequestBodyTooLargeError } from "@/lib/request-body";

type RouteContext = { params: Promise<{ segments: string[] }> };

const SAFE_ID = /^[A-Za-z0-9_-]{1,128}$/;
const MAX_PROXY_BODY = 12 * 1024 * 1024;

function allowed(segments: string[], method: string): boolean {
  if (segments[0] !== "v1") return false;
  if (
    segments.length === 2 &&
    ["models", "storage"].includes(segments[1])
  ) return method === "GET";
  if (segments.length === 2 && segments[1] === "projects") {
    return method === "GET" || method === "POST";
  }
  if (segments.length === 3 && segments[1] === "projects" && SAFE_ID.test(segments[2])) {
    return method === "GET";
  }
  if (
    segments.length === 4 &&
    segments[1] === "projects" &&
    SAFE_ID.test(segments[2]) &&
    segments[3] === "jobs"
  ) {
    return method === "GET";
  }
  if (
    segments.length === 5 &&
    segments[1] === "projects" &&
    SAFE_ID.test(segments[2]) &&
    segments[3] === "jobs" &&
    ["text", "image"].includes(segments[4])
  ) {
    return method === "POST";
  }
  if (segments.length === 3 && segments[1] === "jobs" && SAFE_ID.test(segments[2])) {
    return method === "GET";
  }
  if (
    segments.length === 4 &&
    segments[1] === "jobs" &&
    SAFE_ID.test(segments[2]) &&
    ["cancel", "artifact"].includes(segments[3])
  ) {
    return segments[3] === "cancel" ? method === "POST" : method === "GET";
  }
  return (
    segments.length === 4 &&
    segments[1] === "jobs" &&
    SAFE_ID.test(segments[2]) &&
    segments[3] === "download" &&
    method === "GET"
  );
}

function safeQuery(request: Request): string | null {
  const source = new URL(request.url).searchParams;
  for (const key of source.keys()) {
    if (key !== "limit" && key !== "offset") return null;
  }
  const target = new URLSearchParams();
  for (const key of ["limit", "offset"]) {
    const value = source.get(key);
    if (value !== null) {
      if (!/^\d{1,6}$/.test(value)) return null;
      target.set(key, value);
    }
  }
  const rendered = target.toString();
  return rendered ? `?${rendered}` : "";
}

async function proxy(request: Request, context: RouteContext) {
  const { segments } = await context.params;
  if (!allowed(segments, request.method)) {
    return Response.json({ detail: "Route not exposed by web gateway" }, { status: 404 });
  }

  const token = await readSessionKey();
  if (!token) {
    return Response.json({ detail: "Not authenticated" }, { status: 401 });
  }

  const query = safeQuery(request);
  if (query === null) {
    return Response.json({ detail: "Unsupported query parameter" }, { status: 400 });
  }

  const headers = new Headers();
  const contentType = request.headers.get("content-type");
  const idempotency = request.headers.get("idempotency-key");
  if (contentType) headers.set("Content-Type", contentType);
  if (idempotency) headers.set("Idempotency-Key", idempotency);

  let body: ArrayBuffer | undefined;
  if (request.method === "POST") {
    try {
      body = await readBoundedBody(request, MAX_PROXY_BODY);
    } catch (error) {
      if (error instanceof RequestBodyTooLargeError) {
        return Response.json({ detail: "Request exceeds web gateway limit" }, { status: 413 });
      }
      throw error;
    }
  }

  const path = "/" + segments.map(encodeURIComponent).join("/") + query;
  let upstream: Response;
  try {
    upstream = await productFetch(
      path,
      { method: request.method, headers, body },
      token,
    );
  } catch {
    return Response.json({ detail: "Product API temporarily unavailable" }, { status: 503 });
  }

  if (upstream.status === 401) await clearSessionKey();

  const responseHeaders = new Headers({ "Cache-Control": "no-store" });
  for (const name of [
    "content-type",
    "content-disposition",
    "location",
    "retry-after",
    "x-artifact-sha256",
  ]) {
    const value = upstream.headers.get(name);
    if (value) responseHeaders.set(name, value);
  }
  return new Response(upstream.body, {
    status: upstream.status,
    headers: responseHeaders,
  });
}

export async function GET(request: Request, context: RouteContext) {
  return proxy(request, context);
}

export async function POST(request: Request, context: RouteContext) {
  return proxy(request, context);
}
