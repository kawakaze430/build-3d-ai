# Post-restructure validation — 17 November 2026

The owner reauthorized full available testing after the earlier execution pause.
The first run exposed a Vitest alias-resolution regression; the configuration was
fixed and all available local suites then passed.

| Suite | Passed |
|---|---:|
| SQLite API/gateway | 136 |
| PostgreSQL API | 83 |
| Preparation and metadata auditor | 12 |
| CPU marching cubes | 2 |
| Web unit tests | 14 |
| Browser contracts | 6 |

TypeScript, production build/startup, four installed CLI entrypoints, dependency checks, wheel/migration packaging,
relocated Compose configuration, both nonroot CPU containers and real API/studio
flows also passed. Fresh pinned source preparation succeeded without model load.

[Detailed results](RESULTS.json), [backend evidence](BACKEND_RESULTS.json),
[structural evidence](STRUCTURE_RESULTS.json) and the
[complete test record](../../TEST_AND_VALIDATION_REPORT.txt) retain commands,
initial failures, final outcomes and limits. No real GPU inference, real S3,
Blender or production/public-service acceptance is claimed. Local versions were
Python 3.12 and Node 24; hosted version-matrix results remain unobserved.
