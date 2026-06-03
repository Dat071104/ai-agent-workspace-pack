#!/usr/bin/env python3
"""Check tracked files and local artifacts for common public-repo hygiene problems."""

from __future__ import annotations

import argparse
import fnmatch
import subprocess
from pathlib import Path


FORBIDDEN_PATTERNS = [
    ".env",
    ".env.*",
    "data/*",
    "models/*",
    "mlruns/*",
    "artifacts/*",
    "node_modules/*",
    "dist/*",
    "build/*",
    "__pycache__/*",
    ".pytest_cache/*",
    "target/*",
    "logs/*",
    "*.log",
    "*.sqlite",
    "*.sqlite3",
    "*.db",
    "*.pem",
    "*.key",
]
ARTIFACT_DIR_NAMES = {
    "__pycache__",
    ".pytest_cache",
    "node_modules",
    "dist",
    "build",
    "target",
    "data",
    "models",
    "mlruns",
    "artifacts",
    "coverage",
    "playwright-report",
    "test-results",
}
ARTIFACT_FILE_PATTERNS = [
    ".env",
    ".env.*",
    "*.db",
    "*.sqlite",
    "*.sqlite3",
    "*.pem",
    "*.key",
    "*.log",
]
SKIP_SCAN_DIRS = {".git"}


def run_git(root: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(root),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def is_git_repo(root: Path) -> bool:
    result = run_git(root, ["rev-parse", "--is-inside-work-tree"])
    return result.returncode == 0 and result.stdout.strip() == "true"


def tracked_files(root: Path) -> list[str]:
    result = run_git(root, ["ls-files"])
    if result.returncode != 0:
        return []
    return [line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()]


def matches_forbidden(path: str) -> list[str]:
    normalized = path.replace("\\", "/")
    name = Path(normalized).name
    matches: list[str] = []
    for pattern in FORBIDDEN_PATTERNS:
        if fnmatch.fnmatch(normalized, pattern) or fnmatch.fnmatch(name, pattern):
            matches.append(pattern)
    return matches


def filesystem_artifacts(root: Path) -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    for path in root.rglob("*"):
        if any(part in SKIP_SCAN_DIRS for part in path.parts):
            continue
        rel = path.relative_to(root).as_posix()
        if path.is_dir() and path.name in ARTIFACT_DIR_NAMES:
            findings.append((rel + "/", f"directory {path.name}/"))
            continue
        if path.is_file():
            for pattern in ARTIFACT_FILE_PATTERNS:
                if fnmatch.fnmatch(path.name, pattern):
                    findings.append((rel, f"file pattern {pattern}"))
                    break
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Check forbidden tracked files and filesystem artifacts.")
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument(
        "--warn-only-artifacts",
        action="store_true",
        help="Report filesystem artifacts without failing the command.",
    )
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        parser.error(f"Root must be an existing directory: {root}")

    print(f"Root: {root}")
    failures: list[tuple[str, list[str]]] = []
    git_repo = is_git_repo(root)
    if not git_repo:
        print("WARN: Not a git repository. Tracked-file hygiene check skipped.")
    else:
        files = tracked_files(root)
        for file_name in files:
            patterns = matches_forbidden(file_name)
            if patterns:
                failures.append((file_name, patterns))
        print(f"Tracked files checked: {len(files)}")

    if failures:
        print("FAIL: Forbidden tracked files found:")
        for file_name, patterns in failures:
            print(f"- {file_name} matches {', '.join(patterns)}")
    elif git_repo:
        print("PASS: No forbidden tracked files found.")
    else:
        print("INFO: No tracked-file result because there is no git index.")

    artifacts = filesystem_artifacts(root)
    print(f"Filesystem artifact scan findings: {len(artifacts)}")
    if artifacts:
        label = "WARN" if args.warn_only_artifacts else "FAIL"
        print(f"{label}: Generated/private filesystem artifacts found:")
        for file_name, reason in artifacts:
            print(f"- {file_name} matches {reason}")
    else:
        print("PASS: No generated/private filesystem artifacts found.")

    if failures or (artifacts and not args.warn_only_artifacts):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
