# Previous gateway packaging

These files preserve the gateway Dockerfile and Compose entry point byte-for-byte
from baseline `56f412f0722394300a522b7392b191702d3f2c48`, before the universal
repository consolidation on 17 November 2026. Their directory hierarchy records
the original repository paths.

The old gateway image installed dependencies from package declarations without
the CPU constraints used by the product API. The active gateway packaging now
uses the root build context and the same `requirements.lock` constraints. No
application API, database schema, package declaration or lockfile changed.

This is historical, inactive packaging, retained for recovery and comparison.
Use the root `compose.gateway.yml` and `apps/gateway/Dockerfile` for current
commands. Source/version constraints still do not constitute a complete
artifact-hash lock or a production deployment approval.
