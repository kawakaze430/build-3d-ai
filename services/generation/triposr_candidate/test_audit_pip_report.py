"""CPU-only tests; fixture SHA values are intentionally synthetic, not verified wheels."""
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("audit_pip_report.py")
SPEC = importlib.util.spec_from_file_location("triposr_pip_audit", MODULE_PATH)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def package(name: str, version: str, *, sha: str = "a" * 64, url: str | None = None) -> dict:
    return {
        "metadata": {"name": name, "version": version},
        "download_info": {
            "url": url or f"https://files.pythonhosted.org/packages/{name}-{version}-py3-none-any.whl",
            "archive_info": {"hashes": {"sha256": sha}},
        },
        "is_yanked": False,
    }


def report(*entries: dict) -> dict:
    return {
        "version": "1",
        "install": list(entries),
        "environment": {
            "python_version": "3.10",
            "sys_platform": "linux",
            "platform_machine": "x86_64",
            "platform_system": "Linux",
        },
    }


class ReportAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.pins = module.parse_pins("Pillow==10.1.0\nomegaconf==2.3.0\n")
        self.good = report(
            package("Pillow", "10.1.0"),
            package("omegaconf", "2.3.0"),
            package("antlr4-python3-runtime", "4.9.3"),
        )

    def inspect(self, value: dict) -> dict:
        return module.inspect_report(value, self.pins, b"report", b"pins")

    def test_inventory_is_sorted_and_labels_unverified_provenance(self):
        result = self.inspect(self.good)
        self.assertEqual(result["resolved_wheel_count"], 3)
        self.assertEqual(result["direct_requirement_count"], 2)
        self.assertEqual([x["name"] for x in result["packages"]], [
            "antlr4-python3-runtime", "omegaconf", "pillow"
        ])
        self.assertFalse(result["packages"][0]["direct_requirement"])
        self.assertIn("NOT_A_WHEELHOUSE", result["status"])

    def test_requirements_must_be_exact_and_nonduplicated(self):
        for invalid in ("Pillow>=10", "-e foo", "requests @ https://example.com", "--index-url x", "Pillow==10\npillow==10"):
            with self.subTest(invalid=invalid), self.assertRaises(module.AuditError):
                module.parse_pins(invalid)

    def test_duplicate_normalized_package_is_rejected(self):
        entries = self.good["install"] + [package("antlr4_python3.runtime", "4.9.3")]
        with self.assertRaisesRegex(module.AuditError, "duplicate normalized"):
            self.inspect(report(*entries))

    def test_direct_pin_mismatch_is_rejected(self):
        entries = [package("Pillow", "10.0.0"), *self.good["install"][1:]]
        with self.assertRaisesRegex(module.AuditError, "mismatched direct pin"):
            self.inspect(report(*entries))

    def test_missing_or_malformed_hash_is_rejected(self):
        for digest in ("", "not-a-sha", "f" * 63):
            entries = [package("Pillow", "10.1.0", sha=digest), *self.good["install"][1:]]
            with self.subTest(digest=digest), self.assertRaisesRegex(module.AuditError, "missing SHA256"):
                self.inspect(report(*entries))

    def test_untrusted_urls_sources_and_credentials_are_rejected(self):
        urls = [
            "http://files.pythonhosted.org/p.whl",
            "https://evil.example/p.whl",
            "https://user:password@files.pythonhosted.org/p.whl",
            "file:///tmp/p.whl",
            "https://files.pythonhosted.org/not-a-package.exe",
            "https://files.pythonhosted.org/p.whl?token=secret",
        ]
        for url in urls:
            entries = [package("Pillow", "10.1.0", url=url), *self.good["install"][1:]]
            with self.subTest(url=url), self.assertRaises(module.AuditError):
                self.inspect(report(*entries))

    def test_source_archive_is_visible_blocker_and_release_mode_rejects_it(self):
        value = report(
            package("Pillow", "10.1.0"),
            package("omegaconf", "2.3.0"),
            package(
                "antlr4-python3-runtime", "4.9.3",
                url="https://files.pythonhosted.org/packages/antlr4-python3-runtime-4.9.3.tar.gz",
            ),
        )
        result = self.inspect(value)
        self.assertIn("BLOCKED_BY_SOURCE_ARCHIVES", result["status"])
        self.assertEqual(result["source_archive_count"], 1)
        self.assertEqual(result["resolved_wheel_count"], 2)
        self.assertEqual(result["source_archives_needing_reviewed_build"], [
            "antlr4-python3-runtime"
        ])
        with self.assertRaisesRegex(module.AuditError, "wheel-only release gate"):
            module.inspect_report(value, self.pins, b"report", b"pins", require_wheels=True)

    def test_yanked_or_missing_environment_is_rejected(self):
        value = report(*self.good["install"])
        value["install"][0]["is_yanked"] = True
        with self.assertRaises(module.AuditError):
            self.inspect(value)
        value = report(*self.good["install"])
        del value["environment"]["python_version"]
        with self.assertRaises(module.AuditError):
            self.inspect(value)

    def test_cli_refuses_existing_output_and_does_not_download(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            input_report = directory / "pip-report.json"
            requirements = directory / "requirements.txt"
            output = directory / "audit.json"
            input_report.write_text(json.dumps(self.good), encoding="utf-8")
            requirements.write_text("Pillow==10.1.0\nomegaconf==2.3.0\n", encoding="utf-8")
            argv = ["--report", str(input_report), "--requirements", str(requirements), "--output", str(output)]
            self.assertEqual(module.main(argv), 0)
            self.assertEqual(json.loads(output.read_text())["resolved_wheel_count"], 3)
            self.assertEqual(module.main(argv), 2)
            self.assertEqual(json.loads(output.read_text())["resolved_wheel_count"], 3)


if __name__ == "__main__":
    unittest.main()
