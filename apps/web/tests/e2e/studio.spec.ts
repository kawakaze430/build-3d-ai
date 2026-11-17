import { expect, test, type Page } from "@playwright/test";

const ALICE = "b3d_" + "a".repeat(43);
const BOB = "b3d_" + "b".repeat(43);
const NO_MODEL = "b3d_" + "c".repeat(43);
const NEAR_LIMIT = "b3d_" + "d".repeat(43);

async function login(page: Page, key = ALICE) {
  await page.goto("/");
  await page.getByLabel("User API key").fill(key);
  await page.getByRole("button", { name: "Connect to product API" }).click();
  await expect(page.getByRole("heading", { name: "Projects" })).toBeVisible();
}

async function createProject(page: Page, name: string) {
  await page.getByLabel("New project").fill(name);
  await page.getByRole("button", { name: "Add" }).click();
  const project = page.getByRole("button", { name: new RegExp(name) });
  await expect(project).toBeVisible();
  const projectId = await project.getAttribute("data-project-id");
  if (!projectId) throw new Error("Created project has no ID");
  return projectId;
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

test("shows persistent storage usage and near-limit guidance", async ({ page }) => {
  await login(page);
  const storage = page.getByTestId("storage-usage");
  await expect(storage).toContainText("Storage");
  await expect(storage).toContainText("0 B of 5 GiB");
  await expect(storage).toContainText("5 GiB remaining");

  await page.request.delete("/api/session");
  await page.goto("/");
  await page.getByLabel("User API key").fill(NEAR_LIMIT);
  await page.getByRole("button", { name: "Connect to product API" }).click();
  await expect(page.getByTestId("storage-usage")).toContainText("90%");
  await expect(page.getByText(/Storage is nearing the configured limit/)).toBeVisible();
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
  await expect(page.getByTestId("storage-usage")).not.toContainText("0 B of 5 GiB");
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

test("cancels a slow poll, displays the replacement and reports a genuine failure", async ({ page }) => {
  await page.clock.install();
  await login(page);
  const project = await page.request.post("/api/product/v1/projects", { data: { name: "Polling" } });
  expect(project.status()).toBe(201);
  const { id } = await project.json();
  const job = await page.request.post(`/api/product/v1/projects/${id}/jobs/text`, {
    data: { prompt: "Replacement poll result", model_id: "test_model" },
    headers: { "Idempotency-Key": "poll-result" },
  });
  expect(job.status()).toBe(202);

  const firstPoll = Promise.withResolvers<void>();
  const releaseFirstPoll = Promise.withResolvers<void>();
  let polls = 0;
  await page.route((url) => url.pathname === `/api/product/v1/projects/${id}/jobs`, async (route) => {
    polls += 1;
    if (polls === 1) {
      const response = await route.fetch();
      firstPoll.resolve();
      await releaseFirstPoll.promise;
      // The browser can close the intercepted request when the next poll cancels it.
      await route.fulfill({ response }).catch(() => {});
    } else if (polls === 2) {
      await route.continue();
    } else {
      await route.abort("failed");
    }
  });
  try {
    await page.goto(`/?project=${id}`);
    await firstPoll.promise;
    await page.clock.runFor(5000);
    await expect(page.getByRole("button", { name: /Replacement poll result/ })).toBeVisible();
    await expect(page.getByText(/Service temporarily unavailable/)).toHaveCount(0);
    releaseFirstPoll.resolve();
    await page.clock.runFor(5000);
    await expect(page.getByText(/Service temporarily unavailable/)).toBeVisible();
  } finally {
    releaseFirstPoll.resolve();
  }
});

test("keeps the current project selected after an earlier project submits a job", async ({ page }) => {
  await login(page);
  const first = await createProject(page, "First project");
  const second = await createProject(page, "Second project");
  const job = await page.request.post(`/api/product/v1/projects/${second}/jobs/text`, {
    data: { prompt: "Second project result", model_id: "test_model" },
    headers: { "Idempotency-Key": "second-project-job" },
  });
  expect(job.status()).toBe(202);

  const historyRequested = Promise.withResolvers<void>();
  const releaseHistory = Promise.withResolvers<void>();
  await page.route((url) => url.pathname === `/api/product/v1/projects/${first}/jobs`, async (route) => {
    const response = await route.fetch();
    historyRequested.resolve();
    await releaseHistory.promise;
    await route.fulfill({ response }).catch(() => {});
  });
  const submitted = Promise.withResolvers<number>();
  const releaseSubmission = Promise.withResolvers<void>();
  await page.route(`**/api/product/v1/projects/${first}/jobs/text`, async (route) => {
    const response = await route.fetch();
    submitted.resolve(response.status());
    await releaseSubmission.promise;
    await route.fulfill({ response });
  });
  try {
    await page.getByRole("button", { name: /First project/ }).click();
    await historyRequested.promise;
    await page.getByLabel("Prompt").fill("First project result");
    await page.getByRole("button", { name: "Generate 3D" }).click();
    expect(await submitted.promise).toBe(202);
    await page.getByRole("button", { name: /Second project/ }).click();
    await expect(page.getByRole("button", { name: /Second project result/ })).toBeVisible();

    releaseHistory.resolve();
    releaseSubmission.resolve();
    await expect(page.getByRole("button", { name: "Generate 3D" })).toBeEnabled();
    await expect(page.getByRole("heading", { name: "Second project" })).toBeVisible();
    await expect(page.getByRole("button", { name: /Second project result/ })).toBeVisible();
    await expect(page.getByRole("button", { name: /First project result/ })).toHaveCount(0);
  } finally {
    releaseHistory.resolve();
    releaseSubmission.resolve();
  }
});

test("discards a pending job history response when the workspace signs out", async ({ page }) => {
  await login(page);
  const project = await page.request.post("/api/product/v1/projects", { data: { name: "Private project" } });
  expect(project.status()).toBe(201);
  const { id } = await project.json();
  const job = await page.request.post(`/api/product/v1/projects/${id}/jobs/text`, {
    data: { prompt: "Previous session result", model_id: "test_model" },
    headers: { "Idempotency-Key": "previous-session-job" },
  });
  expect(job.status()).toBe(202);

  const pending = Promise.withResolvers<void>();
  const release = Promise.withResolvers<void>();
  await page.route((url) => url.pathname === `/api/product/v1/projects/${id}/jobs`, async (route) => {
    const response = await route.fetch();
    pending.resolve();
    await release.promise;
    await route.fulfill({ response }).catch(() => {});
  });
  try {
    await page.goto(`/?project=${id}`);
    await pending.promise;
    await page.getByRole("button", { name: "Sign out" }).click();
    await page.getByLabel("User API key").fill(BOB);
    await page.getByRole("button", { name: "Connect to product API" }).click();
    await expect(page.getByRole("button", { name: "Sign out" })).toBeVisible();
    release.resolve();
    await expect(page.getByText("Create your first private project")).toBeVisible();
    await expect(page.getByRole("button", { name: /Previous session result/ })).toHaveCount(0);
    await expect(page.getByText(/Service temporarily unavailable/)).toHaveCount(0);
  } finally {
    release.resolve();
  }
});
