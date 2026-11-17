import { createServer } from "node:http";

const PORT = 8099;
const ALICE = "b3d_" + "a".repeat(43);
const BOB = "b3d_" + "b".repeat(43);
const NO_MODEL = "b3d_" + "c".repeat(43);
const NEAR_LIMIT = "b3d_" + "d".repeat(43);
const DEFAULT_STORAGE_LIMIT = 5 * 1024 * 1024 * 1024;

let projectCounter = 0;
let jobCounter = 0;
let projects = [];
let jobs = [];
let idempotency = new Map();
let storageUsed = new Map();
let aliceRevoked = false;

function reset() {
  projectCounter = 0;
  jobCounter = 0;
  projects = [];
  jobs = [];
  idempotency = new Map();
  storageUsed = new Map();
  aliceRevoked = false;
}

function ownerFor(req) {
  const token = (req.headers.authorization ?? "").replace(/^Bearer\s+/, "");
  if (token === NO_MODEL) return { id: "no-model-user", token, models: [], storageLimit: DEFAULT_STORAGE_LIMIT };
  if (token === NEAR_LIMIT) return { id: "near-limit-user", token, models: ["test_model"], storageLimit: 1000, fixedStorageUsed: 900 };
  if (token === ALICE && !aliceRevoked) return { id: "alice", token, models: ["test_model"], storageLimit: DEFAULT_STORAGE_LIMIT };
  if (token === BOB) return { id: "bob", token, models: ["test_model"], storageLimit: DEFAULT_STORAGE_LIMIT };
  return null;
}

function json(res, status, body, headers = {}) {
  const payload = Buffer.from(JSON.stringify(body));
  res.writeHead(status, {
    "content-type": "application/json",
    "content-length": String(payload.length),
    "cache-control": "no-store",
    ...headers,
  });
  res.end(payload);
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    let size = 0;
    req.on("data", (chunk) => {
      size += chunk.length;
      if (size > 14 * 1024 * 1024) {
        reject(new Error("too large"));
        req.destroy();
        return;
      }
      chunks.push(chunk);
    });
    req.on("end", () => resolve(Buffer.concat(chunks)));
    req.on("error", reject);
  });
}

function project(owner, id) {
  return projects.find((item) => item.owner === owner.id && item.id === id);
}

function publicProject(item) {
  return { id: item.id, name: item.name, created_at: item.created_at };
}

function storageFor(owner) {
  const used = owner.fixedStorageUsed ?? (storageUsed.get(owner.id) ?? 0);
  const limit = owner.storageLimit ?? DEFAULT_STORAGE_LIMIT;
  return {
    used_bytes: used,
    limit_bytes: limit,
    remaining_bytes: Math.max(0, limit - used),
    over_quota: used > limit,
  };
}

function publicJob(item) {
  return {
    id: item.id,
    project_id: item.project_id,
    kind: item.kind,
    status: item.status,
    model_id: item.model_id,
    model_approval: { model_id: item.model_id, fixture: true },
    prompt: item.prompt,
    input_sha256: item.kind === "image" ? "fixture-image-sha" : null,
    error_code: item.error_code ?? null,
    created_at: item.created_at,
    updated_at: item.updated_at,
    started_at: item.started_at ?? null,
  };
}

function triangleGlb() {
  const positions = Buffer.alloc(36);
  const values = [0, 0, 0, 1, 0, 0, 0, 1, 0];
  values.forEach((value, index) => positions.writeFloatLE(value, index * 4));
  const indices = Buffer.alloc(8);
  indices.writeUInt16LE(0, 0);
  indices.writeUInt16LE(1, 2);
  indices.writeUInt16LE(2, 4);
  const bin = Buffer.concat([positions, indices]);
  const document = {
    asset: { version: "2.0", generator: "Build3D synthetic browser fixture" },
    buffers: [{ byteLength: 42 }],
    bufferViews: [
      { buffer: 0, byteOffset: 0, byteLength: 36, target: 34962 },
      { buffer: 0, byteOffset: 36, byteLength: 6, target: 34963 },
    ],
    accessors: [
      {
        bufferView: 0,
        componentType: 5126,
        count: 3,
        type: "VEC3",
        min: [0, 0, 0],
        max: [1, 1, 0],
      },
      { bufferView: 1, componentType: 5123, count: 3, type: "SCALAR" },
    ],
    meshes: [{ primitives: [{ attributes: { POSITION: 0 }, indices: 1 }] }],
    nodes: [{ mesh: 0 }],
    scenes: [{ nodes: [0] }],
    scene: 0,
  };
  let jsonChunk = Buffer.from(JSON.stringify(document));
  const jsonPad = (4 - (jsonChunk.length % 4)) % 4;
  if (jsonPad) jsonChunk = Buffer.concat([jsonChunk, Buffer.alloc(jsonPad, 0x20)]);
  const total = 12 + 8 + jsonChunk.length + 8 + bin.length;
  const header = Buffer.alloc(12);
  header.write("glTF", 0);
  header.writeUInt32LE(2, 4);
  header.writeUInt32LE(total, 8);
  const jsonHeader = Buffer.alloc(8);
  jsonHeader.writeUInt32LE(jsonChunk.length, 0);
  jsonHeader.write("JSON", 4);
  const binHeader = Buffer.alloc(8);
  binHeader.writeUInt32LE(bin.length, 0);
  binHeader.write("BIN\0", 4);
  return Buffer.concat([header, jsonHeader, jsonChunk, binHeader, bin]);
}

const fixtureGlb = triangleGlb();

const server = createServer(async (req, res) => {
  const url = new URL(req.url ?? "/", `http://127.0.0.1:${PORT}`);
  if (url.pathname === "/health") return json(res, 200, { status: "ok" });
  if (url.pathname === "/__reset" && req.method === "POST") {
    reset();
    return json(res, 200, { reset: true });
  }
  if (url.pathname === "/__revoke_alice" && req.method === "POST") {
    aliceRevoked = true;
    return json(res, 200, { revoked: true });
  }

  const owner = ownerFor(req);
  if (!owner) return json(res, 401, { detail: "Invalid API key" });

  if (url.pathname === "/v1/me" && req.method === "GET") {
    return json(res, 200, { user_id: owner.id });
  }
  if (url.pathname === "/v1/models" && req.method === "GET") {
    return json(res, 200, { approved_model_ids: owner.models });
  }
  if (url.pathname === "/v1/storage" && req.method === "GET") {
    return json(res, 200, storageFor(owner));
  }
  if (url.pathname === "/v1/projects" && req.method === "GET") {
    return json(res, 200, {
      items: projects.filter((item) => item.owner === owner.id).map(publicProject),
      limit: 100,
      offset: 0,
    });
  }
  if (url.pathname === "/v1/projects" && req.method === "POST") {
    const raw = await readBody(req);
    const body = JSON.parse(raw.toString("utf8"));
    const item = {
      id: `project_${++projectCounter}`,
      owner: owner.id,
      name: body.name,
      created_at: Date.now() / 1000,
    };
    projects.unshift(item);
    return json(res, 201, publicProject(item));
  }

  let match = url.pathname.match(/^\/v1\/projects\/([A-Za-z0-9_-]+)$/);
  if (match && req.method === "GET") {
    const item = project(owner, match[1]);
    return item ? json(res, 200, publicProject(item)) : json(res, 404, { detail: "Project not found" });
  }

  match = url.pathname.match(/^\/v1\/projects\/([A-Za-z0-9_-]+)\/jobs$/);
  if (match && req.method === "GET") {
    if (!project(owner, match[1])) return json(res, 404, { detail: "Project not found" });
    return json(res, 200, {
      items: jobs
        .filter((item) => item.owner === owner.id && item.project_id === match[1])
        .map(publicJob),
      limit: 100,
      offset: 0,
    });
  }

  match = url.pathname.match(/^\/v1\/projects\/([A-Za-z0-9_-]+)\/jobs\/(text|image)$/);
  if (match && req.method === "POST") {
    if (!project(owner, match[1])) return json(res, 404, { detail: "Project not found" });
    if (owner.models.length === 0) return json(res, 503, { detail: "Generation disabled: no approved model is configured" });

    const key = req.headers["idempotency-key"];
    if (typeof key !== "string") return json(res, 422, { detail: "Idempotency-Key required" });
    const raw = await readBody(req);
    const fingerprint = `${url.pathname}:${raw.toString("base64")}`;
    const existing = idempotency.get(`${owner.id}:${key}`);
    if (existing) {
      if (existing.fingerprint !== fingerprint) {
        return json(res, 409, { detail: "Idempotency-Key was already used for a different request" });
      }
      return json(res, 200, publicJob(existing.job));
    }

    let prompt = null;
    let modelId = "test_model";
    if (match[2] === "text") {
      const body = JSON.parse(raw.toString("utf8"));
      prompt = body.prompt;
      modelId = body.model_id;
      if (prompt === "rate limit") {
        return json(res, 429, { detail: "API request limit reached; retry in 60 seconds" }, { "retry-after": "60" });
      }
    }
    const now = Date.now() / 1000;
    const item = {
      id: `job_${++jobCounter}`,
      owner: owner.id,
      project_id: match[1],
      kind: match[2],
      status: prompt === "complete fixture" ? "completed" : "queued",
      model_id: modelId,
      prompt,
      created_at: now,
      updated_at: now,
      started_at: prompt === "complete fixture" ? now : null,
    };
    jobs.unshift(item);
    if (item.status === "completed") {
      storageUsed.set(owner.id, (storageUsed.get(owner.id) ?? 0) + fixtureGlb.length);
    }
    idempotency.set(`${owner.id}:${key}`, { fingerprint, job: item });
    return json(res, 202, publicJob(item), { location: `/v1/jobs/${item.id}` });
  }

  match = url.pathname.match(/^\/v1\/jobs\/([A-Za-z0-9_-]+)$/);
  if (match && req.method === "GET") {
    const item = jobs.find((job) => job.owner === owner.id && job.id === match[1]);
    return item ? json(res, 200, publicJob(item)) : json(res, 404, { detail: "Job not found" });
  }

  match = url.pathname.match(/^\/v1\/jobs\/([A-Za-z0-9_-]+)\/cancel$/);
  if (match && req.method === "POST") {
    const item = jobs.find((job) => job.owner === owner.id && job.id === match[1]);
    if (!item) return json(res, 404, { detail: "Job not found" });
    if (item.status !== "queued") return json(res, 409, { detail: "Only queued jobs can be canceled" });
    item.status = "canceled";
    item.updated_at = Date.now() / 1000;
    return json(res, 200, publicJob(item));
  }

  match = url.pathname.match(/^\/v1\/jobs\/([A-Za-z0-9_-]+)\/artifact$/);
  if (match && req.method === "GET") {
    const item = jobs.find((job) => job.owner === owner.id && job.id === match[1]);
    if (!item) return json(res, 404, { detail: "Job not found" });
    if (item.status !== "completed") return json(res, 409, { detail: "No verified artifact is available for this job" });
    return json(res, 200, {
      id: `artifact_${item.id}`,
      job_id: item.id,
      sha256: "synthetic-fixture",
      size_bytes: fixtureGlb.length,
      mesh_count: 1,
      created_at: item.updated_at,
    });
  }

  match = url.pathname.match(/^\/v1\/jobs\/([A-Za-z0-9_-]+)\/download$/);
  if (match && req.method === "GET") {
    const item = jobs.find((job) => job.owner === owner.id && job.id === match[1]);
    if (!item) return json(res, 404, { detail: "Job not found" });
    if (item.status !== "completed") return json(res, 409, { detail: "No verified artifact is available for this job" });
    res.writeHead(200, {
      "content-type": "model/gltf-binary",
      "content-length": String(fixtureGlb.length),
      "content-disposition": `attachment; filename="${item.id}.glb"`,
      "x-artifact-sha256": "synthetic-fixture",
    });
    return res.end(fixtureGlb);
  }

  return json(res, 404, { detail: "Not found" });
});

server.listen(PORT, "127.0.0.1", () => {
  console.log(`Synthetic product API fixture listening on ${PORT}`);
});
