import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { expect, test, type Page } from "@playwright/test";

const fixturePath = process.env.BUILD3D_ACCEPTANCE_FIXTURE;
if (!fixturePath) throw new Error("A disposable real API fixture is required.");

const fixture = JSON.parse(readFileSync(fixturePath, "utf8")) as {
  aliceKey: string;
  bobKey: string;
  projectId: string;
  jobId: string;
  artifactBytes: number;
  artifactSha256: string;
};

async function login(page: Page, key: string) {
  await page.getByLabel("User API key").fill(key);
  await page.getByRole("button", { name: "Connect to product API" }).click();
  await expect(page.getByRole("heading", { name: "Projects" })).toBeVisible();
}

test("persists a private project and confirms sign-out against the real API", async ({ page }) => {
  await page.goto("/");
  await login(page, fixture.aliceKey);
  await expect(page.getByTestId("no-models")).toContainText("No approved models");
  await expect(page.getByRole("button", { name: "Generate 3D" })).toHaveCount(0);

  const projectName = "Browser acceptance project";
  await page.getByLabel("New project").fill(projectName);
  await page.getByRole("button", { name: "Add", exact: true }).click();
  const project = page.getByRole("button", { name: new RegExp(projectName) });
  await expect(project).toBeVisible();
  const projectId = await project.getAttribute("data-project-id");
  expect(projectId).toMatch(/^[a-f0-9]{32}$/);

  await page.reload();
  await project.click();
  await expect(page.getByRole("heading", { name: projectName })).toBeVisible();
  await expect(page.getByText("No jobs yet.")).toBeVisible();

  const isPrivateSessionCookie = (cookie: { name: string }) => cookie.name === "build3d_user_key";
  const cookie = (await page.context().cookies()).find(isPrivateSessionCookie);
  expect(cookie?.httpOnly).toBe(true);
  expect(cookie?.sameSite).toBe("Strict");
  await page.getByRole("button", { name: "Sign out" }).click();
  await expect(page.getByLabel("User API key")).toBeVisible();
  expect((await page.context().cookies()).some(isPrivateSessionCookie)).toBe(false);
  expect((await page.request.get("/api/product/v1/projects")).status()).toBe(401);

  await page.reload();
  await login(page, fixture.bobKey);
  await expect(page.getByText(/Create your first private project/)).toBeVisible();
  await expect(project).toHaveCount(0);
  expect((await page.request.get(`/api/product/v1/projects/${projectId}`)).status()).toBe(404);
});

test("renders and downloads a stored synthetic GLB only for its owner", async ({ page }) => {
  await page.goto("/");
  await login(page, fixture.aliceKey);
  await page.getByRole("button", { name: /Synthetic artifact project/ }).click();
  const job = page.getByRole("button", { name: /Synthetic triangle fixture/ });
  await expect(job).toContainText("completed");
  await job.click();
  await expect(page.getByTestId("viewer-ready")).toContainText("Meshes 1");

  const usage = await page.request.get("/api/product/v1/storage");
  expect(usage.status()).toBe(200);
  expect(await usage.json()).toMatchObject({
    used_bytes: fixture.artifactBytes,
    limit_bytes: 5 * 1024 ** 3,
    remaining_bytes: 5 * 1024 ** 3 - fixture.artifactBytes,
  });
  await expect(page.getByTestId("storage-usage")).toContainText("of 5 GiB");
  await expect(page.getByTestId("storage-usage")).not.toContainText("0 B of 5 GiB");

  const download = page.getByRole("link", { name: "Download GLB" });
  const downloadPath = `/api/product/v1/jobs/${fixture.jobId}/download`;
  await expect(download).toHaveAttribute("href", downloadPath);
  const response = await page.request.get(downloadPath);
  expect(response.status()).toBe(200);
  expect(response.headers()["content-type"]).toBe("model/gltf-binary");
  expect(response.headers()["x-artifact-sha256"]).toBe(fixture.artifactSha256);
  const payload = await response.body();
  expect(payload.byteLength).toBe(fixture.artifactBytes);
  expect(createHash("sha256").update(payload).digest("hex")).toBe(fixture.artifactSha256);

  const [browserDownload] = await Promise.all([page.waitForEvent("download"), download.click()]);
  expect(browserDownload.suggestedFilename()).toBe(`${fixture.jobId}.glb`);
  await browserDownload.delete();

  await page.getByRole("button", { name: "Sign out" }).click();
  await login(page, fixture.bobKey);
  expect((await page.request.get(`/api/product/v1/projects/${fixture.projectId}/jobs`)).status()).toBe(404);
  expect((await page.request.get(downloadPath)).status()).toBe(404);
});
