import re
import subprocess
import sys


def get_latest_tag():
    try:
        # Get all tags sorted by version-like order
        result = subprocess.run(
            ["git", "tag", "--list", "--sort=-v:refname"],
            capture_output=True,
            text=True,
            check=True,
        )
        tags = result.stdout.strip().split("\n")
        return tags[0] if tags and tags[0] else None
    except Exception:  # noqa: BLE001
        return None


def parse_version(v_str):
    # Parses X.Y.Z-beta.N or X.Y.Z
    # Returns (major, minor, patch, is_beta, beta_num)
    core = v_str.split("-")[0]
    parts = list(map(int, core.split(".")))
    while len(parts) < 3:
        parts.append(0)

    is_beta = "-" in v_str and "beta" in v_str
    beta_num = -1
    if is_beta:
        match = re.search(r"beta\.(\d+)", v_str)
        if match:
            beta_num = int(match.group(1))

    return parts[0], parts[1], parts[2], is_beta, beta_num


def bump_version(current, bump_type, release_status, all_tags=None):
    is_target_beta = release_status == "beta"

    if not current:
        if is_target_beta:
            return "1.0.0-beta.0"
        return "1.0.0"

    major, minor, patch, is_curr_beta, curr_beta_num = parse_version(current)

    # Find latest STABLE tag for base calculation
    latest_stable = (0, 0, 0)
    if all_tags:
        for t in all_tags:
            t = t.lstrip("v")
            if t and "-" not in t:
                s_major, s_minor, s_patch, _, _ = parse_version(t)
                latest_stable = (s_major, s_minor, s_patch)
                break
    else:
        try:
            res = subprocess.run(
                ["git", "tag", "--list", "--sort=-v:refname"],
                capture_output=True,
                text=True,
                check=True,
            )
            for t in res.stdout.strip().split("\n"):
                t = t.lstrip("v")
                if t and "-" not in t:
                    s_major, s_minor, s_patch, _, _ = parse_version(t)
                    latest_stable = (s_major, s_minor, s_patch)
                    break
        except Exception:  # noqa: BLE001
            pass

    if is_target_beta:
        if is_curr_beta:
            # Check if current beta is already ahead of latest stable
            # If current beta is based on an older stable or equal, we bump
            return f"{major}.{minor}.{patch}-beta.{curr_beta_num + 1}"
        # Current is stable, start next beta cycle based on bump_type
        b_major, b_minor, b_patch = major, minor, patch
        if bump_type == "major":
            b_major += 1
            b_minor = 0
            b_patch = 0
        elif bump_type == "minor":
            b_minor += 1
            b_patch = 0
        else:  # patch
            b_patch += 1
        return f"{b_major}.{b_minor}.{b_patch}-beta.0"

    # Target is STABLE
    if is_curr_beta:
        # Promoting beta to stable -> drop beta suffix
        return f"{major}.{minor}.{patch}"
    # Current is stable, bump directly
    if bump_type == "major":
        return f"{major + 1}.0.0"
    if bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python bump_version.py <bump_type> <release_status> [current_version]")
        sys.exit(1)

    b_type = sys.argv[1].lower()
    r_status = sys.argv[2].lower()

    if len(sys.argv) > 3:
        curr = sys.argv[3].lstrip("v")
    else:
        latest = get_latest_tag()
        curr = latest.lstrip("v") if latest else None

    print(bump_version(curr, b_type, r_status))
