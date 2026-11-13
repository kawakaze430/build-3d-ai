# AI Model Strategy, Dataset and Fine-Tuning Program

## Starting plan

Don't train a foundation model from scratch. Start with **verified inference** using a legally permissible existing image-to-3D checkpoint. Use Step1X-3D training/LoRA code as an initial customization candidate; explore TRELLIS.2 and alternatives only after full dependency license clearance.

## Experiment sequence

1. **Baseline (no training):** evaluate real model results on fixed unseen inputs, record VRAM, GPU instance, latency, failure rates, geometry, texture and GLB size.
2. **Dataset build:** license-curated 3D assets including object geometry, materials, references, camera poses, style annotations, source and permitted use.
3. **Preprocessing:** normal orientation/scale, geometry validity, multi-view renders, texture maps, asset deduplication, model-specific representations, data manifests.
4. **First fine-tune:** small specialized LoRA or supported training recipe (e.g. stylized adult animated character meshes), track checkpoint/data/config and cost.
5. **Compare:** strict held-out evaluation; only keep a fine-tune that improves chosen production metrics without unacceptable regressions.
6. **Scale carefully:** larger specialized data and training only after budget approval and proven experiment benefits.
7. **Production:** versioned model registry, canary rollout, rollback and provenance on each generated asset.

Never claim generic image-model LoRA commands can train a specialized 3D architecture. Follow model-specific official preprocessing and training instructions.

## Data license and ethics

Record asset source URL, rights/attribution, permission for training and commercial use, derivative terms, model/data hash, consent when real likenesses are involved, and expiration/revocation where applicable. Public 3D data collections may contain mixed licenses; do per-asset filtering. Separate train/validation/test by **3D asset or identity**, not by multiple images of the same object.

## Quality and character specialization

The initial research wedge is reusable stylized adult characters (adult body proportions, expressive eyes without childlike proportion, clean face and clothing, consistent proportions, useful Blender export). Evaluate shape from all sides and deformation under rig, not only a pretty render. Target eye direction, blink, brows, jaw, mouth interior, visemes and face blendshapes as a **separate** facial rig pipeline.

A single input image cannot provide certain knowledge of the back of the model. Approximation should be clearly communicated.

## Hardware and budget

Codex creates training code, but dedicated GPU compute executes training. AWS is primary candidate (subject to service limits, credit eligibility and approval); Colab may help with research but is not a permanent public API host. Do not infer training VRAM requirements from inference VRAM. GPU jobs require maximum runtime, spend cap, logs, autosave and an exit criterion.

## Ownership and release

The product can own its fine-tune dataset and adaptation artifacts where legally permitted, but underlying third-party code/weights retain their licenses and rights. Record base checkpoint source and derivative obligations in every model card.
