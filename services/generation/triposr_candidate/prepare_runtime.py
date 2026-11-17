#!/usr/bin/env python3
"""Prepare the exact TripoSR qualification tree without model/GPU execution.

This script deliberately does not download weights, contact Hugging Face, build
containers, or run inference. It accepts only the reviewed TripoSR source
revision, verifies the exact upstream blobs we patch, copies the source tree,
then applies a small deterministic qualification-only patchset.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

UPSTREAM_COMMIT = "107cefdc244c39106fa830359024f6a2f1c78871"
CHECKPOINT_SHA256 = "429e2c6b22a0923967459de24d67f05962b235f79cde6b032aa7ed2ffcd970ee"
CHECKPOINT_BYTES = 1_677_246_742

# Git blob IDs from the exact reviewed upstream commit. Any upstream drift
# causes preparation to stop before a file is changed.
EXPECTED_BLOBS = {
    "requirements.txt": "c905bdb3540890d0af5382f984f48ef74d9a270c",
    "run.py": "1150529c1b9525c88e87dba44fa649129b1d2d95",
    "tsr/utils.py": "9758f2e44cd4091f2124929edc89b59e98fff667",
    "tsr/system.py": "bcdb69b2e5c85b3c0ffebd7ff82fc4fe7b3d543e",
    "tsr/models/isosurface.py": "076321b81f573ab95a6c7d5328f6366e0f33c38e",
    "tsr/models/tokenizers/image.py": "d4034b25a7b2e8f38630fd69a0bae75ed2a5edb0",
}


def git_blob_id(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode()
    return hashlib.sha1(header + data).hexdigest()


def checked_replace(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one exact source fragment, found {count}")
    return text.replace(old, new, 1)


def source_head(source: Path) -> str:
    try:
        completed = subprocess.run(
            ["git", "-C", str(source), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RuntimeError("source-dir must be an exact Git checkout") from exc
    return completed.stdout.strip()


def copy_reviewed_tree(source: Path, destination: Path) -> None:
    git = ["git", "--no-replace-objects", "-C", str(source)]
    tree = subprocess.check_output([*git, "ls-tree", "-r", "-z", "--full-tree", UPSTREAM_COMMIT])
    for entry in tree.split(b"\0")[:-1]:
        metadata, path_bytes = entry.split(b"\t", 1)
        mode, kind, blob = metadata.split()
        relative = path_bytes.decode("utf-8")
        if kind != b"blob" or mode not in {b"100644", b"100755"}:
            raise RuntimeError(f"unsupported Git entry for qualification: {relative}")
        if any(part in {"", ".", "..", ".git"} for part in relative.split("/")):
            raise RuntimeError(f"invalid Git path for qualification: {relative}")
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(subprocess.check_output([*git, "cat-file", "blob", blob.decode("ascii")]))
        target.chmod(0o755 if mode == b"100755" else 0o644)


def verify_upstream_blobs(source: Path) -> None:
    for relative, expected in EXPECTED_BLOBS.items():
        path = source / relative
        if not path.is_file():
            raise RuntimeError(f"missing reviewed upstream file: {relative}")
        actual = git_blob_id(path.read_bytes())
        if actual != expected:
            raise RuntimeError(
                f"upstream file drift for {relative}: expected {expected}, got {actual}"
            )


def patch_isosurface(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = checked_replace(
        text,
        "from torchmcubes import marching_cubes\n",
        "from skimage import measure\n",
        "isosurface import",
    )
    text = checked_replace(
        text,
        "self.mc_func: Callable = marching_cubes",
        "self.mc_func: Callable = measure.marching_cubes",
        "isosurface callable",
    )
    old = '''        try:
            v_pos, t_pos_idx = self.mc_func(level.detach(), 0.0)
        except AttributeError:
            print("torchmcubes was not compiled with CUDA support, use CPU version instead.")
            v_pos, t_pos_idx = self.mc_func(level.detach().cpu(), 0.0)
        v_pos = v_pos[..., [2, 1, 0]]
        v_pos = v_pos / (self.resolution - 1.0)
        return v_pos.to(level.device), t_pos_idx.to(level.device)
'''
    new = '''        volume = level.detach().cpu().numpy()
        v_pos_np, t_pos_idx_np, _, _ = self.mc_func(volume, level=0.0)
        # scikit-image returns coordinates in the input array axis order.
        # The reviewed TripoSR-scikit patch reverses face winding to preserve
        # the original mesh orientation after replacing torchmcubes.
        t_pos_idx_np = t_pos_idx_np[:, [1, 0, 2]]
        v_pos = torch.from_numpy(np.ascontiguousarray(v_pos_np)).to(
            device=level.device, dtype=torch.float32
        )
        t_pos_idx = torch.from_numpy(np.ascontiguousarray(t_pos_idx_np)).to(
            device=level.device, dtype=torch.long
        )
        v_pos = v_pos / (self.resolution - 1.0)
        return v_pos, t_pos_idx
'''
    text = checked_replace(text, old, new, "isosurface forward")
    path.write_text(text, encoding="utf-8")


def patch_utils(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = checked_replace(text, "import rembg\n", "", "utils rembg import")
    text = checked_replace(
        text,
        "    if do_remove:\n        image = rembg.remove(image, session=rembg_session, **rembg_kwargs)\n",
        '''    if do_remove:
        try:
            import rembg
        except ImportError as exc:
            raise RuntimeError(
                "Background removal is not installed in the Build3D qualification runtime"
            ) from exc
        image = rembg.remove(image, session=rembg_session, **rembg_kwargs)
''',
        "utils lazy rembg",
    )
    path.write_text(text, encoding="utf-8")


def patch_run(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = checked_replace(text, "import rembg\n", "", "run rembg import")
    text = checked_replace(
        text,
        "output_dir = args.output_dir\nos.makedirs(output_dir, exist_ok=True)\n\ndevice = args.device\n",
        '''output_dir = args.output_dir
os.makedirs(output_dir, exist_ok=True)

if not args.no_remove_bg:
    parser.error(
        "Build3D qualification runtime requires --no-remove-bg to prevent hidden model downloads"
    )
if not os.path.isdir(args.pretrained_model_name_or_path):
    parser.error(
        "--pretrained-model-name-or-path must be a local reviewed model directory"
    )

device = args.device
''',
        "run qualification guards",
    )
    text = checked_replace(
        text,
        '''if args.no_remove_bg:
    rembg_session = None
else:
    rembg_session = rembg.new_session()
''',
        '''rembg_session = None
''',
        "run rembg session",
    )
    text = checked_replace(
        text,
        '''for i, image_path in enumerate(args.image):
    if args.no_remove_bg:
''',
        '''for i, image_path in enumerate(args.image):
    item_output_dir = os.path.join(output_dir, str(i))
    os.makedirs(item_output_dir, exist_ok=True)
    if args.no_remove_bg:
''',
        "run output directory",
    )
    text = checked_replace(
        text,
        '''        if not os.path.exists(os.path.join(output_dir, str(i))):
            os.makedirs(os.path.join(output_dir, str(i)))
        image.save(os.path.join(output_dir, str(i), f"input.png"))
''',
        '''        image.save(os.path.join(item_output_dir, "input.png"))
''',
        "run duplicate output directory",
    )
    path.write_text(text, encoding="utf-8")


def patch_image_tokenizer(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = checked_replace(
        text,
        "from dataclasses import dataclass\n\nimport torch\n",
        "from dataclasses import dataclass\nfrom pathlib import Path\n\nimport torch\n",
        "image tokenizer pathlib",
    )
    text = checked_replace(
        text,
        "from huggingface_hub import hf_hub_download\n",
        "",
        "image tokenizer hub import",
    )
    old = '''        self.model: ViTModel = ViTModel(
            ViTModel.config_class.from_pretrained(
                hf_hub_download(
                    repo_id=self.cfg.pretrained_model_name_or_path,
                    filename="config.json",
                )
            )
        )
'''
    new = '''        config_path = (
            Path(__file__).resolve().parents[3]
            / "build3d_runtime"
            / "dino_config.json"
        )
        if not config_path.is_file():
            raise RuntimeError("Pinned local DINO config is missing")
        self.model: ViTModel = ViTModel(
            ViTModel.config_class.from_json_file(str(config_path))
        )
'''
    text = checked_replace(text, old, new, "image tokenizer local DINO config")
    path.write_text(text, encoding="utf-8")


def patch_system(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = checked_replace(
        text,
        "import math\nimport os\n",
        "import hashlib\nimport math\nimport os\nfrom pathlib import Path\n",
        "system imports",
    )
    text = checked_replace(
        text,
        "from huggingface_hub import hf_hub_download\n",
        "",
        "system hub import",
    )
    old = '''        if os.path.isdir(pretrained_model_name_or_path):
            config_path = os.path.join(pretrained_model_name_or_path, config_name)
            weight_path = os.path.join(pretrained_model_name_or_path, weight_name)
        else:
            config_path = hf_hub_download(
                repo_id=pretrained_model_name_or_path, filename=config_name
            )
            weight_path = hf_hub_download(
                repo_id=pretrained_model_name_or_path, filename=weight_name
            )

        cfg = OmegaConf.load(config_path)
        OmegaConf.resolve(cfg)
        model = cls(cfg)
        ckpt = torch.load(weight_path, map_location="cpu")
        model.load_state_dict(ckpt)
        return model
'''
    new = f'''        if not os.path.isdir(pretrained_model_name_or_path):
            raise RuntimeError("Build3D qualification runtime accepts only a local model directory")

        source_root = Path(__file__).resolve().parents[1]
        config_path = source_root / "build3d_runtime" / "model_config.yaml"
        weight_path = Path(pretrained_model_name_or_path) / weight_name
        if not config_path.is_file() or not weight_path.is_file():
            raise RuntimeError("Pinned local model config/checkpoint is missing")
        if weight_path.stat().st_size != {CHECKPOINT_BYTES}:
            raise RuntimeError("TripoSR checkpoint byte length does not match reviewed artifact")

        digest = hashlib.sha256()
        with weight_path.open("rb") as handle:
            while chunk := handle.read(8 * 1024 * 1024):
                digest.update(chunk)
        if digest.hexdigest() != "{CHECKPOINT_SHA256}":
            raise RuntimeError("TripoSR checkpoint SHA256 does not match reviewed artifact")

        cfg = OmegaConf.load(config_path)
        OmegaConf.resolve(cfg)
        model = cls(cfg)
        ckpt = torch.load(weight_path, map_location="cpu", weights_only=True)
        model.load_state_dict(ckpt)
        return model
'''
    text = checked_replace(text, old, new, "system local checkpoint")
    path.write_text(text, encoding="utf-8")


def write_runtime_assets(destination: Path) -> None:
    here = Path(__file__).resolve().parent
    runtime_dir = destination / "build3d_runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    for filename in ("model_config.yaml", "dino_config.json", "runtime_manifest.json"):
        shutil.copy2(here / filename, runtime_dir / filename)
    shutil.copy2(here / "requirements-build3d.txt", destination / "requirements-build3d.txt")
    shutil.copy2(here / "Dockerfile.candidate", destination / "Dockerfile.build3d-candidate")


def verify_prepared(destination: Path) -> None:
    requirements = (destination / "requirements-build3d.txt").read_text(encoding="utf-8")
    lowered = requirements.lower()
    for forbidden in ("torchmcubes", "rembg", "gradio"):
        if forbidden in lowered:
            raise RuntimeError(f"forbidden qualification dependency remains: {forbidden}")

    source_text = "\n".join(
        (destination / relative).read_text(encoding="utf-8")
        for relative in EXPECTED_BLOBS
        if relative.endswith(".py")
    )
    if "from torchmcubes" in source_text or "hf_hub_download(" in source_text:
        raise RuntimeError("prepared runtime still contains a forbidden hidden-download/runtime path")

    manifest = json.loads(
        (destination / "build3d_runtime" / "runtime_manifest.json").read_text(encoding="utf-8")
    )
    if manifest.get("triposr_source_commit") != UPSTREAM_COMMIT:
        raise RuntimeError("runtime manifest source revision mismatch")
    if manifest.get("checkpoint_sha256") != CHECKPOINT_SHA256:
        raise RuntimeError("runtime manifest checkpoint mismatch")


def prepare(source: Path, destination: Path) -> None:
    source = source.resolve()
    root = subprocess.check_output(
        ["git", "-C", str(source), "rev-parse", "--show-toplevel"], text=True,
    ).rstrip("\n")
    if Path(root).resolve() != source:
        raise RuntimeError("source-dir must be the checkout root")
    if destination.is_symlink():
        raise RuntimeError("output-dir must not be a symlink")
    destination = destination.resolve()
    if destination.is_relative_to(source):
        raise RuntimeError("output-dir must be outside the source checkout")
    if destination.exists() and (not destination.is_dir() or any(destination.iterdir())):
        raise RuntimeError("output-dir must be absent or empty")

    head = source_head(source)
    if head != UPSTREAM_COMMIT:
        raise RuntimeError(f"unexpected TripoSR revision: {head}")

    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".triposr-prepare-", dir=destination.parent) as staging:
        prepared = Path(staging) / "source"
        prepared.mkdir()
        copy_reviewed_tree(source, prepared)
        verify_upstream_blobs(prepared)
        apply_patches(prepared)
        prepared.rename(destination)


def apply_patches(destination: Path) -> None:
    # The original requirements file is intentionally replaced with the
    # qualification-only direct pins. The full transitive/wheel-hash lock is a
    # separate release gate and is not claimed by this file.
    shutil.copy2(
        Path(__file__).resolve().parent / "requirements-build3d.txt",
        destination / "requirements.txt",
    )
    patch_isosurface(destination / "tsr/models/isosurface.py")
    patch_utils(destination / "tsr/utils.py")
    patch_run(destination / "run.py")
    patch_image_tokenizer(destination / "tsr/models/tokenizers/image.py")
    patch_system(destination / "tsr/system.py")
    write_runtime_assets(destination)
    verify_prepared(destination)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        prepare(args.source_dir, args.output_dir)
    except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"qualification preparation failed: {exc}", file=sys.stderr)
        return 2
    print(f"prepared TripoSR qualification runtime at {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
