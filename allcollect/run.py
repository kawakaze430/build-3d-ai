"""Run browser acceptance against disposable SQLite and the real product API."""

import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

from PIL import Image

from build3d_api.config import Settings
from build3d_api.db import create_database, migrate
from build3d_api.storage import FileSystemArtifactStorage
from build3d_api.store import Store, new_id
from build3d_gateway.glb_validation import inspect_glb
from build3d_gateway.textured_glb import SimpleOBJ, build_textured_glb


ROOT = Path(__file__).resolve().parents[4]
WEB = ROOT / "apps" / "web"


def seed_database(settings: Settings, root: Path) -> dict:
    engine = create_database(settings.database_url)
    try:
        migrate(engine)
        store = Store(engine, settings)
        alice = store.create_user("Acceptance Alice")
        bob = store.create_user("Acceptance Bob")
        owner_id = alice["user_id"]
        project = store.create_project(owner_id, "Synthetic artifact project")
        job, _ = store.submit(
            owner_id=owner_id,
            project_id=project["id"],
            kind="text",
            model_id="synthetic_fixture",
            key="real-api-acceptance-fixture",
            approval={},
            prompt="Synthetic triangle fixture",
        )

        # Seed historical data through the store and artifact interfaces. The
        # HTTP API still has an empty model policy, and no worker is started.
        claimed = store.claim()
        if claimed is None or claimed["id"] != job["id"]:
            raise RuntimeError("Could not claim the synthetic acceptance job")
        mesh = SimpleOBJ(
            positions=((0, 0, 0), (1, 0, 0), (0, 1, 0)),
            texcoords=((0, 0), (1, 0), (0, 1)),
            normals=None,
            triangles=((0, 1, 2),),
        )
        texture = io.BytesIO()
        Image.new("RGB", (2, 2), "blue").save(texture, format="PNG")
        source = root / "synthetic-triangle.glb"
        source.write_bytes(build_textured_glb(mesh, texture.getvalue()))
        with source.open("rb") as source_file:
            report = inspect_glb(source_file)

        artifact_id = new_id()
        storage = FileSystemArtifactStorage(settings.artifact_dir)
        storage.prepare()
        storage.publish(
            artifact_id=artifact_id,
            owner_id=owner_id,
            job_id=job["id"],
            source=source,
            sha256=report.sha256,
            size_bytes=report.size_bytes,
        )
        if not store.transition(claimed, "completed", artifact={
            "id": artifact_id,
            "owner_id": owner_id,
            "job_id": job["id"],
            "sha256": report.sha256,
            "size_bytes": report.size_bytes,
            "mesh_count": report.mesh_count,
            "created_at": time.time(),
        }):
            raise RuntimeError("Could not complete the synthetic acceptance job")

        return {
            "aliceKey": alice["api_key"],
            "bobKey": bob["api_key"],
            "projectId": project["id"],
            "jobId": job["id"],
            "artifactBytes": report.size_bytes,
            "artifactSha256": report.sha256,
        }
    finally:
        engine.dispose()


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="build3d-real-api-") as temporary:
        root = Path(temporary)
        settings = Settings(
            database_url=f"sqlite:///{root / 'acceptance.db'}",
            artifact_dir=root / "artifacts",
        )
        fixture_path = root / "acceptance.json"
        fixture_path.touch(mode=0o600, exist_ok=False)
        fixture_path.write_text(json.dumps(seed_database(settings, root)), encoding="utf-8")
        model_policy = root / "model-policy.json"
        model_policy.write_text(
            json.dumps({"schema_version": 1, "approved_models": []}), encoding="utf-8"
        )
        test_env = {
            **os.environ,
            "BUILD3D_ACCEPTANCE_PYTHON": sys.executable,
            "BUILD3D_ACCEPTANCE_FIXTURE": str(fixture_path),
            "DATABASE_URL": settings.database_url,
            "ARTIFACT_DIR": str(settings.artifact_dir),
            "ARTIFACT_STORAGE_BACKEND": settings.artifact_storage_backend,
            "ARTIFACT_STORAGE_PREFIX": settings.artifact_storage_prefix,
            "EXTERNAL_JWT_AUTH_ENABLED": "false",
            "MODEL_APPROVAL_FILE": str(model_policy),
            "API_REQUESTS_PER_MINUTE": str(settings.requests_per_minute),
            "DEBUG": "",
            "PWDEBUG": "0",
        }
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts/cloud/run_web.py"),
             str(WEB / "node_modules/.bin/playwright"), "test",
             "--config", "playwright.real-api.config.ts"],
            cwd=ROOT,
            env=test_env,
            check=False,
        ).returncode


if __name__ == "__main__":
    sys.exit(main())
