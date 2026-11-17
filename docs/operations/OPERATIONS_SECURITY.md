# Production Security, Privacy and Cloud Cost Rules

## Customer security

Require auth and object-level authorization for all projects, jobs, artifacts and downloads. Guard against IDOR, broken authorization, unsafe uploaded meshes/textures, zip bombs, oversized objects, malicious scripts in blend/scene formats, SSRF by reference URL, denial of service and prompt injection when tools use model output.

Convert and render files only in sandboxed short-lived containers with minimal credentials/network. Validate file type/content, size, nesting, asset/texture references and processing time. Never execute uploaded scripts.

Protect customer assets with private storage, least-privilege IAM and expiring signed URLs. Encrypt in transit and at rest. Secret-store integration, backups and recovery drills required before public launch. Minimize logs of user content. Implement deletion and retention rules and clear terms around training on customer uploads (default: **do not use for training without permission**).

## Payment operations

Use transaction-safe credit reservations, idempotent webhooks, refund/reversal on failed generation, rate limits and fraud controls. Never treat a test payment or demo as proof of completed production billing.

## GPU/cloud financial controls

- Cloud plan: AWS is the intended principal infrastructure; Google Colab is research-only. Confirm cloud credits, quotas, eligibility, expiry and actual rates before assuming “free”.
- Explicit owner approval and fixed budget for new paid GPU resources, large dataset downloads and training runs.
- Autosuspend idle GPUs, queue workloads, cap max job time/concurrency, limit retries, monitor per-model GPU-seconds and costs.
- Enforce billing alerts; deny unreviewed public unrestricted GPU endpoints.
- Benchmark quality and cost before training or integrating another expensive model.

## Reliability

Immutable artifacts with hashes, queue dead-letter handling, cancellation, failure taxonomy, rollback of model version and app release, automated availability checks, P50/P95 metrics, backup/restore tests, and customer support escalation process.

## Licensing operations

Keep a current register for source, model weights and transitive dependencies. Block restricted research libraries from production by default. Preserve upstream attributions. Conduct legal review for geographic, commercial-SaaS and model-output limitations before release.
