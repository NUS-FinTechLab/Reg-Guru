#!/usr/bin/env python3
"""Apply SQL migrations stored in backend/migrations."""

from __future__ import annotations

import argparse
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
BACKEND_PATH = REPO_ROOT / "backend"
if str(BACKEND_PATH) not in sys.path:
    sys.path.insert(0, str(BACKEND_PATH))

from app.db import get_connection  # noqa: E402

DEFAULT_MIGRATIONS_DIR = REPO_ROOT / "backend" / "migrations"


def apply_sql_file(path: pathlib.Path) -> None:
    sql = path.read_text()
    if not sql.strip():
        return

    with get_connection() as conn:
        with conn.cursor() as cur:
            # Execute the full file to ensure dollar-quoted blocks stay intact.
            cur.execute(sql)


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply backend SQL migrations")
    parser.add_argument(
        "--path",
        type=pathlib.Path,
        default=DEFAULT_MIGRATIONS_DIR,
        help="Directory containing .sql migration files",
    )
    args = parser.parse_args()

    migrations_dir = args.path
    if not migrations_dir.exists():
        raise SystemExit(f"Migration directory not found: {migrations_dir}")

    sql_files = sorted(p for p in migrations_dir.glob("*.sql"))
    if not sql_files:
        print("No migrations to apply")
        return

    for sql_file in sql_files:
        print(f"Applying migration: {sql_file.name}")
        apply_sql_file(sql_file)

    print("All migrations applied successfully")


if __name__ == "__main__":
    main()
