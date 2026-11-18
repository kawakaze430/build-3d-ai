import { defineConfig, devices } from "@playwright/test";
import path from "node:path";

const fixturePath = process.env.BUILD3D_ACCEPTANCE_FIXTURE;
if (!fixturePath || !process.env.BUILD3D_ACCEPTANCE_PYTHON) {
  throw new Error("Run apps/web/tests/real-api/run.py with the prepared Python environment.");
}

const chromium = process.env.BUILD3D_SYSTEM_CHROMIUM;
const web = path.resolve(__dirname);
const apiPort = 18181;
const webPort = 13000;
const apiUrl = `http://127.0.0.1:${apiPort}`;
const webUrl = `http://127.0.0.1:${webPort}`;

export default defineConfig({
  testDir: path.join(web, "tests/real-api"),
  outputDir: path.join(path.dirname(fixturePath), "playwright-results"),
  reporter: "list",
  workers: 1,
  use: {
    ...devices["Desktop Chrome"],
    baseURL: webUrl,
    // Session request bodies and cookies contain disposable API keys.
    trace: "off",
    screenshot: "off",
    video: "off",
    ...(chromium ? { launchOptions: { executablePath: chromium } } : {}),
  },
  webServer: [
    {
      cwd: path.resolve(web, "../.."),
      command: `"$BUILD3D_ACCEPTANCE_PYTHON" -m uvicorn build3d_api.main:create_app --factory --host 127.0.0.1 --port ${apiPort}`,
      url: `${apiUrl}/health`,
      timeout: 30_000,
      reuseExistingServer: false,
    },
    {
      cwd: web,
      command: `npm run dev -- --hostname 127.0.0.1 --port ${webPort}`,
      url: webUrl,
      timeout: 120_000,
      reuseExistingServer: false,
      env: { BUILD3D_API_URL: apiUrl },
    },
  ],
});
