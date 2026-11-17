# Identity and account lifecycle decision

**Research date:** 15 November 2026  
**Status:** Immutable external-identity mapping is implemented; trusted JWT/JWKS validation is implemented behind a **disabled-by-default** feature flag. Public browser account/session lifecycle is still not enabled.

## Current state

The product backend already supports operator-provisioned user API keys with SHA-256 digest storage, revocation, tenant-scoped projects/jobs/artifacts and rate limiting. The browser studio uses those keys only as a private/development mechanism: the key is validated by the Next.js server and then kept in an HttpOnly SameSite cookie.

Migration `0002` adds an operator-managed `external_identities` table. It maps an immutable `(issuer, subject)` pair to one product user, rejects a second subject for the same product user+issuer, and never uses email/name matching. Store-level resolution returns only active product users. Operator CLI commands can link, list and unlink mappings; there is deliberately no tenant HTTP endpoint for changing them.

That mapping alone is intentionally **not** described as public customer authentication. The API now has an opt-in trusted assertion layer, but it remains disabled unless an operator supplies a reviewed provider file and sets `EXTERNAL_JWT_AUTH_ENABLED=true`. There is still no self-service signup, verified email flow, password recovery, account deletion workflow or customer session administration.

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

## Implemented schema boundary

Migration `0002` adds:

```text
external_identities
- id
- owner_id -> users.id
- issuer
- subject
- created_at
UNIQUE (issuer, subject)
UNIQUE (owner_id, issuer)
```

Issuer values are canonicalized and must use HTTPS except loopback/localhost development. Subjects are treated as opaque provider identifiers. Linking is idempotent only for the exact same owner+issuer+subject and conflicts if an issuer/subject is already owned by someone else.

Operator commands:

```bash
build3d-admin link-identity --user-id <product-user-id> --issuer https://studio.example.com --subject <provider-user-id>
build3d-admin list-identities --user-id <product-user-id>
build3d-admin unlink-identity --issuer https://studio.example.com --subject <provider-user-id>
```

Do not store a Better Auth password hash in the Python product tables. Do not duplicate Better Auth sessions in `apps/api`.

## Trusted assertion layer

`apps/api/src/build3d_api/trusted_identity.py` implements the previously missing trusted-assertion boundary using pinned PyJWT 2.15.1 + cryptography 50.0.2. It is disabled by default.

Provider configuration is static and operator-controlled; there is **no automatic OIDC discovery**. Each provider pins:
- exact JWT issuer string;
- one or more accepted audiences;
- exact JWKS URL;
- asymmetric algorithm allowlist limited to RS256, ES256 or EdDSA;
- maximum assertion lifetime (30–3600 seconds);
- bounded clock leeway, JWKS cache, unknown-key refresh cooldown and network timeout.

The validator bounds JWT/JWKS sizes, disables redirects, rejects remote plaintext HTTP, requires `exp`, `iat`, `iss`, `sub` and `aud`, selects no algorithm from attacker-controlled token data, and never uses email/name claims for ownership. Only a cryptographically validated issuer+subject pair is passed to the immutable product mapping. External assertions have their own atomic database-backed 60-second rate window in migration `0004`.

Example configuration: [`config/identity-providers.example.json`](../config/identity-providers.example.json).

```bash
EXTERNAL_JWT_AUTH_ENABLED=true
IDENTITY_PROVIDER_FILE=/run/secrets/build3d-identity-providers.json
```

Existing `b3d_...` developer API keys remain independently valid. A disabled/unmapped product user cannot gain access merely because the external JWT is valid.

This still does **not** enable Better Auth itself or public signup/session lifecycle. The browser/BFF integration remains the next layer.

## Feature flag / rollout

Public identity should remain off by default until the mapping + assertion tests exist. The present API-key session remains available for private development and programmatic clients.

A safe rollout sequence is:

1. **Implemented/tested:** external identity mapping migration and operator-only linking/listing/unlinking;
2. **Implemented/tested:** trusted assertion/JWKS validation in `apps/api` behind an explicit disabled-by-default feature flag;
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
