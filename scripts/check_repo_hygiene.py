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

# Hybrid _agent_ops/ policy: durable project memory is tracked so it survives a
# clone; session-scoped working memory stays local. See core-context/README.md.
OPS_SESSION_SCOPED = {
    "SESSION_BRIEF.md",
    "CURRENT_TASK.md",
    "LOG_SUMMARY.md",
    "code_index.json",
}
OPS_SESSION_SCOPED_DIRS: set[str] = set()
OPS_DURABLE = {
    "INDEX.md",
    "OPERATING_RULES.md",
    "SESSION_PROTOCOL.md",
    "PROJECT_CONTEXT_CARD.md",
    "REPO_MAP.md",
    "IMPLEMENTATION_LOG.md",
    "DECISION_LOG.md",
    "RISK_REGISTER.md",
    "PHASE_ROADMAP.md",
}


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


def ops_policy_violations(tracked: list[str], ops_folder: str) -> list[tuple[str, str]]:
    """Session-scoped ops files that are tracked when they should stay local."""
    prefix = f"{ops_folder}/"
    violations: list[tuple[str, str]] = []
    for path in tracked:
        if not path.startswith(prefix):
            continue
        remainder = path[len(prefix) :]
        head = remainder.split("/", 1)[0]
        if remainder in OPS_SESSION_SCOPED:
            violations.append((path, "session-scoped working memory"))
        elif head in OPS_SESSION_SCOPED_DIRS:
            violations.append((path, f"session-scoped folder {head}/"))
    return violations


def ops_untracked_durable(root: Path, tracked: list[str], ops_folder: str) -> list[str]:
    """Durable memory that exists on disk but is not tracked, so a clone loses it."""
    ops_dir = root / ops_folder
    if not ops_dir.is_dir():
        return []
    tracked_set = set(tracked)
    return [
        f"{ops_folder}/{name}"
        for name in sorted(OPS_DURABLE)
        if (ops_dir / name).is_file() and f"{ops_folder}/{name}" not in tracked_set
    ]


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
    parser.add_argument(
        "--ops-folder",
        default="_agent_ops",
        help="Agent ops folder to check against the hybrid tracking policy.",
    )
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        parser.error(f"Root must be an existing directory: {root}")

    print(f"Root: {root}")
    failures: list[tuple[str, list[str]]] = []
    ops_violations: list[tuple[str, str]] = []
    ops_untracked: list[str] = []
    git_repo = is_git_repo(root)
    if not git_repo:
        print("WARN: Not a git repository. Tracked-file hygiene check skipped.")
    else:
        files = tracked_files(root)
        for file_name in files:
            patterns = matches_forbidden(file_name)
            if patterns:
                failures.append((file_name, patterns))
        ops_violations = ops_policy_violations(files, args.ops_folder)
        ops_untracked = ops_untracked_durable(root, files, args.ops_folder)
        print(f"Tracked files checked: {len(files)}")

    if failures:
        print("FAIL: Forbidden tracked files found:")
        for file_name, patterns in failures:
            print(f"- {file_name} matches {', '.join(patterns)}")
    elif git_repo:
        print("PASS: No forbidden tracked files found.")
    else:
        print("INFO: No tracked-file result because there is no git index.")

    if git_repo and (root / args.ops_folder).is_dir():
        if ops_violations:
            print(f"FAIL: Session-scoped {args.ops_folder}/ files are tracked:")
            for file_name, reason in ops_violations:
                print(f"- {file_name} is {reason}; it should stay local")
            print(
                f"  Fix: git rm --cached <file>, and confirm {args.ops_folder}/.gitignore exists."
            )
        else:
            print(f"PASS: No session-scoped {args.ops_folder}/ files are tracked.")
        if ops_untracked:
            print(f"INFO: Durable {args.ops_folder}/ memory exists but is not tracked:")
            for file_name in ops_untracked:
                print(f"- {file_name} would be lost on a fresh clone")

    artifacts = filesystem_artifacts(root)
    print(f"Filesystem artifact scan findings: {len(artifacts)}")
    if artifacts:
        label = "WARN" if args.warn_only_artifacts else "FAIL"
        print(f"{label}: Generated/private filesystem artifacts found:")
        for file_name, reason in artifacts:
            print(f"- {file_name} matches {reason}")
    else:
        print("PASS: No generated/private filesystem artifacts found.")

    if failures or ops_violations or (artifacts and not args.warn_only_artifacts):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
