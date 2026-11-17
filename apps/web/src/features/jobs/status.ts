import type { JobStatus } from "@/lib/contracts";

const POLLABLE = new Set<JobStatus>(["queued", "dispatching", "running"]);
const ATTENTION = new Set<JobStatus>(["submission_unknown", "polling_paused", "timed_out"]);

export function isPollable(status: JobStatus): boolean {
  return POLLABLE.has(status);
}

export function needsOperatorAttention(status: JobStatus): boolean {
  return ATTENTION.has(status);
}

export function jobStatusLabel(status: JobStatus): string {
  return status.replaceAll("_", " ");
}

export function jobStatusDescription(status: JobStatus): string {
  switch (status) {
    case "queued":
      return "Accepted by the durable API and waiting for a worker.";
    case "dispatching":
      return "A worker has claimed the job and may be submitting it upstream.";
    case "running":
      return "An upstream job ID is recorded and completion is being polled.";
    case "completed":
      return "A verified GLB artifact is available.";
    case "failed":
      return "The job reached a known failure state. Review its error code before retrying.";
    case "canceled":
      return "Canceled before upstream submission.";
    case "submission_unknown":
      return "The submission outcome is uncertain. It must not be automatically retried; operator reconciliation may be required.";
    case "polling_paused":
      return "Repeated upstream reads failed. The quota slot is retained until the operator investigates and reconciles the job.";
    case "timed_out":
      return "Completion was not observed before the timeout. Remote compute may still exist, so operator reconciliation is required.";
  }
}

export function statusTone(status: JobStatus): "good" | "warn" | "bad" | "neutral" {
  if (status === "completed") return "good";
  if (ATTENTION.has(status)) return "warn";
  if (status === "failed") return "bad";
  return "neutral";
}
