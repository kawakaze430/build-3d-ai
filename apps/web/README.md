# Build 3D AI Web Studio

This is the first real browser product surface for the durable `apps/api` backend. It is **not** a fake generator and it does not contain a sample mesh in production UI paths.

## Security model

- The browser submits the current operator-provisioned **user API key** to `/api/session`.
- Next.js validates that key against `GET /v1/me`, then stores it in an HttpOnly, SameSite=Strict cookie.
- Browser JavaScript never receives the persisted key.
- `BUILD3D_API_URL` is server configuration; users cannot choose arbitrary proxy targets.
- The BFF exposes a strict allowlist of tenant product routes only. Operator gateway and upstream GPU credentials are never proxied.
- The FastAPI product API remains the authoritative tenant/ownership boundary.

This is a private/development authentication mechanism. Public signup, recovery, email verification, account deletion and long-lived customer sessions still require a mature identity solution.

## Run locally

Start/migrate `apps/api`, provision a user key, then:

```bash
cd apps/web
cp .env.example .env.local
npm install
npm run dev
```

The default backend is `http://127.0.0.1:8081`.

## What works

- private API-key login through a server-side session;
- project list/create/open with URL-persisted selected project;
- approved-model list and an explicit no-model-approved state;
- real text and image job submission with fresh idempotency keys;
- persisted job history with all uncertain/recovery states preserved;
- polling cancellation when navigating away from a project/page;
- real owner-scoped GLB download;
- Three.js/R3F GLB viewport with orbit, zoom, reset, wireframe and mesh/triangle statistics;
- responsive UI and explicit error handling for 401/404/409/413/429/5xx;
- unit and Playwright browser tests using a clearly synthetic test backend/triangle GLB fixture.

## Validation

```bash
npm run typecheck
npm test
npm run build
npx playwright install --with-deps chromium
npm run test:e2e
```

Browser fixtures prove the web/API contract and GLB viewer path only. They **do not** prove real AI generation, model quality, GPU cost, Blender import or production deployment.
