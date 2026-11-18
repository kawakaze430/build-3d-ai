import { afterEach, describe, expect, it, vi } from "vitest";
import { HISTORY_PAGE_SIZE, JOB_STATUSES } from "@/lib/contracts";
import { ApiClientError, apiErrorMessage, getStorageUsage, listJobs } from "./api";

afterEach(() => vi.unstubAllGlobals());

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

describe("API response contracts", () => {
  const job = {
    id: "job", project_id: "project", kind: "text", model_id: "example",
    model_approval: { model_id: "example" },
    prompt: "chair", input_sha256: null, error_code: null,
    created_at: 1, updated_at: 2, started_at: null,
  };

  it("retains every documented job status and only the public fields", async () => {
    const fixtures = JOB_STATUSES.map((status) => ({ ...job, status, lease_token: "internal" }));
    vi.stubGlobal("fetch", async () => Response.json({
      items: fixtures, limit: HISTORY_PAGE_SIZE, offset: 0,
    }));
    await expect(listJobs("project", 0)).resolves.toEqual({
      items: JOB_STATUSES.map((status) => ({ ...job, status })), offset: 0,
    });
  });

  it("rejects an unsupported status instead of treating the job as completed", async () => {
    vi.stubGlobal("fetch", async () => Response.json({
      items: [{ ...job, status: "unexpected" }], limit: HISTORY_PAGE_SIZE, offset: 0,
    }));
    await expect(listJobs("project", 0)).rejects.toThrow("malformed job data");
  });

  it("rejects malformed storage usage", async () => {
    vi.stubGlobal("fetch", async () => Response.json({
      used_bytes: "0", limit_bytes: 10, remaining_bytes: 10, over_quota: false,
    }));
    await expect(getStorageUsage()).rejects.toMatchObject({ status: 502 });
  });
});
