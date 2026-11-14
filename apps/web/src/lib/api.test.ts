import { describe, expect, it } from "vitest";
import { ApiClientError, apiErrorMessage } from "./api";

describe("API error presentation", () => {
  it("distinguishes ownership-safe 404 and idempotency/artifact 409 responses", () => {
    expect(apiErrorMessage(new ApiClientError(404, "Project not found"))).toContain("another user");
    expect(apiErrorMessage(new ApiClientError(409, "No verified artifact"))).toContain("current resource state");
  });

  it("surfaces limits without exposing raw backend internals", () => {
    expect(apiErrorMessage(new ApiClientError(413, "too large"))).toContain("too large");
    expect(apiErrorMessage(new ApiClientError(429, "limit", "60"))).toContain("60 seconds");
    expect(apiErrorMessage(new ApiClientError(503, "Database temporarily unavailable"))).toContain("temporarily unavailable");
  });
});
