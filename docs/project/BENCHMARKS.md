# Competitive Benchmark and Quality Protocol

## What to compare

Our product vs chosen legal, documented market baselines (e.g. Meshy and Tripo) using dated versions and identical permitted inputs. “Best” is not assumed; evidence is required.

## Starter benchmark

A frozen 100-item set: 25 stylized characters, 25 hard-surface objects, 25 organic/complex objects, and 25 everyday props. Record input usage rights and original camera view. Add hard test cases with long hair, facial expressions, hands, reflective materials, thin structures and clothing.

Use held-out inputs for any fine-tuned model. Evaluate at multiple angles, not only the reference-facing render. Keep failures in the sample; no cherry-picking.

## Metrics

- Valid-generation rate, quality-rated from multiple views, input silhouette/shape fidelity.
- Geometry integrity: broken pieces, floating surfaces, normals, UV/material seams, triangle counts.
- Artist usability: deformation under skeleton, Blender/Unity/Unreal import where supported, manual fixup minutes.
- Facial animation readiness: eye look/blink, jaw interior, brow/smile, speech shape consistency.
- Latency P50/P95, GPU-seconds, cold start, VRAM, failure/retry rate and complete USD cost/asset.
- UX success and stability: download, privacy and errors.

## Honest publication

Label exact generation model, weight and repository revision, quality setting, hardware, timestamp, evaluation method and confidence/uncertainty. Blind human ratings when possible. Separate performance targets from observed measurements.

## Offline validation and summarization

Run the evaluator after collecting results. Keep the input manifest and results
with the private evidence they reference. The evaluator reads those two JSON
files and writes a stable summary to standard output.

```bash
python scripts/benchmark/summarize.py data/benchmark-inputs.json data/benchmark-results.json > data/benchmark-summary.json
.venv/bin/python -m pytest -q scripts/benchmark/test_summarize.py
```

Use `schema_version: 1` in both records. Set `evidence_kind` to `fixture` for
synthetic schema tests or `measured` for an executed benchmark.
Do not change measured source records after a summary has been published.
The summary identifies the exact versions of the records by SHA-256.

| Record | Required fields |
|---|---|
| Manifest | A nonempty `samples` list. Each sample has a unique `id` and lowercase `input_sha256`, a `category`, boolean `held_out: true`, boolean `license_approved: true` and an identifiable `rights_reference`. |
| Results | The manifest's byte-for-byte `input_manifest_sha256`, a `run` record and a nonempty `attempts` list. |
| Run | `id`, `source_revision`, `model_revision`, `checkpoint_sha256`, `runtime_sha256`, hardware description in `hardware`, timezone-qualified ISO 8601 `started_at`, and a JSON `parameters` object for settings shared by all attempts. |
| Every attempt | `sample_id`, consecutive `attempt_index` starting at 1, `outcome`, `seed`, `latency_ms`, `gpu_ms`, `peak_vram_mib`, `artist_correction_seconds` and `cost_microusd`. All counters use nonnegative integers. Record `compute`, `storage` and `other` cost separately in millionths of a dollar, using zero only for known zero cost. |
| Failed attempt | `outcome: "failed"`, `failure_stage` and `reason`. Include `output_sha256` if an output existed. A failed render or validation that prevented scoring belongs here. |
| Rated attempt | `outcome: "accepted"` or `"rejected"`, `output_sha256`, front/side/back render digests in `view_sha256`, `structural_glb_passed`, `blender_import_passed`, `rating_notes` and `quality_scores`. Both checks must pass for acceptance. A rejected output also requires a `reason`. |

Score `geometry`, `materials`, `hidden_view_consistency` and `usability` from
1 to 5. Use 1 when the observed output is unusable for that dimension, 3 for
usable with significant correction and 5 for ready in the declared target
workflow. Record criteria, reviewer notes and expected hardware or importer
differences before comparing runs. The evaluator checks for the rights and
validation references. The operator must verify the legal evidence, artifact
bytes, technical measurements and rubric ratings.

Include failures and rejected outputs in the attempts. Every frozen sample
must have at least one attempt. A sample can be retried until one result is
accepted. The summary reports overall and per-category samples and
acceptances, attempt outcomes and failure stages, nearest-rank P50/P95 latency
across all attempts, and score sums with the number of rated attempts. Total
cost includes every attempt, and retry cost is the portion from attempts after
the first. Cost per accepted asset divides total cost by accepted samples and
rounds to the nearest millionth of a dollar. Runs with zero accepted samples
report this amount as JSON `null`. Invalid or incomplete records exit with
status 2 and produce no summary.

The CPU tests validate fixture records only. A measured benchmark still
requires approved inputs, a qualified runtime, artifact checks and resource
authorization.

## Proposed release gates

First release: at least 100 end-to-end runs with recorded success/failure, importable GLB and cross-account privacy tests. Aspirational valid-job success target is 95%+ for supported inputs; it is **not an observed result**. Every future feature needs its own downstream test.
