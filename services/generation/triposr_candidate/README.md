# Deterministic TripoSR qualification patchset

**Status: qualification-only. No model is production-approved and this directory does not authorize GPU spend.**

This slice removes the known non-deterministic/hidden-download paths from the first TripoSR qualification candidate without vendoring the upstream project.

## What it does

`prepare_runtime.py` accepts only a clean checkout of:

- `VAST-AI-Research/TripoSR@107cefdc244c39106fa830359024f6a2f1c78871`

It verifies the Git blob ID of every upstream file it modifies, copies the source tree, then applies a narrow patchset:

- replaces the unpinned `torchmcubes` import with `scikit-image==0.25.2` marching cubes;
- applies the face-winding adjustment documented by the MIT `vltmedia/TripoSR-scikit` patch evidence;
- removes `rembg` from the first-run dependency path and requires `--no-remove-bg`;
- fixes the stock `--no-remove-bg` output-directory bug by creating `output/<index>` for every image;
- rejects remote model IDs; the checkpoint must be a local reviewed file;
- verifies the exact 1,677,246,742-byte `model.ckpt` SHA256 before `torch.load`;
- uses `torch.load(..., weights_only=True)` for the candidate state dict;
- replaces DINO config retrieval with a bundled local architecture config;
- sets Hugging Face / Transformers offline environment flags in the candidate container;
- replaces the stock requirements with qualification-only direct pins that contain no `torchmcubes`, `rembg` or `gradio`.

The source tree is still TripoSR and remains subject to its upstream MIT license. The small marching-cubes behavior change is based on separately reviewed MIT patch evidence; scikit-image 0.25.2 is BSD-3-Clause.

## Prepare — CPU/source operation only

```bash
git clone https://github.com/VAST-AI-Research/TripoSR.git /tmp/TripoSR
git -C /tmp/TripoSR checkout 107cefdc244c39106fa830359024f6a2f1c78871

python services/generation/triposr_candidate/prepare_runtime.py \
  --source-dir /tmp/TripoSR \
  --output-dir /tmp/TripoSR-build3d
```

Preparation stops if the source commit, source blob IDs, replacement fragments or runtime manifest differ from the reviewed values.

## Candidate container

`Dockerfile.candidate` references the Linux/amd64 manifest digest for
`pytorch/pytorch:2.2.1-cuda12.1-cudnn8-runtime`:

`sha256:11691e035a3651d25a87116b4f6adc113a27a29d8f5a6a583f8569e0ee5ff897`

That manifest digest was checked on Docker Hub on 15 Nov 2026. **The repository CI does not build this 3.4 GB candidate image yet**, so OS-library and texture-bake runtime compatibility remain an explicit gate.

scikit-image 0.25.2 is used instead of 0.26.0 because 0.25.2 supports Python >=3.10, matching the candidate-era PyTorch environment more conservatively; PyPI reports the package under BSD-3-Clause. The exact container interpreter is still verified at image-build time before approval.

## Model staging

The prepared runtime intentionally does not download weights. Stage only the pinned model checkpoint from:

`stabilityai/TripoSR@2ba2f5591f8eb0821784764ab9ab99a12e1abb08`

Required checkpoint:

- filename: `model.ckpt`
- bytes: `1677246742`
- SHA256: `429e2c6b22a0923967459de24d67f05962b235f79cde6b032aa7ed2ffcd970ee`

The runtime verifies both before loading. Arbitrary user checkpoints are not supported.

## What CI proves

The qualification workflow:

1. clones the exact TripoSR commit;
2. applies this patchset with source-blob guards;
3. checks that forbidden dependency/import paths are gone;
4. compiles the patched Python source;
5. resolves the direct candidate dependency set on CPU;
6. runs scikit-image axis/normalization and explicit face-winding contract tests.

It does **not** build the full GPU image, load the checkpoint, run CUDA, bake a real texture, prove torchmcubes numerical equivalence, prove Blender import, or clear the model/data/runtime legally for production.

## Remaining gate

Before the first GPU run:

- build and inspect the digest-pinned candidate image;
- record exact resolved transitive package/wheel hashes and bundled system libraries;
- confirm ModernGL/xatlas texture baking works headlessly in that image;
- confirm the exact checkpoint loads successfully with `weights_only=True`;
- obtain owner/legal approval for the exact source + model + runtime + data chain;
- obtain the bounded GPU budget approval in `docs/FIRST_REAL_GPU_RUNBOOK.md`.

No production model approval file is changed by this patchset.
