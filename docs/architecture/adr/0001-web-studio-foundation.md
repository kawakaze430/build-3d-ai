# ADR 0001 — First-party browser studio foundation

**Date:** 2026-11-15  
**Status:** Accepted for the private product milestone

## Context

The project needs a browser studio that talks to the existing tenant/product API without exposing operator or upstream GPU credentials. The previous plan required an evidence-based choice between adapting Open3DStudio, selectively reusing it, or creating a first-party frontend.

Open3DStudio was inspected at pinned commit `f2e403eb11a2c33077e9f353fa240974edb06981`. Its repository is Apache-2.0, but the application is an Electron + Create React App / `react-scripts 5` product with a large direct 3DAIGC API client and workflows broader than the contracts currently exposed by Build 3D AI. Its most recent inspected source push is from January 2026. Adopting the whole UI would import backend coupling, desktop packaging, product assumptions and branding/UX debt that this project does not need.

The useful technical pattern is not unique to that application: Three.js, React Three Fiber and Drei are maintained reusable libraries with suitable permissive licenses.

## Decision

Choose **C: create a clean first-party frontend** in `apps/web` using Next.js, React, Three.js and React Three Fiber.

Do not vendor or clone Open3DStudio's application. Individual ideas or components may be reconsidered later only after a file-level fit/license review.

The private login flow uses the already-implemented operator-provisioned **user API key**, but the key is submitted once to a Next.js server route and stored in an HttpOnly SameSite cookie. Client JavaScript never receives the persisted key. A server-side BFF proxies only a strict allowlist of tenant API routes to a fixed `BUILD3D_API_URL`; the browser cannot choose arbitrary upstream URLs and never receives the gateway control key or GPU bearer token.

## Initial dependency set

- Next.js 16.4.6 / React 19.3.1 — MIT
- Three.js 0.187.0 — MIT
- React Three Fiber 9.8.2 — MIT
- Drei 10.7.9 — MIT
- Vitest 5.1.0 — MIT
- Playwright 1.65.1 — Apache-2.0

Exact transitive package inventory and lockfile review remain release work; these pins are for the first browser milestone, not blanket commercial approval of every future frontend dependency.

## Consequences

Benefits:
- original product UI and branding;
- narrow coupling to the Build 3D tenant API rather than upstream admin APIs;
- server-side containment of current user API keys;
- real GLB rendering and downloads through owner-scoped product routes;
- easier migration to a mature identity provider later because browser code does not depend on upstream authentication.

Costs:
- some UI/product behavior must be implemented rather than inherited;
- the first milestone does not include public signup, password recovery, billing or collaboration;
- current API-key sessions are a private/development mechanism, not final public SaaS identity.

## Security and rollback

The BFF exposes only projects, approved models, owned jobs/artifacts and downloads. It rejects arbitrary paths and query parameters and applies a bounded request-body limit before forwarding. Product API ownership checks remain authoritative.

Rollback is isolated: remove/disable `apps/web`; the existing FastAPI product API and worker are unchanged.
