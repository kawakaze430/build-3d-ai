# Original browser request-body implementations

Preserved from commit `56f412f0722394300a522b7392b191702d3f2c48` on
17 November 2026 before consolidating request-body limits.

The files under `apps/web/` preserve their exact original bytes and relative
paths. They are inactive historical material, excluded from the root Docker
context and active app compilation/tests. The replacement stays at the same
active route paths and shares `apps/web/src/lib/request-body.ts`.

The original product route checked actual size only after allocating the full
body, and the login route had no explicit body byte limit. The shared reader
limits streamed bytes regardless of missing or understated Content-Length.
The retained studio component also documents its prior duplicate download URL;
the active component now reuses the existing API helper.

This is a preservation/consolidation record, not evidence of malicious code.
Do not run these superseded routes as an application or copy them over the
active implementations without reviewing the current contracts.
