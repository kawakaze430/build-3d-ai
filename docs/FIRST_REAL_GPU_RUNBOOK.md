# First Real GPU Qualification Runbook — TripoSR Candidate

**Status: BLOCKED / DO NOT EXECUTE until the owner approves both the exact runtime/license verdict and the GPU budget.**

This runbook prepares the smallest useful real-generation qualification. It does **not** approve TripoSR for production and it does not authorize cloud spend. The repository's model approval file must remain empty until the exact runtime below is cleared.

## Why this candidate

The stock Step1X-3D and TripoSG runtime paths currently fail this project's worldwide-commercial dependency gate. TripoSR is a more promising **qualification candidate** because its inspected source and published checkpoint are MIT-labeled, the model card describes a curated Objaverse training subset as CC-BY, and the published README reports about 6 GB VRAM for a single image.

That top-level evidence is still insufficient for production approval. The stock TripoSR environment contains an unpinned Git dependency on torchmcubes, the inspected historical torchmcubes snapshot did not contain a repository license file, and the model checkpoint is a Python/PyTorch pickle-style file. A real run must therefore use an exact reviewed fork/container and the exact checkpoint hash below.

## Frozen upstream evidence

| Item | Pinned evidence | Status |
|---|---|---|
| TripoSR source | `VAST-AI-Research/TripoSR@107cefdc244c39106fa830359024f6a2f1c78871` | MIT-labeled source; **candidate only** |
| TripoSR model repo | `stabilityai/TripoSR@2ba2f5591f8eb0821784764ab9ab99a12e1abb08` | MIT-labeled model card; **candidate only** |
| `model.ckpt` | 1,677,246,742 bytes; SHA256 `429e2c6b22a0923967459de24d67f05962b235f79cde6b032aa7ed2ffcd970ee` | exact approved-hash candidate; pickle checkpoint, load only in isolated trusted runtime |
| DINO config | `facebook/dino-vitb16@fdc136b8ef48f5a94159af5dd6323ae7a219697a/config.json` | Apache-2.0 model repository; TripoSR uses the ViT config shape |
| xatlas-python | `mworchel/xatlas-python@ff6541ec7ed1b5131dd7bf5447da6174e6c82621` (v0.0.9) | MIT; stock `export()` writes OBJ |
| TripoSR stock torchmcubes requirement | unpinned `git+https://github.com/tatsy/torchmcubes.git` | **not cleared for deterministic commercial runtime** |
| TripoSR-scikit patch evidence | `vltmedia/TripoSR-scikit@fa39422b81217687f16efe7bb3afc136feb87ba7` | MIT fork; only 2 commits ahead of its 2024 merge base and 17 commits behind current TripoSR, so do **not** use the whole fork as the base |
| scikit-image candidate | `scikit-image==0.26.0` | BSD-3-Clause stable release; Python >=3.11; exact numerical/orientation compatibility still requires a candidate-runtime test |

References:
- https://github.com/VAST-AI-Research/TripoSR
- https://huggingface.co/stabilityai/TripoSR/tree/2ba2f5591f8eb0821784764ab9ab99a12e1abb08
- https://huggingface.co/facebook/dino-vitb16/tree/fdc136b8ef48f5a94159af5dd6323ae7a219697a
- https://github.com/mworchel/xatlas-python/tree/ff6541ec7ed1b5131dd7bf5447da6174e6c82621

## CPU-only work completed before the GPU gate

The gateway now includes `build3d-pack-textured-glb`. It accepts the narrow xatlas-python single-mesh OBJ dialect plus a baked PNG and emits a self-contained GLB 2.0 containing:

- embedded geometry;
- embedded PNG image in the BIN chunk;
- `TEXCOORD_0`;
- optional normals;
- a metallic-roughness PBR material using the baked image as base color;
- no external MTL, image, buffer or network references.

The parser rejects external OBJ material directives, non-triangle faces, negative/aliased indices, oversized inputs and malformed PNG dimensions. Output is written atomically and rerun through the same structural GLB validator used by product downloads.

This closes the **packaging** gap discovered in TripoSR's stock texture path: TripoSR calls xatlas-python's `export()`, but that helper writes OBJ syntax. It does not prove UV orientation or visual texture correctness; the first real Blender/browser import must check those visually. `--flip-v` exists only as an explicit qualification option and is never silently applied.

Example CPU-only packaging command after a candidate texture bake exists:

```bash
build3d-pack-textured-glb   ./output/0/mesh.obj   ./output/0/texture.png   ./output/0/mesh-textured.glb
```

## Remaining runtime blocker before any GPU start

Create and review an exact TripoSR runtime fork/container that:

1. pins every Python/CUDA dependency and base image digest;
2. replaces or otherwise clears the stock unpinned/historically ambiguous torchmcubes dependency;
3. pins the DINO config download to `fdc136b8ef48f5a94159af5dd6323ae7a219697a`;
4. disables automatic background-removal model downloads for the first test by using `--no-remove-bg` and a pre-cropped, rights-cleared input;
5. downloads TripoSR only at revision `2ba2f5591f8eb0821784764ab9ab99a12e1abb08`;
6. verifies `model.ckpt` SHA256 **before** loading it;
7. runs the checkpoint only in the isolated model container; never load arbitrary user-supplied PyTorch checkpoints;
8. emits baked OBJ + PNG and then uses the first-party GLB packager above;
9. verifies the final GLB with `build3d-gpu-smoke` / product validation before publication.

A concrete reuse path now exists: `vltmedia/TripoSR-scikit@fa39422b81217687f16efe7bb3afc136feb87ba7` is MIT and replaces torchmcubes with `skimage.measure.marching_cubes`, including a face-winding adjustment. GitHub comparison shows that fork is **17 current-upstream commits behind**, so it must not replace the current TripoSR base. Port only the minimal marching-cubes change onto the pinned current source with attribution, pin `scikit-image==0.26.0` (BSD-3-Clause), and test numerical orientation/scale against the original behavior before GPU qualification.

## Proposed first GPU envelope — requires owner approval

Provider: AWS EC2  
Region: `us-east-1` (N. Virginia), unless the owner chooses another allowed region  
Instance: `g6.xlarge`  
GPU: 1 × NVIDIA L4, 24 GB VRAM  
System memory: 16 GiB  
vCPU: 4  
Published TripoSR expectation: ~6 GB VRAM for one image  
Observed public on-demand compute price near the research date: approximately **$0.8048/hour** in `us-east-1`.

Price must be rechecked from AWS immediately before launch. Storage, public IPv4, data transfer, tax and support are separate.

Proposed hard limits for the first run:

- maximum instance lifetime: **60 minutes**;
- maximum approved EC2 compute charge: **$1.00** for the instance itself;
- total experiment cap including storage/network cushion: **$3.00**;
- one image only;
- no retries after a model/infrastructure failure without reviewing the failure first;
- no Spot instance for the first qualification;
- automatic shutdown/termination command prepared before inference begins.

These are proposed limits, not authorization.

## Network and credential boundary

- Do not expose the model runtime to the public internet.
- Prefer SSM or a tightly scoped operator path rather than a world-open SSH security group.
- Keep the inference service on a private/loopback interface behind the existing authenticated gateway.
- Do not place AWS credentials, upstream bearer tokens, model-policy signing material or product operator keys in browser code.
- Use an instance role / short-lived AWS credentials where possible.
- Log model revision, checkpoint hash and container/image digest, but never log secrets.

## Input for the first real test

Use one deterministic, owner-controlled image with clear commercial rights. For the first TripoSR qualification, prepare it before launch as a centered RGB image with the gray/background framing expected by `--no-remove-bg`.

Record before upload:

```bash
sha256sum ./qualification-input.png
python - <<'PY'
from PIL import Image
p = "qualification-input.png"
im = Image.open(p)
print({"format": im.format, "mode": im.mode, "size": im.size})
PY
```

Do not use a celebrity/real-person likeness or an asset with uncertain rights for the first commercial-runtime qualification.

## Setup commands — prepare only after runtime fork is reviewed

The exact container digest and requirements lock are intentionally placeholders until the runtime fork removes the torchmcubes blocker. Do not replace them with `main` or floating package versions.

```bash
git clone https://github.com/VAST-AI-Research/TripoSR.git
cd TripoSR
git checkout 107cefdc244c39106fa830359024f6a2f1c78871
git status --short

# Apply only the reviewed Build 3D AI runtime patchset.
# Then build the exact pinned container and record its immutable image digest.
```

Checkpoint retrieval after owner/license approval:

```bash
hf download hf://stabilityai/TripoSR@2ba2f5591f8eb0821784764ab9ab99a12e1abb08/model.ckpt \
  --local-dir ./approved-model
echo "429e2c6b22a0923967459de24d67f05962b235f79cde6b032aa7ed2ffcd970ee  ./approved-model/model.ckpt" | sha256sum -c -
```

**Do not load the checkpoint if the hash check fails.**

Candidate inference shape after the deterministic runtime patch is complete:

```bash
python run.py ./qualification-input.png \
  --pretrained-model-name-or-path ./approved-model   --no-remove-bg   --bake-texture   --texture-resolution 2048   --model-save-format obj   --output-dir ./qualification-output

build3d-pack-textured-glb \
  ./qualification-output/0/mesh.obj \
  ./qualification-output/0/texture.png \
  ./qualification-output/0/mesh-textured.glb
```

The exact output subdirectory names must be confirmed against the pinned runtime before execution.

## Required measurements

Capture all of the following in one immutable experiment record:

- source commit and runtime-fork commit;
- container/base-image digest;
- exact dependency lock;
- model repository revision and `model.ckpt` SHA256;
- DINO config revision;
- input image SHA256, dimensions and rights/provenance note;
- full generation parameters and marching-cubes resolution;
- random seed where the runtime exposes one; if no seed exists, record that explicitly;
- AWS region, instance ID/type and GPU model;
- driver/CUDA/PyTorch versions;
- peak GPU VRAM;
- model initialization time;
- inference time;
- texture-bake time;
- GLB packaging time;
- total wall-clock time;
- GLB byte size, SHA256, mesh/primitive/material counts;
- vertex/triangle counts;
- browser viewer result and screenshots;
- Blender import result and screenshots from multiple angles;
- UV orientation/material correctness;
- failures and every retry;
- instance launch/termination timestamps and actual AWS cost.

## Acceptance sequence

The first real vertical slice is successful only if all steps are real and traceable:

```text
rights-cleared input
→ pinned private TripoSR candidate runtime
→ real GPU inference
→ baked UV OBJ + PNG
→ first-party embedded textured GLB
→ gateway structural/checksum validation
→ product artifact/storage path
→ owner-scoped browser viewer/download
→ Blender glTF import
→ measured cost/VRAM/timing report
→ cloud resource terminated
```

A valid GLB alone is not model-quality acceptance. Texture mirroring, seams, holes, backside geometry, normals, scale/orientation and Blender/browser visual agreement must be reviewed.

## Stop conditions

Stop immediately and terminate the instance if:

- checkpoint/config hash or revision differs;
- runtime needs an unreviewed model/weight download;
- dependency resolution escapes the pinned lock;
- GPU/driver mismatch requires ad-hoc package upgrades;
- output contains unexpected external resources;
- GLB validator fails;
- VRAM suggests the chosen instance is unsuitable;
- spend approaches the approved cap;
- any license/runtime provenance assumption changes.

## Cleanup

After the single run:

1. copy only the approved benchmark report/artifact evidence to the intended private location;
2. terminate the EC2 instance, not merely stop the inference process;
3. remove temporary public IP/security-group rules if any were created;
4. remove temporary volumes/snapshots unless the owner explicitly approved retention;
5. rotate any credential accidentally exposed to the instance shell/logs;
6. record final provider cost and termination evidence;
7. do not add the model to production approval until the complete result and license chain are reviewed.

## Current gate summary

- CPU product/gateway/browser/storage foundations: implemented and tested.
- Textured GLB packaging adapter: implemented with synthetic tests wired into Gateway/Product CI; merge only while those checks remain green.
- TripoSR source/model: promising research candidate, **not production approved**.
- Deterministic TripoSR runtime fork: **blocked/open**.
- GPU owner approval: **not granted in this session**.
- Real generation/Blender proof: **not executed**.
