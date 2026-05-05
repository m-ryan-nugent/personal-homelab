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
DEPLOYMENT_FILE = Path("infra/apps/cluster-dashboard/k8s/deployment.yaml")


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
        nargs="?",
        help="Release tag to apply, for example v1.0.1",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show which files would change without writing them.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if tracked docs do not match the image tag pinned in the deployment.",
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


def get_deployment_version() -> str:
    deployment_text = (REPO_ROOT / DEPLOYMENT_FILE).read_text()
    images = set(IMAGE_RE.findall(deployment_text))

    if len(images) != 1:
        raise RuntimeError(
            f"expected exactly one dashboard image reference in {DEPLOYMENT_FILE}, found {len(images)}"
        )

    return next(iter(images)).rsplit(":", maxsplit=1)[1]


def check_target(target: TargetFile, expected_image: str) -> None:
    absolute_path = REPO_ROOT / target.path
    text = absolute_path.read_text()
    images = IMAGE_RE.findall(text)

    if len(images) < target.minimum_replacements:
        raise RuntimeError(
            f"expected at least {target.minimum_replacements} image reference updates in {target.path}, found {len(images)}"
        )

    mismatches = sorted({image for image in images if image != expected_image})
    if mismatches:
        mismatch_list = ", ".join(mismatches)
        raise RuntimeError(
            f"{target.path} contains dashboard image references that do not match {expected_image}: {mismatch_list}"
        )


def run_check() -> int:
    try:
        version = get_deployment_version()
    except RuntimeError as error:
        print(error, file=sys.stderr)
        return 1

    expected_image = f"{IMAGE_REPOSITORY}:{version}"
    print(f"Checking cluster-dashboard release references against {expected_image}")

    try:
        for target in TARGET_FILES:
            check_target(target, expected_image)
            print(f"ok {target.path}")
    except RuntimeError as error:
        print(error, file=sys.stderr)
        return 1

    print("All tracked dashboard image references are in sync.")
    return 0


def main() -> int:
    args = parse_args()

    if args.check:
        if args.version is not None:
            print("--check does not accept a version argument", file=sys.stderr)
            return 2
        if args.dry_run:
            print("--check cannot be combined with --dry-run", file=sys.stderr)
            return 2
        return run_check()

    if args.version is None:
        print("version is required unless --check is used", file=sys.stderr)
        return 2

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