import glob
import json
import os
import re
import subprocess
from datetime import UTC, datetime


def run_git(args):
    try:
        return (
            subprocess.check_output(["git"] + args, stderr=subprocess.DEVNULL)
            .decode("utf-8")
            .strip()
        )
    except subprocess.CalledProcessError:
        return ""


def main():
    rtype = os.environ.get("RELEASE_TYPE", "beta")
    bump_level = os.environ.get("BUMP_LEVEL", "patch")
    version_override = os.environ.get("VERSION_OVERRIDE", "")
    repo = os.environ.get("REPO", "")

    # Determine owner and repo_name dynamically
    owner = "faserf"
    repo_name = os.path.basename(os.getcwd())
    if "/" in repo:
        owner, repo_name = repo.split("/", 1)

    # Dynamic manifest location
    manifest_files = glob.glob("custom_components/*/manifest.json")
    if not manifest_files:
        print("Error: manifest.json not found!")
        return
    manifest_path = manifest_files[0]
    domain = os.path.basename(os.path.dirname(manifest_path))

    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    friendly_name = manifest.get("name", domain)

    # Dynamic documentation URL logic
    docs_url = manifest.get("documentation")
    if not docs_url:
        if os.path.exists("docs"):
            docs_url = f"https://{owner}.github.io/{repo_name}/"
        else:
            docs_url = (
                f"https://github.com/{repo}"
                if repo
                else f"https://github.com/faserf/{repo_name}"
            )

    # Calculate version via version_manager
    bump_args = [
        "python",
        ".github/scripts/version_manager.py",
        "bump",
        "--type",
        rtype,
        "--level",
        bump_level,
    ]
    version = (
        subprocess.check_output(bump_args, stderr=subprocess.DEVNULL)
        .decode("utf-8")
        .strip()
    )

    # Revert modified files to keep clean state
    for path in [manifest_path, "pyproject.toml"]:
        try:
            subprocess.run(["git", "checkout", "--", path], check=False)
        except Exception:  # noqa: BLE001
            pass

    if version_override:
        version = version_override.lstrip("v")

    tag = f"v{version}"
    is_prerelease = "false" if rtype == "stable" else "true"

    # Find last tag for changelog
    last_tag = run_git(["describe", "--tags", "--abbrev=0", "HEAD~1"])
    if not last_tag:
        last_tag = run_git(["rev-list", "--max-parents=0", "HEAD"])

    # Generate changelog via changelog_builder.py
    repo_url = f"https://github.com/{owner}/{repo_name}"
    changelog_args = [
        "python",
        ".github/scripts/changelog_builder.py",
        "--tag",
        last_tag,
        "--url",
        repo_url,
    ]
    try:
        raw_changelog = (
            subprocess.check_output(changelog_args, stderr=subprocess.DEVNULL)
            .decode("utf-8")
            .strip()
        )
    except Exception:  # noqa: BLE001
        raw_changelog = "## Changelog\n\nNo significant changes."

    now = datetime.now(UTC)
    date_str = now.strftime("%B %d, %Y")

    full_body = (
        f"# {friendly_name} {tag} ({date_str})\n\n"
        f"{raw_changelog}\n\n"
        f"**Full Changelog**: {repo_url}/compare/{last_tag}...{tag}"
    )

    with open("release_body.md", "w", encoding="utf-8") as f:
        f.write(full_body)

    # Export to GITHUB_OUTPUT if available
    gh_out = os.environ.get("GITHUB_OUTPUT")
    if gh_out:
        with open(gh_out, "a", encoding="utf-8") as f:
            f.write(f"version={version}\n")
            f.write(f"tag={tag}\n")
            f.write(f"is_prerelease={is_prerelease}\n")
            # Multiline release body syntax for GITHUB_OUTPUT
            f.write("release_body<<EOF\n")
            f.write(full_body + "\n")
            f.write("EOF\n")

    print(f"Calculated Version: {version}")
    print(f"Tag: {tag}")
    print(f"Pre-release: {is_prerelease}")


if __name__ == "__main__":
    main()
