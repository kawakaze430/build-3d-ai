from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).with_name("prepare_runtime.py")
SPEC = importlib.util.spec_from_file_location("triposr_prepare_runtime", MODULE_PATH)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def test_git_blob_id_matches_git_format():
    assert module.git_blob_id(b"hello\n") == "ce013625030ba8dba906f756967f9e9ca394464a"


def test_checked_replace_is_fail_closed():
    assert module.checked_replace("a b c", "b", "x", "test") == "a x c"
    for source in ("a c", "b b"):
        try:
            module.checked_replace(source, "b", "x", "test")
        except RuntimeError:
            pass
        else:
            raise AssertionError("ambiguous/missing source fragment must be rejected")


def test_reviewed_blob_inventory_contains_all_patched_upstream_files():
    expected = {
        "requirements.txt",
        "run.py",
        "tsr/utils.py",
        "tsr/system.py",
        "tsr/models/isosurface.py",
        "tsr/models/tokenizers/image.py",
    }
    assert set(module.EXPECTED_BLOBS) == expected
    assert all(len(value) == 40 for value in module.EXPECTED_BLOBS.values())


def commit_tree(source: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    git = ["git", "-C", str(source)]
    subprocess.run([*git, "init", "-q"], check=True)
    subprocess.run([*git, "add", "--all"], check=True)
    subprocess.run(
        [
            *git, "-c", "core.hooksPath=/dev/null", "-c", "commit.gpgsign=false",
            "-c", "user.name=Qualification fixture", "-c", "user.email=fixture@example.invalid",
            "commit", "-qm", "Reviewed fixture",
        ],
        check=True,
    )
    monkeypatch.setattr(module, "UPSTREAM_COMMIT", module.source_head(source))


def test_prepare_uses_only_pinned_regular_files(tmp_path, monkeypatch):
    source = tmp_path / "source"
    source.mkdir()
    (source / ".gitignore").write_text("ignored-*.txt\n")
    observed = source / "run.py"
    observed.write_bytes(b"# reviewed source\n")
    observed.chmod(0o755)
    commit_tree(source, monkeypatch)
    monkeypatch.setattr(module, "EXPECTED_BLOBS", {"run.py": module.git_blob_id(observed.read_bytes())})
    monkeypatch.setattr(module, "apply_patches", lambda destination: None)

    observed.write_text("# changed in the checkout\n")
    (source / "ignored-local.txt").write_text("local only")
    (source / "ignored-link.txt").symlink_to(tmp_path / "outside.txt")
    destination = tmp_path / "prepared"
    destination.mkdir()
    module.prepare(source, destination)

    assert {item.name for item in destination.iterdir()} == {".gitignore", "run.py"}
    assert (destination / "run.py").read_bytes() == b"# reviewed source\n"
    assert (destination / "run.py").stat().st_mode & 0o777 == 0o755


def test_prepare_rejects_tracked_symlinks_without_publishing_output(tmp_path, monkeypatch):
    source = tmp_path / "source"
    source.mkdir()
    (tmp_path / "outside.txt").write_text("outside the checkout")
    (source / "tracked-link").symlink_to("../outside.txt")
    commit_tree(source, monkeypatch)
    destination = tmp_path / "prepared"

    with pytest.raises(RuntimeError, match="unsupported Git entry"):
        module.prepare(source, destination)

    assert not destination.exists()
    assert list(tmp_path.glob(".triposr-prepare-*")) == []


def test_prepare_rejects_wrong_blob_and_destination_inside_checkout(tmp_path, monkeypatch):
    source = tmp_path / "source"
    source.mkdir()
    (source / "run.py").write_text("# reviewed source\n")
    commit_tree(source, monkeypatch)
    monkeypatch.setattr(module, "EXPECTED_BLOBS", {"run.py": "0" * 40})
    destination = tmp_path / "prepared"
    destination.mkdir()

    with pytest.raises(RuntimeError, match="upstream file drift"):
        module.prepare(source, destination)
    assert list(destination.iterdir()) == []

    with pytest.raises(RuntimeError, match="outside the source checkout"):
        module.prepare(source, source / "output")
    assert not (source / "output").exists()

    subdirectory = source / "subdir"
    subdirectory.mkdir()
    with pytest.raises(RuntimeError, match="checkout root"):
        module.prepare(subdirectory, source / "output")

    linked_destination = tmp_path / "linked"
    linked_destination.symlink_to(destination, target_is_directory=True)
    with pytest.raises(RuntimeError, match="must not be a symlink"):
        module.prepare(source, linked_destination)

    monkeypatch.setattr(module, "UPSTREAM_COMMIT", "0" * 40)
    with pytest.raises(RuntimeError, match="unexpected TripoSR revision"):
        module.prepare(source, destination)
