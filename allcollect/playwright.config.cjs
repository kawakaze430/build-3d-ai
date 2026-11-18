// Retained system-Chromium configuration used for cloud browser contracts.
const path = require('node:path');
const web = path.resolve(__dirname, '../../apps/web');

module.exports = {
  testDir: path.join(web, 'tests/e2e'),
  outputDir: '/tmp/build3d-playwright-results',
  workers: 1,
  timeout: 30000,
  use: {
    baseURL: 'http://127.0.0.1:3000',
    launchOptions: {
      executablePath: '/usr/bin/chromium',
      args: ['--no-sandbox'],
    },
  },
  webServer: [
    {
      cwd: web,
      command: 'node tests/mock-backend.mjs',
      url: 'http://127.0.0.1:8099/health',
      timeout: 30000,
    },
    {
      cwd: web,
      command: 'npm run dev -- --hostname 127.0.0.1 --port 3000',
      url: 'http://127.0.0.1:3000',
      timeout: 120000,
      env: { BUILD3D_API_URL: 'http://127.0.0.1:8099' },
    },
  ],
};
