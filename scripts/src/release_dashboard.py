from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
IMAGE_REPOSITORY = "ghcr.io/m-ryan-nugent/cluster-dashboard"
VERSION_RE = re.compile(r"^v\d+\.\d+\.\d+$")
IMAGE_RE = re.compile(rf"{re.escape(IMAGE_REPOSITORY)}:v\d+\.\d+\.\d+")


@dataclass(frozen=True)
class TargetFile:
    path: Path
    minimum_replacements: int = 1


TARGET_FILES = (
    TargetFile(Path("infra/apps/cluster-dashboard/k8s/deployment.yaml")),
    TargetFile(Path("docs/k8s-deployment.md")),
    TargetFile(Path("infra/apps/cluster-dashboard/README.md")),
    TargetFile(Path("README.md")),
    TargetFile(Path("docs/kiosk-setup.md")),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Update cluster-dashboard release references to a new GHCR version tag."
    )
    parser.add_argument(
        "version",
        help="Release tag to apply, for example v1.0.1",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show which files would change without writing them.",
    )
    return parser.parse_args()


def validate_version(version: str) -> None:
    if not VERSION_RE.fullmatch(version):
        raise ValueError("version must match vMAJOR.MINOR.PATCH, for example v1.0.1")


def update_target(target: TargetFile, version: str, dry_run: bool) -> int:
    absolute_path = REPO_ROOT / target.path
    original_text = absolute_path.read_text()
    updated_text, replacements = IMAGE_RE.subn(f"{IMAGE_REPOSITORY}:{version}", original_text)

    if replacements < target.minimum_replacements:
        raise RuntimeError(
            f"expected at least {target.minimum_replacements} image reference updates in {target.path}, found {replacements}"
        )

    if not dry_run and updated_text != original_text:
        absolute_path.write_text(updated_text)

    return replacements


def main() -> int:
    args = parse_args()

    try:
        validate_version(args.version)
    except ValueError as error:
        print(error, file=sys.stderr)
        return 2

    print(f"Preparing cluster-dashboard release {args.version}")

    try:
        for target in TARGET_FILES:
            replacements = update_target(target, args.version, args.dry_run)
            status = "would update" if args.dry_run else "updated"
            print(f"{status} {target.path} ({replacements} replacements)")
    except RuntimeError as error:
        print(error, file=sys.stderr)
        return 1

    if args.dry_run:
        print("Dry run complete. No files were changed.")
    else:
        print("Release references updated.")
        print("Next steps:")
        print("  git diff")
        print(f"  git commit -am \"Release cluster dashboard {args.version}\"")
        print(f"  git tag {args.version}")
        print("  git push origin main")
        print(f"  git push origin {args.version}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())