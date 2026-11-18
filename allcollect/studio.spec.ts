import { expect, test, type Page } from "@playwright/test";

const ALICE = "b3d_" + "a".repeat(43);
const BOB = "b3d_" + "b".repeat(43);
const NO_MODEL = "b3d_" + "c".repeat(43);
const NEAR_LIMIT = "b3d_" + "d".repeat(43);
const SESSION_COOKIE = "build3d_user_key";

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

test("keeps sign-out retryable until the session cookie is cleared", async ({ page }) => {
  await login(page);
  const cookie = (await page.context().cookies()).find((item) => item.name === SESSION_COOKIE);
  expect(cookie?.httpOnly).toBe(true);
  expect(cookie?.sameSite).toBe("Strict");

  await page.route("**/api/session", async (route) => {
    if (route.request().method() === "DELETE") await route.abort("failed");
    else await route.continue();
  });
  const signOut = page.getByRole("button", { name: "Sign out" });
  await signOut.click();
  await expect(page.getByText("Could not confirm sign-out. Try again.")).toBeVisible();
  await expect(signOut).toBeEnabled();
  expect((await page.context().cookies()).some((item) => item.name === SESSION_COOKIE)).toBe(true);
  await page.reload();
  await expect(signOut).toBeVisible();

  await page.unroute("**/api/session");
  const confirmation = page.waitForResponse((response) =>
    response.url().endsWith("/api/session") && response.request().method() === "DELETE",
  );
  await signOut.click();
  const response = await confirmation;
  expect(response.status()).toBe(204);
  expect(response.headers()["cache-control"]).toBe("no-store");
  await expect(page.getByLabel("User API key")).toBeVisible();
  expect((await page.context().cookies()).some((item) => item.name === SESSION_COOKIE)).toBe(false);
  await page.reload();
  await expect(page.getByLabel("User API key")).toBeVisible();
});

test("clears a revoked cookie when restoring the studio", async ({ page, request }) => {
  await login(page);
  expect((await request.post("http://127.0.0.1:8099/__revoke_alice")).ok()).toBe(true);

  const restoration = page.waitForResponse((response) =>
    response.url().endsWith("/api/session") && response.request().method() === "GET",
  );
  await page.reload();
  expect((await restoration).status()).toBe(401);
  await expect(page.getByLabel("User API key")).toBeVisible();
  expect((await page.context().cookies()).some((item) => item.name === SESSION_COOKIE)).toBe(false);
});

test("expires an idle workspace after the browser loses its session cookie", async ({ page }) => {
  await page.clock.install();
  await login(page);
  await expect(page.getByText("Create your first private project")).toBeVisible();

  await page.context().clearCookies({ name: SESSION_COOKIE });
  await page.clock.runFor(5000);
  await expect(page.getByText("Your session has ended. Sign in again with a valid user API key.")).toBeVisible();
  await expect(page.getByLabel("User API key")).toBeVisible();
  await expect(page.getByRole("button", { name: "Sign out" })).toHaveCount(0);
});

test("ends a revoked workspace and discards an earlier submission result after re-login", async ({ page, request }) => {
  await page.clock.install();
  await login(page);
  const project = await createProject(page, "Previous user's workspace");

  const submitted = Promise.withResolvers<number>();
  const release = Promise.withResolvers<void>();
  await page.route(`**/api/product/v1/projects/${project}/jobs/text`, async (route) => {
    const response = await route.fetch();
    submitted.resolve(response.status());
    await release.promise;
    await route.fulfill({ response }).catch(() => {});
  });
  try {
    await page.getByLabel("Prompt").fill("Previous user's draft");
    await page.getByRole("button", { name: "Generate 3D" }).click();
    expect(await submitted.promise).toBe(202);
    expect((await request.post("http://127.0.0.1:8099/__revoke_alice")).ok()).toBe(true);

    await page.clock.runFor(5000);
    await expect(page.getByText("Your session has ended. Sign in again with a valid user API key.")).toBeVisible();
    expect((await page.context().cookies()).some((item) => item.name === SESSION_COOKIE)).toBe(false);
    await page.getByLabel("User API key").fill(BOB);
    await page.getByRole("button", { name: "Connect to product API" }).click();
    await expect(page.getByTitle("bob")).toBeVisible();
    release.resolve();
    await expect(page.getByTitle("bob")).toBeVisible();
    await expect(page.getByLabel("Prompt")).toHaveValue("");
    await expect(page.getByRole("button", { name: /Previous user's workspace|Previous user's draft/ })).toHaveCount(0);
  } finally {
    release.resolve();
  }
});

test("browses project and job history beyond the first 100 with stable selection and deep links", async ({ page, request }) => {
  expect((await request.post("http://127.0.0.1:8099/__seed_history")).ok()).toBe(true);
  await login(page);
  const projectList = page.locator(".project-list .project-item");
  const jobList = page.locator(".job-list .job-card");
  await expect(projectList).toHaveCount(100);
  await expect(jobList).toHaveCount(100);
  const initialProjects = await projectList.evaluateAll((items) => items.map((item) => item.textContent));
  const initialJobs = await jobList.evaluateAll((items) => items.map((item) => item.querySelector("strong")?.textContent));

  await page.getByRole("button", { name: "Next project page" }).click();
  await expect(projectList).toHaveCount(2);
  await expect(page.getByRole("button", { name: "Next project page" })).toBeDisabled();
  await expect(page.getByRole("heading", { name: "History project 102" })).toBeVisible();
  const olderProjects = await projectList.evaluateAll((items) => items.map((item) => item.textContent));
  expect(new Set([...initialProjects, ...olderProjects]).size).toBe(102);

  await page.getByRole("button", { name: "Next job page" }).click();
  const olderJob = page.getByRole("button", { name: /History job 001/ });
  await expect(olderJob).toBeVisible();
  const olderJobs = await jobList.evaluateAll((items) => items.map((item) => item.querySelector("strong")?.textContent));
  expect(new Set([...initialJobs, ...olderJobs]).size).toBe(200);
  await olderJob.click();
  await expect(olderJob).toHaveAttribute("aria-current", "true");
  await page.getByRole("button", { name: "Next job page" }).click();
  await expect(page.getByText("No jobs on this page.")).toBeVisible();
  await expect(page.getByRole("button", { name: "Next job page" })).toBeDisabled();
  await expect(page.getByTitle("History job 001")).toBeVisible();
  await page.getByRole("button", { name: "Previous job page" }).click();
  await expect(olderJob).toHaveAttribute("aria-current", "true");

  await page.getByRole("button", { name: /History project 001/ }).click();
  await expect(page.getByRole("heading", { name: "History project 001" })).toBeVisible();
  await expect(page.getByText("No jobs yet.")).toBeVisible();
  await expect(page).toHaveURL(/\?project=history_project_001$/);
  await page.reload();
  await expect(page.getByRole("heading", { name: "History project 001" })).toBeVisible();
  await expect(projectList).toHaveCount(100);
});

test("discards an in-flight history page when its project is no longer active", async ({ page, request }) => {
  expect((await request.post("http://127.0.0.1:8099/__seed_history")).ok()).toBe(true);
  await login(page);
  const requested = Promise.withResolvers<void>();
  const release = Promise.withResolvers<void>();
  const settled = Promise.withResolvers<void>();
  await page.route(
    (url) => url.pathname.endsWith("/history_project_102/jobs") && url.searchParams.get("offset") === "100",
    async (route) => {
      const response = await route.fetch();
      requested.resolve();
      await release.promise;
      await route.fulfill({ response }).catch(() => {});
      settled.resolve();
    },
  );
  try {
    await page.getByRole("button", { name: "Next job page" }).click();
    await requested.promise;
    await expect(page.getByRole("status").filter({ hasText: "Loading…" })).toBeVisible();
    await page.getByRole("button", { name: /History project 101/ }).click();
    await expect(page.getByText("No jobs yet.")).toBeVisible();
    release.resolve();
    await settled.promise;
    await expect(page.getByRole("heading", { name: "History project 101" })).toBeVisible();
    await expect(page.getByRole("button", { name: /History job 001/ })).toHaveCount(0);
  } finally {
    release.resolve();
  }
});

test("refreshes the chosen offsets after inserts and preserves them after a rejected page", async ({ page, request }) => {
  expect((await request.post("http://127.0.0.1:8099/__seed_history")).ok()).toBe(true);
  await login(page);
  const rejectedJobPage = (url: URL) =>
    url.pathname.endsWith("/history_project_102/jobs") && url.searchParams.get("offset") === "100";
  await page.route(rejectedJobPage, (route) => route.fulfill({
    status: 422,
    json: { detail: "History page rejected" },
  }));
  const nextJob = page.getByRole("button", { name: "Next job page" });
  await nextJob.click();
  await expect(page.getByText("History page rejected")).toBeVisible();
  await expect(page.getByRole("button", { name: /History job 200/ })).toBeVisible();
  await page.unroute(rejectedJobPage);
  await nextJob.click();
  await expect(page.getByRole("button", { name: /History job 001/ })).toBeVisible();

  await page.getByLabel("Prompt").fill("New independent job selection");
  await page.getByRole("button", { name: "Generate 3D" }).click();
  await expect(page.getByTitle("New independent job selection")).toBeVisible();
  await expect(page.getByRole("button", { name: /History job 101/ })).toBeVisible();
  await expect(page.getByRole("button", { name: /History job 001/ })).toHaveCount(0);

  await page.getByRole("button", { name: "Next project page" }).click();
  await expect(page.getByRole("button", { name: /History project 001/ })).toBeVisible();
  await page.getByLabel("New project").fill("New independent project selection");
  await page.getByRole("button", { name: "Add" }).click();
  await expect(page.getByRole("heading", { name: "New independent project selection" })).toBeVisible();
  await expect(page.getByRole("button", { name: /History project 003/ })).toBeVisible();
  await expect(page.getByRole("button", { name: "Previous project page" })).toBeEnabled();

  const unsupported = await page.request.get("/api/product/v1/projects?limit=101&offset=0");
  expect(unsupported.status()).toBe(422);
  const outsideRange = await page.request.get("/api/product/v1/projects?limit=100&offset=100001");
  expect(outsideRange.status()).toBe(422);
});
