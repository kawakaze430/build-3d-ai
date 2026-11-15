from __future__ import annotations

import importlib.util
from pathlib import Path

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
