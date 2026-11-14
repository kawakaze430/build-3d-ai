import { NextResponse } from "next/server";
import {
  clearSessionKey,
  productFetch,
  readSessionKey,
  storeSessionKey,
} from "@/lib/server-product-api";

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
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
  }
  try {
    const response = await productFetch("/v1/me", { method: "GET" }, key);
    if (!response.ok) {
      if (response.status === 401) await clearSessionKey();
      return NextResponse.json(
        { detail: await safeDetail(response) },
        { status: response.status },
      );
    }
    const data = (await response.json()) as { user_id?: unknown };
    if (typeof data.user_id !== "string") {
      return NextResponse.json({ detail: "Malformed product API response" }, { status: 502 });
    }
    return NextResponse.json({ authenticated: true, userId: data.user_id });
  } catch {
    return NextResponse.json({ detail: "Product API temporarily unavailable" }, { status: 503 });
  }
}

export async function POST(request: Request) {
  let apiKey: unknown;
  try {
    ({ apiKey } = (await request.json()) as { apiKey?: unknown });
  } catch {
    return NextResponse.json({ detail: "Expected JSON login body" }, { status: 400 });
  }
  if (typeof apiKey !== "string" || apiKey.length < 24 || apiKey.length > 512) {
    return NextResponse.json({ detail: "Invalid user API key format" }, { status: 422 });
  }

  try {
    const response = await productFetch("/v1/me", { method: "GET" }, apiKey);
    if (!response.ok) {
      return NextResponse.json(
        { detail: await safeDetail(response) },
        { status: response.status },
      );
    }
    const data = (await response.json()) as { user_id?: unknown };
    if (typeof data.user_id !== "string") {
      return NextResponse.json({ detail: "Malformed product API response" }, { status: 502 });
    }
    await storeSessionKey(apiKey);
    return NextResponse.json({ authenticated: true, userId: data.user_id });
  } catch {
    return NextResponse.json({ detail: "Product API temporarily unavailable" }, { status: 503 });
  }
}

export async function DELETE() {
  await clearSessionKey();
  return new Response(null, { status: 204 });
}
