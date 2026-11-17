# TripoSR artifact and rights evidence

On 18 November 2026, the CPU review selected 33 concrete wheels for a CPython 3.10 Linux x86-64 target with glibc 2.35 compatibility. That platform is a resolver target based on the Ubuntu 22.04 base metadata. The interpreter and ABI installed in the image still need inspection. The selection uses the current candidate's 12 direct pins and a locally built wheel for its ANTLR dependency.

The [artifact record](TRIPOSR_ARTIFACT_EVIDENCE.json) identifies each selected file, its byte count, digest, origin and declared license metadata. It records independent byte verification for 25 wheels totaling 6,605,576 bytes, including the local ANTLR wheel. That verification used a 1 MiB cap per file and checked byte counts and SHA-256. The eight remaining wheels total 114,638,940 bytes and have index digests only. Notice paths and hashes record files identified by name in the verified wheel ZIPs. Native entries identify files present in those ZIPs. Neither list identifies linked system libraries or clears bundled code.

Reproduce the selection with uv 0.13.6 from the repository root, using a directory containing only the reviewed local ANTLR wheel:

```bash
uv --system-certs --no-config pip compile \
  --no-managed-python --no-python-downloads --python-version 3.10 \
  --python-platform x86_64-manylinux_2_35 --only-binary :all: \
  --default-index https://pypi.org/simple --find-links /path/to/verified-wheel-dir \
  services/generation/triposr_candidate/requirements-build3d.txt
```

The index can change. Before considering these inputs for release, use the exact filenames in the artifact record and check each byte count and digest against the recorded values. A mismatch or missing artifact requires renewed review. The candidate Dockerfile still resolves from its qualification pins. The artifact record is evidence for a proposed wheelhouse and does not control that build.

## ANTLR source archive

OmegaConf 2.3.0 requires `antlr4-python3-runtime==4.9.*`. PyPI provides 4.9.3 as a source archive. A real pip dry-run for that pin produced the source archive entry. The existing auditor reported the blocker and `--require-wheels` exited 2 without writing a release report. The candidate's index workflow retains that behavior.

The published archive contains a setuptools setup file and Python package files. The setup file lists the package and script inputs, declares BSD and includes only a conditional `typing` requirement for Python earlier than 3.5. The archive and resulting wheel lack a standalone license file. The [license at the exact upstream 4.9.3 commit](https://github.com/antlr/antlr4/blob/e4c1a74c66bd5290364ea2b36c97cd724b247357/LICENSE.txt) contains BSD-3-Clause and accompanying third-party notices. Preserve that full notice alongside any redistributed binary and review its applicability against the exact artifact.

From a trusted CPython 3.12.14 Linux environment whose `venv` bundles pip 25.0.1, download these three small files from their PyPI release pages. Use the same interpreter, zlib and tool versions if the output hash differs on another builder. [ANTLR release](https://pypi.org/project/antlr4-python3-runtime/4.9.3/#files) · [setuptools release](https://pypi.org/project/setuptools/75.8.0/#files) · [wheel release](https://pypi.org/project/wheel/0.45.1/#files)

```bash
sha256sum --check <<'SHA256'
f224469b4168294902bb1efa80a8bf7855f24c99aef99cbefc1bcd3cce77881b  antlr4-python3-runtime-4.9.3.tar.gz
e3982f444617239225d675215d51f6ba05f845d4eec313da4418fdbb56fb27e3  setuptools-75.8.0-py3-none-any.whl
708e7481cc80179af0e556bbf0cc00b8444c7321e2700b8d8580231d13017248  wheel-0.45.1-py3-none-any.whl
SHA256
```

Continue only after all three checks succeed. Run the build in an isolated temporary directory without external credentials or network access:

```bash
python -m venv build-venv
build-venv/bin/python -m pip --version
build-venv/bin/python -m pip install --no-index --no-deps \
  setuptools-75.8.0-py3-none-any.whl wheel-0.45.1-py3-none-any.whl
SOURCE_DATE_EPOCH=1633564800 PYTHONHASHSEED=0 TZ=UTC LC_ALL=C.UTF-8 \
  build-venv/bin/python -m pip wheel --no-index --no-deps --no-build-isolation \
  --wheel-dir wheel-output antlr4-python3-runtime-4.9.3.tar.gz
sha256sum --check <<'SHA256'
50f2b7f0ee7522778df794525fd812ade4079e96b101cf9f83145649738ea95d  wheel-output/antlr4_python3_runtime-4.9.3-py3-none-any.whl
SHA256
```

Two fresh build environments produced this same 144,591-byte wheel. The reviewed wheel installed offline with the verified OmegaConf 2.3.0 wheel and the CPython 3.12 PyYAML 6.0.3 wheel (SHA-256 `ba1cc08a7ccde2d2ec775841541641e4548226580ab850948cbfda66a1befcdc`). Dependency consistency and an OmegaConf YAML interpolation using ANTLR both passed. Qualification still needs to verify the candidate interpreter, retain the notice and stage the wheel in a separately verified offline wheelhouse.

## Base image and rights

| Evidence | Observed result | Open release work |
|---|---|---|
| Docker Hub Linux/amd64 base | Manifest SHA-256 `11691e035a3651d25a87116b4f6adc113a27a29d8f5a6a583f8569e0ee5ff897` checked against 1,366 registry bytes. Config SHA-256 `bbb9480407512d12387d74a66e1d804802d1227898051afa108a2796e2a94189` checked against 4,372 registry bytes. The config says Ubuntu 22.04 and records PyTorch 2.2.1 and CUDA 12.1.1 build inputs. [Base image manifest](https://hub.docker.com/layers/pytorch/pytorch/2.2.1-cuda12.1-cudnn8-runtime/images/sha256-11691e035a3651d25a87116b4f6adc113a27a29d8f5a6a583f8569e0ee5ff897) | Five layer blobs totaling 3,660,023,501 compressed bytes remain unpulled. Python/Conda packages, CUDA/cuDNN/Triton and OS/library versions and notices must be inspected in the image. Obtain NVIDIA and OS redistribution evidence, and record the resulting candidate's immutable digest. |
| TripoSR source and narrow marching-cubes patch | The upstream MIT license at `107cefdc244c39106fa830359024f6a2f1c78871` and MIT patch-source license at `fa39422b81217687f16efe7bb3afc136feb87ba7` have the same SHA-256 `ade0a66629bdd7e01e46b3296b3851cff0fd27989bca53da470ad6e96ed620fb`. [Upstream notice](https://github.com/VAST-AI-Research/TripoSR/blob/107cefdc244c39106fa830359024f6a2f1c78871/LICENSE) · [Patch-source notice](https://github.com/vltmedia/TripoSR-scikit/blob/fa39422b81217687f16efe7bb3afc136feb87ba7/LICENSE) | Preserve both source provenance records and the license in prepared outputs. |
| Python wheel notices and native dependencies | Seven verified wheels contain native entries, including ModernGL, glcontext and the xatlas binding. The selected xatlas wheel includes a LICENSE file even though PyPI does not declare a license field for that release. | Verify the remaining wheel bytes and notices. Determine ELF linkage, bundled libraries and obligations for OpenGL/EGL/X11 drivers and wrappers, codecs and the FFmpeg executable, NumPy/SciPy and numerical libraries, Pillow codecs, scikit-image, tokenizers and other native wheels. Package license labels alone do not resolve those obligations. |
| PyTorch source notice | PyTorch v2.2.1 resolves to `6c8c5ad5eaf47a62fafbb4a2747198cbffbf1ff0`. Its source license SHA-256 is `d63aaf3622186b2a761832a5704edeef1f25d08f5b9c50ac4e435befc8e348a8`. [Exact source notice](https://github.com/pytorch/pytorch/blob/6c8c5ad5eaf47a62fafbb4a2747198cbffbf1ff0/LICENSE) | Establish the correspondence between the binary/image distributions and all associated notices and licenses. |
| Checkpoint, DINO configuration and data rights | The pinned identities and expected checkpoint SHA-256 remain in the [runtime manifest](../../services/generation/triposr_candidate/runtime_manifest.json). The earlier license review records the model card's MIT label and its statement about a curated CC-BY Objaverse subset. This environment received HTTP 403 for the exact Hugging Face metadata URLs. | Verify exact model/config notices against an authorized source, and determine training asset attribution and geographic, commercial SaaS, redistribution and generated-output rights. Keep the checkpoint unstaged until rights and resource approvals permit verification. |

The evidence advances BE-02. The full wheelhouse, base-layer inventories, immutable candidate image and owner/legal decision remain open. The production approval list remains empty.

## PR #26 disposition

The remote PR head `712920893d9c9ba139c935605af5a89d2cfccaf0` introduced 11 changed paths relative to `477b3bff3fd5449dba1d1dd7a9e4e062f99856a3`. Both auditor files are byte-identical to the copies on main. The workflow's test, resolver, index-audit and artifact-upload steps are already on main. Its eight changed documents either have current equivalents in the candidate README, runbook, handoff and checklist, or survive as four byte-identical historical research documents. No missing implementation from the PR was identified. Treat the PR as superseded for code integration and retain it as a provenance reference. [PR #26](https://github.com/kawakaze430/build-3d-ai/pull/26) · [Recovery record](../../AnalyseFuture/repository-inventory/RECOVERED_BRANCH_FILES.json)
