import { cookies } from "next/headers";

export const SESSION_COOKIE = "build3d_user_key";

function configuredApiBase(): URL {
  const raw = process.env.BUILD3D_API_URL ?? "http://127.0.0.1:8081";
  const url = new URL(raw);
  if (!["http:", "https:"].includes(url.protocol) || url.username || url.password) {
    throw new Error("BUILD3D_API_URL must be an http(s) origin without embedded credentials");
  }
  url.pathname = "/";
  url.search = "";
  url.hash = "";
  return url;
}

export async function readSessionKey(): Promise<string | null> {
  return (await cookies()).get(SESSION_COOKIE)?.value ?? null;
}

export async function storeSessionKey(value: string): Promise<void> {
  (await cookies()).set(SESSION_COOKIE, value, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "strict",
    path: "/",
    maxAge: 8 * 60 * 60,
  });
}

export async function clearSessionKey(): Promise<void> {
  (await cookies()).delete(SESSION_COOKIE);
}

export async function productFetch(
  path: string,
  init: RequestInit = {},
  tokenOverride?: string,
): Promise<Response> {
  if (!path.startsWith("/v1/")) {
    throw new Error("Only product API v1 paths are allowed");
  }
  const token = tokenOverride ?? (await readSessionKey());
  if (!token) {
    return new Response(JSON.stringify({ detail: "A user API key is required" }), {
      status: 401,
      headers: { "content-type": "application/json" },
    });
  }

  const headers = new Headers(init.headers);
  headers.set("Authorization", `Bearer ${token}`);
  headers.set("Accept", headers.get("Accept") ?? "application/json");

  return fetch(new URL(path, configuredApiBase()), {
    ...init,
    headers,
    cache: "no-store",
    redirect: "manual",
  });
}
