// Use the canonical browser contract configuration with managed-Chromium policy.
// Playwright loads the TypeScript configuration through its supported transformer.
process.env.BUILD3D_SYSTEM_CHROMIUM = '/usr/bin/chromium';
module.exports = require('../../apps/web/playwright.config.ts').default;
