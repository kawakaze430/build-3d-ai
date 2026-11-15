export const JOB_STATUSES = [
  "queued",
  "dispatching",
  "running",
  "completed",
  "failed",
  "canceled",
  "submission_unknown",
  "polling_paused",
  "timed_out",
] as const;

export type JobStatus = (typeof JOB_STATUSES)[number];

export interface SessionInfo {
  authenticated: true;
  userId: string;
}

export interface Project {
  id: string;
  name: string;
  created_at: number;
}

export interface Job {
  id: string;
  project_id: string;
  kind: "text" | "image";
  status: JobStatus;
  model_id: string;
  model_approval?: Record<string, unknown>;
  prompt: string | null;
  input_sha256: string | null;
  error_code: string | null;
  created_at: number;
  updated_at: number;
  started_at: number | null;
}

export interface Artifact {
  id: string;
  job_id: string;
  sha256: string;
  size_bytes: number;
  mesh_count: number;
  created_at: number;
}

export interface StorageUsage {
  used_bytes: number;
  limit_bytes: number;
  remaining_bytes: number;
  over_quota: boolean;
}
