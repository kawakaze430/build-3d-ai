"""Ensure installed distributions can run migrations outside this checkout."""
from pathlib import Path
import zipfile

wheel = next(Path("dist").glob("build3d_api-*.whl"))
with zipfile.ZipFile(wheel) as archive:
    names = set(archive.namelist())
    required = {
        "build3d_api/migrations/env.py",
        "build3d_api/migrations/versions/0001_projects_jobs.py",
    }
    assert required <= names, f"Wheel is missing migration files: {required - names}"
print("API wheel includes versioned migrations")
