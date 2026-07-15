"""
Run Alembic migrations.
Usage: python scripts/run_migrations.py
"""
import subprocess
import sys
from pathlib import Path


def main() -> None:
    project_root = Path(__file__).parent.parent
    try:
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True,
        )
        print(result.stdout or "Migrations applied successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Migration failed:\n{e.stderr}", file=sys.stderr)
        if "could not connect" in e.stderr or "Connection refused" in e.stderr:
            print("Is the database running and reachable?", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("alembic not found. Is it installed? (pip install alembic)", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
