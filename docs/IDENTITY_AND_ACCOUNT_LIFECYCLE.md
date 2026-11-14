# Identity and account lifecycle decision

**Research date:** 15 November 2026  
**Status:** Architecture decision recorded; public identity is **not implemented or enabled**.

## Current state

The product backend already supports operator-provisioned user API keys with SHA-256 digest storage, revocation, tenant-scoped projects/jobs/artifacts and rate limiting. The browser studio uses those keys only as a private/development mechanism: the key is validated by the Next.js server and then kept in an HttpOnly SameSite cookie.

That is intentionally not described as public customer authentication. There is no self-service signup, verified email flow, password recovery, account deletion workflow or customer session administration yet.

## Reuse evaluation

### Better Auth — recommended first integration candidate

At the research date the current npm release is Better Auth 1.7.24, MIT-licensed and actively maintained. Its official documentation provides first-party Next.js integration, database-backed sessions, email/password, email verification/password reset and social authentication. It also has a schema/migration CLI.

Engineering fit:
- lives naturally in the existing Next.js application;
- can run against owner-controlled PostgreSQL;
- avoids implementing password hashing, reset tokens, session cookies and OAuth flows from scratch;
- supports later passkeys/2FA/organization features without making them requirements for the first account milestone.

### Auth.js — viable alternative

Auth.js supports OAuth, magic links, credentials and WebAuthn plus database adapters. It is a good fit when authentication is primarily delegated to OAuth/email providers. Its Credentials documentation deliberately leaves password persistence/reset/rate-limit logic to the application, so it is less attractive if first-party email/password accounts are required.

### Keycloak — enterprise alternative

Keycloak remains a mature self-hosted identity server with federation/SSO capabilities. It is operationally heavier than an in-app TypeScript identity layer and is better suited if enterprise SSO, centralized federation or multi-application identity becomes an early requirement.

## Decision

Use **Better Auth as the preferred public-browser identity candidate**, but do **not** install/enable it yet.

The missing safety boundary is not password hashing; it is identity linkage between the browser identity system and the existing Python product authorization model. Adding a second user table without an explicit mapping would create ambiguous ownership. Passing long-lived product API keys into a new session layer would also preserve the wrong credential model.

Before enabling public identity, implement an explicit product identity link and trusted service-auth contract:

1. Better Auth owns browser account/session lifecycle.
2. Each Better Auth user is linked by an immutable provider subject to exactly one product `users.id`; never link by mutable email alone.
3. The server-side BFF authenticates the session and presents a short-lived/internal service assertion to `apps/api`; it must not expose a durable user API key to browser JavaScript.
4. `apps/api` validates that assertion, resolves the product owner and applies the same object-level authorization used for API keys.
5. Existing API keys remain separately issued/revoked credentials for developer/programmatic access.
6. Account deletion revokes sessions and API keys, blocks new work, then follows an explicit data-retention/deletion policy for projects, inputs and artifacts.
7. Password reset/email verification require a selected mail provider, sender-domain setup, abuse/rate controls and operational monitoring before public enablement.

## Proposed schema boundary

Add a versioned table such as:

```text
external_identities
- id
- user_id -> users.id
- issuer
- subject
- created_at
UNIQUE (issuer, subject)
```

Do not store a Better Auth password hash in the Python product tables. Do not duplicate Better Auth sessions in `apps/api`.

The eventual trusted assertion should be short-lived, audience-bound, issuer-bound and cryptographically verified. Exact mechanism (OIDC/JWT or an internal BFF service-token exchange) must be selected and threat-modeled before implementation.

## Feature flag / rollout

Public identity should remain off by default until the mapping + assertion tests exist. The present API-key session remains available for private development and programmatic clients.

A safe rollout sequence is:

1. add external identity mapping migration and admin-only linking tests;
2. add trusted assertion validation to `apps/api` behind an explicit feature flag;
3. integrate Better Auth in `apps/web` against a dedicated test database;
4. test signup, verification, login, session rotation, logout, password reset, account deletion, disabled-user behavior and cross-user isolation;
5. only then enable public browser identity in staging.

## Security tests required before enablement

- session fixation/rotation and logout invalidation;
- reset-token single use and expiry;
- verified-email requirements where configured;
- CSRF/origin/cookie protections;
- disabled/deleted account cannot mint or use product identity;
- immutable issuer+subject mapping and no email-based account takeover;
- cross-user project/job/artifact access remains 404;
- API-key revocation remains independent from browser-session revocation;
- rate limits for signup/login/reset endpoints;
- audit events contain identifiers but never passwords, reset tokens or API keys.

## Cost and external dependencies

No identity provider, email service or paid infrastructure is provisioned by this decision. Better Auth can be self-hosted with the application/database, but real email delivery and any external social/OIDC providers have their own operational and policy requirements.

This is an engineering recommendation, not a production security certification.
