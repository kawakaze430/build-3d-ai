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

## Proposed release gates

First release: at least 100 end-to-end runs with recorded success/failure, importable GLB and cross-account privacy tests. Aspirational valid-job success target is 95%+ for supported inputs; it is **not an observed result**. Every future feature needs its own downstream test.
