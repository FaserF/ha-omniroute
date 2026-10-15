import argparse
import datetime
import glob
import json
import os
import re
import subprocess


def find_manifest():
    matches = glob.glob("custom_components/*/manifest.json")
    return matches[0] if matches else None


MANIFEST_FILE = find_manifest()


def get_current_version(manifest_path=None):
    if manifest_path is None:
        manifest_path = MANIFEST_FILE
    try:
        tags = (
            subprocess.check_output(["git", "tag"], stderr=subprocess.DEVNULL)
            .decode()
            .splitlines()
        )
        v_tags = []
        for tag in tags:
            tag = tag.strip()
            match = re.match(r"^v?(\d+)\.(\d+)\.(\d+)(?:(b)(\d+)|(-dev)(\d+))?$", tag)
            if match:
                y, m, p, bp, bn, dp, dn = match.groups()
                v_tags.append(
                    {
                        "tag": tag,
                        "key": (
                            int(y),
                            int(m),
                            int(p),
                            (1 if bp else (0 if dp else 2)),
                            (int(bn) if bp else (int(dn) if dp else 0)),
                        ),
                    }
                )
        if v_tags:
            return sorted(v_tags, key=lambda x: x["key"], reverse=True)[0]["tag"]
    except Exception:
        pass
    if manifest_path and os.path.exists(manifest_path):
        with open(manifest_path, encoding="utf-8") as f:
            return json.load(f).get("version", "1.0.0")
    return "1.0.0"


def write_version(v, manifest_path=None):
    if manifest_path is None:
        manifest_path = MANIFEST_FILE
    if manifest_path and os.path.exists(manifest_path):
        with open(manifest_path, encoding="utf-8") as f:
            data = json.load(f)
        data["version"] = v
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.write("\n")

    if os.path.exists("pyproject.toml"):
        with open("pyproject.toml", encoding="utf-8") as f:
            content = f.read()
        content = re.sub(r'version = "[^"]+"', f'version = "{v}"', content)
        with open("pyproject.toml", "w", encoding="utf-8") as f:
            f.write(content)


def bump_calver(current, r_type, level="patch"):
    now = datetime.datetime.now(datetime.timezone.utc)
    target_year = now.year
    target_month = now.month

    match = re.match(r"^v?(\d+)\.(\d+)\.(\d+)(?:b(\d+))?$", current)
    if not match:
        curr_y, curr_m, curr_p = target_year, target_month, 0
        curr_b = None
    else:
        curr_y = int(match.group(1))
        curr_m = int(match.group(2))
        curr_p = int(match.group(3))
        curr_b = int(match.group(4)) if match.group(4) is not None else None

    if target_year != curr_y or target_month != curr_m:
        next_y, next_m, next_p = target_year, target_month, 0
        next_b = 1 if r_type == "beta" else None
    else:
        next_y, next_m = curr_y, curr_m
        if r_type == "beta":
            if curr_b is not None:
                next_p = curr_p
                next_b = curr_b + 1
            else:
                next_p = curr_p + 1
                next_b = 1
        else:
            if curr_b is not None:
                next_p = curr_p
            else:
                next_p = curr_p + 1
            next_b = None

    if next_b is not None:
        return f"{next_y}.{next_m}.{next_p}b{next_b}"
    return f"{next_y}.{next_m}.{next_p}"


def bump_semver(current, r_type, level="patch"):
    clean = current.lstrip("v")
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)(?:b(\d+))?", clean)
    if not match:
        major, minor, patch = 1, 0, 0
        b_num = None
    else:
        major = int(match.group(1))
        minor = int(match.group(2))
        patch = int(match.group(3))
        b_num = int(match.group(4)) if match.group(4) is not None else None

    if r_type == "beta":
        if b_num is not None:
            return f"{major}.{minor}.{patch}b{b_num + 1}"
        if level == "major":
            major += 1
            minor = 0
            patch = 0
        elif level == "minor":
            minor += 1
            patch = 0
        else:
            patch += 1
        return f"{major}.{minor}.{patch}b1"

    # Stable release
    if b_num is not None:
        return f"{major}.{minor}.{patch}"

    if level == "major":
        major += 1
        minor = 0
        patch = 0
    elif level == "minor":
        minor += 1
        patch = 0
    else:
        patch += 1
    return f"{major}.{minor}.{patch}"


def bump_version(current, r_type, scheme="semver", level="patch"):
    if scheme == "calver":
        return bump_calver(current, r_type, level)
    return bump_semver(current, r_type, level)


def main():
    parser = argparse.ArgumentParser(description="Manage project versions.")
    subparsers = parser.add_subparsers(dest="command")

    get_parser = subparsers.add_parser("get", help="Get current version")
    get_parser.add_argument("--manifest", help="Path to manifest.json")

    bump_parser = subparsers.add_parser("bump", help="Bump version")
    bump_parser.add_argument(
        "--type",
        choices=["stable", "beta", "nightly"],
        default="stable",
        help="Release type",
    )
    bump_parser.add_argument(
        "--scheme",
        choices=["semver", "calver"],
        default="semver",
        help="Versioning scheme",
    )
    bump_parser.add_argument(
        "--level",
        choices=["major", "minor", "patch"],
        default="patch",
        help="Bump level for semver",
    )
    bump_parser.add_argument("--manifest", help="Path to manifest.json")

    set_parser = subparsers.add_parser("set", help="Set version directly")
    set_parser.add_argument("version", help="Version string to set")
    set_parser.add_argument("--manifest", help="Path to manifest.json")

    args = parser.parse_args()

    if args.command == "get":
        print(get_current_version(args.manifest))
    elif args.command == "bump":
        current = get_current_version(args.manifest)
        new_version = bump_version(current, args.type, args.scheme, args.level)
        write_version(new_version, args.manifest)
        print(new_version)
    elif args.command == "set":
        write_version(args.version, args.manifest)
        print(args.version)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
