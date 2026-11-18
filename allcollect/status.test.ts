import { describe, expect, it } from "vitest";
import { isPollable, jobStatusDescription, needsOperatorAttention } from "./status";

describe("job status semantics", () => {
  it("only polls states that are safe to read automatically", () => {
    expect(isPollable("queued")).toBe(true);
    expect(isPollable("dispatching")).toBe(true);
    expect(isPollable("running")).toBe(true);
    expect(isPollable("submission_unknown")).toBe(false);
    expect(isPollable("polling_paused")).toBe(false);
    expect(isPollable("timed_out")).toBe(false);
  });

  it("preserves uncertain states instead of flattening them into failed", () => {
    expect(needsOperatorAttention("submission_unknown")).toBe(true);
    expect(needsOperatorAttention("polling_paused")).toBe(true);
    expect(needsOperatorAttention("timed_out")).toBe(true);
    expect(jobStatusDescription("submission_unknown")).toContain("must not be automatically retried");
  });
});
