import { NextResponse } from "next/server";
import { readBoundedBody, RequestBodyTooLargeError } from "@/lib/server/request-body";
import {
  clearSessionKey,
  productFetch,
  readSessionKey,
  storeSessionKey,
} from "@/lib/server/product-api";

const MAX_SESSION_BODY = 8 * 1024;
const SESSION_HEADERS = { "Cache-Control": "no-store" };

function sessionJson(body: Record<string, unknown>, status = 200) {
  return NextResponse.json(body, { status, headers: SESSION_HEADERS });
}

async function safeDetail(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: unknown };
    if (typeof body.detail === "string" && body.detail.length <= 300) return body.detail;
  } catch {
    // Fall through to a generic message.
  }
  return response.status >= 500
    ? "Product API temporarily unavailable"
    : "Authentication failed";
}

export async function GET() {
  const key = await readSessionKey();
  if (!key) {
    return sessionJson({ detail: "Not authenticated" }, 401);
  }
  try {
    const response = await productFetch("/v1/me", { method: "GET" }, key);
    if (!response.ok) {
      if (response.status === 401) await clearSessionKey();
      return sessionJson({ detail: await safeDetail(response) }, response.status);
    }
    const data = (await response.json()) as { user_id?: unknown };
    if (typeof data.user_id !== "string") {
      return sessionJson({ detail: "Malformed product API response" }, 502);
    }
    return sessionJson({ authenticated: true, userId: data.user_id });
  } catch {
    return sessionJson({ detail: "Product API temporarily unavailable" }, 503);
  }
}

export async function POST(request: Request) {
  let apiKey: unknown;
  try {
    const body = await readBoundedBody(request, MAX_SESSION_BODY);
    ({ apiKey } = JSON.parse(new TextDecoder().decode(body)) as { apiKey?: unknown });
  } catch (error) {
    if (error instanceof RequestBodyTooLargeError) {
      return sessionJson({ detail: "Login request exceeds web gateway limit" }, 413);
    }
    return sessionJson({ detail: "Expected JSON login body" }, 400);
  }
  if (typeof apiKey !== "string" || apiKey.length < 24 || apiKey.length > 512) {
    return sessionJson({ detail: "Invalid user API key format" }, 422);
  }

  try {
    const response = await productFetch("/v1/me", { method: "GET" }, apiKey);
    if (!response.ok) {
      return sessionJson({ detail: await safeDetail(response) }, response.status);
    }
    const data = (await response.json()) as { user_id?: unknown };
    if (typeof data.user_id !== "string") {
      return sessionJson({ detail: "Malformed product API response" }, 502);
    }
    await storeSessionKey(apiKey);
    return sessionJson({ authenticated: true, userId: data.user_id });
  } catch {
    return sessionJson({ detail: "Product API temporarily unavailable" }, 503);
  }
}

export async function DELETE() {
  await clearSessionKey();
  return new Response(null, { status: 204, headers: SESSION_HEADERS });
}
