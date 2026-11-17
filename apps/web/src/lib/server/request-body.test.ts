import { describe, expect, it, vi } from "vitest";
import { readBoundedBody, RequestBodyTooLargeError } from "./request-body";

function streamedRequest(
  chunks: string[],
  options: { length?: string; close?: boolean; cancel?: () => void } = {},
): Request {
  const encoder = new TextEncoder();
  const stream = new ReadableStream<Uint8Array>({
    start(controller) {
      for (const chunk of chunks) controller.enqueue(encoder.encode(chunk));
      if (options.close !== false) controller.close();
    },
    cancel: options.cancel,
  });
  const init: RequestInit & { duplex: "half" } = {
    method: "POST",
    body: stream,
    duplex: "half",
    headers: options.length === undefined ? {} : { "Content-Length": options.length },
  };
  return new Request("http://example.test/body", init);
}

describe("bounded request-body reads", () => {
  it("retains valid chunked bytes at the limit without requiring Content-Length", async () => {
    const body = await readBoundedBody(streamedRequest(["abc", "def"]), 6);
    expect(new TextDecoder().decode(body)).toBe("abcdef");
  });

  it("rejects an overflowing chunked body without Content-Length and cancels the source", async () => {
    const cancel = vi.fn();
    await expect(readBoundedBody(
      streamedRequest(["abc", "def"], { close: false, cancel }), 5,
    )).rejects.toBeInstanceOf(RequestBodyTooLargeError);
    expect(cancel).toHaveBeenCalledOnce();
  });

  it("does not trust an understated Content-Length", async () => {
    const cancel = vi.fn();
    await expect(readBoundedBody(
      streamedRequest(["abc", "def"], { length: "1", close: false, cancel }), 5,
    )).rejects.toBeInstanceOf(RequestBodyTooLargeError);
    expect(cancel).toHaveBeenCalledOnce();
  });

  it.each(["not-a-number", "-1", "2.5"])(
    "still enforces streamed bytes with malformed Content-Length %s",
    async (length) => {
      await expect(readBoundedBody(
        streamedRequest(["abcdef"], { length }), 5,
      )).rejects.toBeInstanceOf(RequestBodyTooLargeError);
    },
  );

  it("accepts bounded content despite a malformed length hint", async () => {
    const body = await readBoundedBody(streamedRequest(["abc"], { length: "unknown" }), 5);
    expect(new TextDecoder().decode(body)).toBe("abc");
  });

  it("rejects a declared oversize request early and cancels its source", async () => {
    const cancel = vi.fn();
    await expect(readBoundedBody(
      streamedRequest(["abc"], { length: "100", close: false, cancel }), 5,
    )).rejects.toBeInstanceOf(RequestBodyTooLargeError);
    expect(cancel).toHaveBeenCalledOnce();
  });

  it("propagates input read failures rather than presenting them as size rejections", async () => {
    const failure = new Error("input stream failed");
    const init: RequestInit & { duplex: "half" } = {
      method: "POST",
      duplex: "half",
      body: new ReadableStream({ start(controller) { controller.error(failure); } }),
    };
    const request = new Request("http://example.test/body", init);
    await expect(readBoundedBody(request, 5)).rejects.toBe(failure);
  });

  it("keeps the size rejection when cancellation fails", async () => {
    const request = streamedRequest(["abcdef"], {
      close: false,
      cancel() { throw new Error("cancel failed"); },
    });
    await expect(readBoundedBody(request, 5)).rejects.toBeInstanceOf(RequestBodyTooLargeError);
  });
});
