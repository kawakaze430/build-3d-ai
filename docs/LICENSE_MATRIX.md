# Commercial License and Deployment Gate — Partial Review (2026-11-13)

**Status: NO MODEL APPROVED FOR PRODUCTION.** This is an evidence-based source/license inventory, not legal advice or completion of issue #2. A permissive app-repository license never clears upstream model weights, forked components, training assets, or transitive rendering dependencies.

| Component | Pinned upstream commit | Repository-level license checked | Commercial-release decision |
|---|---|---|---|
| [Open3DStudio](https://github.com/FishWoWater/Open3DStudio) | `f2e403eb11a2c33077e9f353fa240974edb06981` | Apache-2.0 ([LICENSE](https://github.com/FishWoWater/Open3DStudio/blob/main/LICENSE)) | Research-only until frontend dependencies, assets and build tested |
| [3DAIGC-API](https://github.com/FishWoWater/3DAIGC-API) | `9c5643f99cbfd8d47b81922790f0d0a36be57e81` | Apache-2.0 ([LICENSE](https://github.com/FishWoWater/3DAIGC-API/blob/main/LICENSE)) | Research-only: its `.gitmodules` includes separately licensed AI systems |
| [Step1X-3D](https://github.com/stepfun-ai/Step1X-3D) | `cb5ac944709c6c913109070c7b90c3447f57f3d4` | Apache-2.0 ([LICENSE](https://github.com/stepfun-ai/Step1X-3D/blob/main/LICENSE)) | Research-only: inspect actual weights and borrowed texture baking components |
| [TRELLIS.2](https://github.com/microsoft/TRELLIS.2) | `75fbf0183001ed9876c8dbb35de6b68552ee08bd` | MIT ([LICENSE](https://github.com/microsoft/TRELLIS.2/blob/main/LICENSE)) | **Do not use standard NVIDIA renderer path commercially** without permission or permitted replacement |
| [UniRig](https://github.com/VAST-AI-Research/UniRig) | `6793c6640ff01c8fb389f3993434124bb43d2933` | MIT (LICENSE) | Research-only pending pretrained weights, dependencies, functional test |
| [SkinTokens](https://github.com/VAST-AI-Research/SkinTokens) | `273b691d35989d71cd17ff2895fdc735097b92d1` | MIT (LICENSE) | Research-only pending weights and dependencies |
| [xatlas](https://github.com/jpcy/xatlas) | `f700c7790aaa030e794b52ba7791a05c085faf0c` | MIT (LICENSE) | Promising library; adapter, notices and dependent bindings still untested |
| [glTF Transform](https://github.com/donmccurdy/glTF-Transform) | Revision not pinned | MIT (LICENSE.md) | Promising library; exact installed version not selected |
| [NVIDIA PartField](https://github.com/nv-tlabs/PartField) | `373025dbd283bb44cc4a6dc78c99994dbc91de32` | NVIDIA-specific, §3.3 non-commercial research/education use | **BLOCKED** for commercial deployment without other permission |
| [Hunyuan3D-2.1](https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1) | `82920d643c0dc2f7bfd7255f45f62d386edfe60c` | Tencent Hunyuan 3D 2.1 Community License | **BLOCKED for worldwide service**: EU, UK, South Korea excluded; further hosted-service obligations |

## Explicit high-risk dependency evidence

1. [TRELLIS.2 README](https://github.com/microsoft/TRELLIS.2/blob/main/README.md) setup explicitly includes **nvdiffrast** and **nvdiffrec**.
2. [nvdiffrast LICENSE §3.3](https://github.com/NVlabs/nvdiffrast/blob/main/LICENSE.txt) limits use of the Work/derivatives to non-commercial research/evaluation.
3. [nvdiffrec LICENSE §3.3](https://github.com/NVlabs/nvdiffrec/blob/main/LICENSE.txt) similarly limits use to non-commercial research/evaluation.
4. [PartField LICENSE §3.3](https://github.com/nv-tlabs/PartField/blob/main/LICENSE) limits use to non-commercial research and education.
5. [Hunyuan3D-2.1 LICENSE](https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1/blob/main/LICENSE) expressly excludes the EU, UK and South Korea from its defined territory; it also has hosted-service and other conditions.
6. [3DAIGC-API .gitmodules](https://github.com/FishWoWater/3DAIGC-API/blob/main/.gitmodules) lists external/forked TRELLIS, PartField, PartPacker, Hunyuan3D, UniRig, FastMesh, PartUV, TRELLIS.2, Hunyuan3D-Part, UltraShape and VoxHammer; neither source license nor weight license follows automatically from the parent repo.

## Runtime integration policy

- The gateway defaults to **zero** approved runtime model IDs; any valid generation attempt returns HTTP 503 until an exact reviewed model entry is configured.
- A selected upstream model ID must match a reviewed entry and include the true upstream revision and weight checksum. Unknown models return HTTP 403.
- A model's claimed VRAM, supported features or output format in a README does not prove it works on our servers.
- **Operator attestation is required:** the approval file records review metadata but does not itself verify legal rights. Human/license review must cover dependencies, data, hosted use, geographic reach, and attribution.
- Production and customer-data access require separate authentication, tenant security, rate limits and credit accounting. This gateway is still private and single-operator.

## Needed before closing Issue #2

Audit license files of each **exact cloned submodule revision**, pretrained checkpoints and weights distribution pages, transitive runtime containers, npm packages, texture pipelines and datasets. Run verified clean-room build/tests of frontend and backend, document fork deltas, and select one commercially permitted baseline **end-to-end** GPU stack. That work is still open.
