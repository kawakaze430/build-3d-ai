import { expect, test } from "@playwright/test";

const ALICE = "b3d_" + "a".repeat(43);
const BOB = "b3d_" + "b".repeat(43);
const NO_MODEL = "b3d_" + "c".repeat(43);

async function login(page: any, key = ALICE) {
  await page.goto("/");
  await page.getByLabel("User API key").fill(key);
  await page.getByRole("button", { name: "Connect to product API" }).click();
  await expect(page.getByRole("heading", { name: "Projects" })).toBeVisible();
}

async function createProject(page: any, name: string) {
  await page.getByLabel("New project").fill(name);
  await page.getByRole("button", { name: "Add" }).click();
  await expect(page.getByRole("button", { name: new RegExp(name) })).toBeVisible();
}

test.beforeEach(async ({ request }) => {
  await request.post("http://127.0.0.1:8099/__reset");
});

test("authenticates, creates a project, and submits text and image jobs", async ({ page }) => {
  await login(page);
  await createProject(page, "Film assets");

  await page.getByLabel("Prompt").fill("stylized chair");
  await page.getByRole("button", { name: "Generate 3D" }).click();
  await expect(page.getByText("queued", { exact: true }).first()).toBeVisible();

  await page.getByRole("tab", { name: "Image → 3D" }).click();
  await page.getByLabel("Reference image").setInputFiles({
    name: "reference.png",
    mimeType: "image/png",
    buffer: Buffer.from(
      "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Y9ZQmcAAAAASUVORK5CYII=",
      "base64",
    ),
  });
  await page.getByRole("button", { name: "Generate from image" }).click();
  await expect(page.getByText("Image reference").first()).toBeVisible();
});

test("shows a deliberate no-approved-model state", async ({ page }) => {
  await login(page, NO_MODEL);
  await expect(page.getByTestId("no-models")).toContainText("No approved models");
  await expect(page.getByText("Generation is intentionally disabled")).toBeVisible();
});

test("loads the completed synthetic GLB through the real viewer path", async ({ page }) => {
  await login(page);
  await createProject(page, "Viewer fixture");
  await page.getByLabel("Prompt").fill("complete fixture");
  await page.getByRole("button", { name: "Generate 3D" }).click();

  await expect(page.getByText("completed", { exact: true }).first()).toBeVisible();
  await expect(page.getByTestId("viewer-ready")).toContainText("Meshes 1");
  await expect(page.getByRole("link", { name: "Download GLB" })).toBeVisible();
});

test("preserves idempotency conflicts and cross-user ownership at the BFF boundary", async ({ page }) => {
  await login(page);
  const projectResponse = await page.request.post("/api/product/v1/projects", {
    data: { name: "Contract project" },
  });
  expect(projectResponse.status()).toBe(201);
  const project = await projectResponse.json();

  const url = `/api/product/v1/projects/${project.id}/jobs/text`;
  const headers = { "Idempotency-Key": "fixed-contract-key" };
  const payload = { prompt: "chair", model_id: "test_model" };
  const first = await page.request.post(url, { data: payload, headers });
  const replay = await page.request.post(url, { data: payload, headers });
  expect(first.status()).toBe(202);
  expect(replay.status()).toBe(200);
  expect((await replay.json()).id).toBe((await first.json()).id);

  const conflict = await page.request.post(url, {
    data: { ...payload, prompt: "different" },
    headers,
  });
  expect(conflict.status()).toBe(409);

  await page.request.delete("/api/session");
  const bobSession = await page.request.post("/api/session", { data: { apiKey: BOB } });
  expect(bobSession.status()).toBe(200);
  const forbidden = await page.request.get(`/api/product/v1/projects/${project.id}`);
  expect(forbidden.status()).toBe(404);
});

test("renders rate-limit failures without hiding the status", async ({ page }) => {
  await login(page);
  await createProject(page, "Limits");
  await page.getByLabel("Prompt").fill("rate limit");
  await page.getByRole("button", { name: "Generate 3D" }).click();
  await expect(page.getByText(/Rate or active-job limit reached/)).toBeVisible();
  await expect(page.getByText(/60 seconds/)).toBeVisible();
});
