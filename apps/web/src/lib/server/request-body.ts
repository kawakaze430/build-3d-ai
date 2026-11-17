export class RequestBodyTooLargeError extends Error {
  constructor() {
    super("Request exceeds configured byte limit");
    this.name = "RequestBodyTooLargeError";
  }
}

/** Bound actual streamed bytes; Content-Length is only an early-rejection hint. */
export async function readBoundedBody(request: Request, maxBytes: number): Promise<ArrayBuffer> {
  const declared = request.headers.get("content-length")?.trim();
  if (declared && /^\d+$/.test(declared) && Number(declared) > maxBytes) {
    try {
      await request.body?.cancel();
    } catch {
      // Preserve the size rejection even if the source cannot be canceled.
    }
    throw new RequestBodyTooLargeError();
  }

  if (!request.body) return new ArrayBuffer(0);
  const reader = request.body.getReader();
  const chunks: Uint8Array[] = [];
  let size = 0;
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      if (value.byteLength > maxBytes - size) {
        try {
          await reader.cancel();
        } catch {
          // A cancellation error must not replace the intended 413 response.
        }
        throw new RequestBodyTooLargeError();
      }
      chunks.push(value);
      size += value.byteLength;
    }
  } finally {
    reader.releaseLock();
  }

  const body = new Uint8Array(size);
  let offset = 0;
  for (const chunk of chunks) {
    body.set(chunk, offset);
    offset += chunk.byteLength;
  }
  return body.buffer;
}
