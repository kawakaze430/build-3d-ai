import {
  JOB_STATUSES,
  type Job,
  type JobStatus,
  type Project,
  type SessionInfo,
  type StorageUsage,
} from "@/lib/contracts";

export class ApiClientError extends Error {
  constructor(
    public readonly status: number,
    message: string,
    public readonly retryAfter?: string,
  ) {
    super(message);
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isStatus(value: unknown): value is JobStatus {
  return typeof value === "string" && (JOB_STATUSES as readonly string[]).includes(value);
}

function parseProject(value: unknown): Project {
  if (
    !isRecord(value) ||
    typeof value.id !== "string" ||
    typeof value.name !== "string" ||
    typeof value.created_at !== "number"
  ) {
    throw new ApiClientError(502, "Backend returned malformed project data");
  }
  return { id: value.id, name: value.name, created_at: value.created_at };
}

function parseJob(value: unknown): Job {
  if (
    !isRecord(value) ||
    typeof value.id !== "string" ||
    typeof value.project_id !== "string" ||
    (value.kind !== "text" && value.kind !== "image") ||
    !isStatus(value.status) ||
    typeof value.model_id !== "string" ||
    typeof value.created_at !== "number" ||
    typeof value.updated_at !== "number"
  ) {
    throw new ApiClientError(502, "Backend returned malformed job data");
  }
  return {
    id: value.id,
    project_id: value.project_id,
    kind: value.kind,
    status: value.status,
    model_id: value.model_id,
    model_approval: isRecord(value.model_approval) ? value.model_approval : undefined,
    prompt: typeof value.prompt === "string" ? value.prompt : null,
    input_sha256: typeof value.input_sha256 === "string" ? value.input_sha256 : null,
    error_code: typeof value.error_code === "string" ? value.error_code : null,
    created_at: value.created_at,
    updated_at: value.updated_at,
    started_at: typeof value.started_at === "number" ? value.started_at : null,
  };
}

async function detailFor(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: unknown };
    if (typeof body.detail === "string") return body.detail;
  } catch {
    // Use status fallback below.
  }
  return `Request failed with HTTP ${response.status}`;
}

async function requestJson(path: string, init: RequestInit = {}): Promise<unknown> {
  let response: Response;
  try {
    response = await fetch(path, { ...init, cache: "no-store" });
  } catch {
    init.signal?.throwIfAborted();
    throw new ApiClientError(503, "Web gateway is unavailable");
  }
  if (!response.ok) {
    const detail = await detailFor(response);
    init.signal?.throwIfAborted();
    throw new ApiClientError(
      response.status,
      detail,
      response.headers.get("retry-after") ?? undefined,
    );
  }
  try {
    const value: unknown = await response.json();
    init.signal?.throwIfAborted();
    return value;
  } catch {
    init.signal?.throwIfAborted();
    throw new ApiClientError(502, "Backend returned malformed JSON");
  }
}

export function apiErrorMessage(error: unknown): string {
  if (!(error instanceof ApiClientError)) return "Unexpected application error";
  if (error.status === 401) return "Your session is missing or the user API key was rejected.";
  if (error.status === 404) return "The resource was not found, or it belongs to another user.";
  if (error.status === 409) return `The request conflicts with the current resource state: ${error.message}`;
  if (error.status === 413) return "The uploaded request is too large.";
  if (error.status === 429) {
    return `Rate or active-job limit reached.${error.retryAfter ? ` Retry after ${error.retryAfter} seconds.` : ""}`;
  }
  if (error.status >= 500) return `Service temporarily unavailable: ${error.message}`;
  return error.message;
}

export async function getSession(signal?: AbortSignal): Promise<SessionInfo> {
  const value = await requestJson("/api/session", { signal });
  if (!isRecord(value) || value.authenticated !== true || typeof value.userId !== "string") {
    throw new ApiClientError(502, "Malformed session response");
  }
  return { authenticated: true, userId: value.userId };
}

export async function login(apiKey: string, signal?: AbortSignal): Promise<SessionInfo> {
  const value = await requestJson("/api/session", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ apiKey }),
    signal,
  });
  if (!isRecord(value) || value.authenticated !== true || typeof value.userId !== "string") {
    throw new ApiClientError(502, "Malformed session response");
  }
  return { authenticated: true, userId: value.userId };
}

export async function logout(signal?: AbortSignal): Promise<void> {
  const response = await fetch("/api/session", {
    method: "DELETE",
    cache: "no-store",
    redirect: "error",
    signal,
  });
  if (response.status !== 204) {
    throw new ApiClientError(response.status, "Could not clear session");
  }
}

export async function listModels(signal?: AbortSignal): Promise<string[]> {
  const value = await requestJson("/api/product/v1/models", { signal });
  if (!isRecord(value) || !Array.isArray(value.approved_model_ids) || !value.approved_model_ids.every((x) => typeof x === "string")) {
    throw new ApiClientError(502, "Backend returned malformed model data");
  }
  return [...value.approved_model_ids];
}

export async function getStorageUsage(signal?: AbortSignal): Promise<StorageUsage> {
  const value = await requestJson("/api/product/v1/storage", { signal });
  if (
    !isRecord(value) ||
    !Number.isSafeInteger(value.used_bytes) ||
    !Number.isSafeInteger(value.limit_bytes) ||
    !Number.isSafeInteger(value.remaining_bytes) ||
    typeof value.over_quota !== "boolean" ||
    (value.used_bytes as number) < 0 ||
    (value.limit_bytes as number) < 0 ||
    (value.remaining_bytes as number) < 0
  ) {
    throw new ApiClientError(502, "Backend returned malformed storage usage");
  }
  const used = value.used_bytes as number;
  const limit = value.limit_bytes as number;
  const remaining = value.remaining_bytes as number;
  const overQuota = value.over_quota as boolean;
  if (remaining !== Math.max(0, limit - used) || overQuota !== (used > limit)) {
    throw new ApiClientError(502, "Backend returned inconsistent storage usage");
  }
  return {
    used_bytes: used,
    limit_bytes: limit,
    remaining_bytes: remaining,
    over_quota: overQuota,
  };
}

export async function listProjects(signal?: AbortSignal): Promise<Project[]> {
  const value = await requestJson("/api/product/v1/projects?limit=100&offset=0", { signal });
  if (!isRecord(value) || !Array.isArray(value.items)) {
    throw new ApiClientError(502, "Backend returned malformed project list");
  }
  return value.items.map(parseProject);
}

export async function createProject(name: string, signal?: AbortSignal): Promise<Project> {
  return parseProject(await requestJson("/api/product/v1/projects", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
    signal,
  }));
}

export async function listJobs(projectId: string, signal?: AbortSignal): Promise<Job[]> {
  const value = await requestJson(
    `/api/product/v1/projects/${encodeURIComponent(projectId)}/jobs?limit=100&offset=0`,
    { signal },
  );
  if (!isRecord(value) || !Array.isArray(value.items)) {
    throw new ApiClientError(502, "Backend returned malformed job list");
  }
  return value.items.map(parseJob);
}

export async function submitTextJob(
  projectId: string,
  prompt: string,
  modelId: string,
  signal?: AbortSignal,
): Promise<Job> {
  return parseJob(await requestJson(
    `/api/product/v1/projects/${encodeURIComponent(projectId)}/jobs/text`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Idempotency-Key": crypto.randomUUID(),
      },
      body: JSON.stringify({ prompt, model_id: modelId }),
      signal,
    },
  ));
}

export async function submitImageJob(
  projectId: string,
  file: File,
  modelId: string,
  signal?: AbortSignal,
): Promise<Job> {
  const form = new FormData();
  form.set("model_id", modelId);
  form.set("file", file);
  return parseJob(await requestJson(
    `/api/product/v1/projects/${encodeURIComponent(projectId)}/jobs/image`,
    {
      method: "POST",
      headers: { "Idempotency-Key": crypto.randomUUID() },
      body: form,
      signal,
    },
  ));
}

export function artifactDownloadUrl(jobId: string): string {
  return `/api/product/v1/jobs/${encodeURIComponent(jobId)}/download`;
}
