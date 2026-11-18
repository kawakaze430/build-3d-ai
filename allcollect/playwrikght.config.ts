import { defineConfig, devices } from "@playwright/test";
import path from "node:path";

const systemChromium = process.env.BUILD3D_SYSTEM_CHROMIUM;
const web = path.resolve(__dirname);

export default defineConfig({
  testDir: path.join(web, "tests/e2e"),
  ...(systemChromium ? { outputDir: "/tmp/build3d-playwright-results" } : {}),
  fullyParallel: false,
  workers: 1,
  timeout: 30_000,
  expect: { timeout: 10_000 },
  use: {
    baseURL: "http://127.0.0.1:3000",
    trace: "retain-on-failure",
    ...devices["Desktop Chrome"],
    ...(systemChromium ? { launchOptions: { executablePath: systemChromium, args: ["--no-sandbox"] } } : {}),
  },
  webServer: [
    {
      cwd: web,
      command: "node tests/mock-backend.mjs",
      url: "http://127.0.0.1:8099/health",
      reuseExistingServer: !systemChromium,
      timeout: 30_000,
    },
    {
      cwd: web,
      command: "npm run dev -- --hostname 127.0.0.1 --port 3000",
      url: "http://127.0.0.1:3000",
      reuseExistingServer: !systemChromium,
      timeout: 120_000,
      env: {
        BUILD3D_API_URL: "http://127.0.0.1:8099",
      },
    },
  ],
});
