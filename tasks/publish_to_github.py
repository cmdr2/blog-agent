import requests
import hashlib


def run(files, config={}):
    """
    Commit only changed files to a GitHub repo branch using the Git Data API.

    Args:
        files: list of tuples (filepath, file_contents)
            filepath: str - path inside the repo (e.g. "posts/new.md")
            file_contents: str - file contents as text (UTF-8)
        config: dict with keys:
            github_owner: str
            github_repo: str
            github_branch: str
            github_token: str (PAT or GitHub App installation token)
    """
    owner = config["github_owner"]
    repo = config["github_repo"]
    branch = config["github_branch"]
    prefix = config.get("github_prefix", "")
    token = config["github_token"]

    api = f"https://api.github.com/repos/{owner}/{repo}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    # 1. Get the latest commit on the branch
    ref_resp = requests.get(f"{api}/git/ref/heads/{branch}", headers=headers)
    ref_resp.raise_for_status()
    ref_data = ref_resp.json()
    latest_commit_sha = ref_data["object"]["sha"]

    commit_resp = requests.get(f"{api}/git/commits/{latest_commit_sha}", headers=headers)
    commit_resp.raise_for_status()
    commit_data = commit_resp.json()
    base_tree_sha = commit_data["tree"]["sha"]

    # 2. Get the full tree of the branch
    tree_resp = requests.get(f"{api}/git/trees/{base_tree_sha}?recursive=1", headers=headers)
    tree_resp.raise_for_status()
    tree_data = tree_resp.json()
    existing_files = {item["path"]: item["sha"] for item in tree_data.get("tree", []) if item["type"] == "blob"}

    # 3. Prepare tree entries for changed files only
    tree_entries = []
    changed_files = []

    if prefix:
        prefix = prefix.strip("/")

    for filepath, content in files:
        full_path = f"{prefix}/{filepath}" if prefix else filepath

        # Quick check: if file exists and has the same blob sha, skip
        if full_path in existing_files:
            data = f"blob {len(content)}\0{content}".encode("utf-8")
            computed_sha = hashlib.sha1(data).hexdigest()
            if computed_sha == existing_files[full_path]:
                continue  # unchanged

        # Create new blob
        blob_resp = requests.post(
            f"{api}/git/blobs",
            headers=headers,
            json={"content": content, "encoding": "utf-8"},
        )
        blob_resp.raise_for_status()
        blob_sha = blob_resp.json()["sha"]

        tree_entries.append(
            {
                "path": full_path,
                "mode": "100644",
                "type": "blob",
                "sha": blob_sha,
            }
        )
        changed_files.append(full_path)

    if not tree_entries:
        return {"committed_files": [], "commit_sha": None}

    # 4. Create a new tree
    new_tree_resp = requests.post(
        f"{api}/git/trees",
        headers=headers,
        json={"base_tree": base_tree_sha, "tree": tree_entries},
    )
    new_tree_resp.raise_for_status()
    new_tree_sha = new_tree_resp.json()["sha"]

    # 5. Create a new commit
    new_commit_resp = requests.post(
        f"{api}/git/commits",
        headers=headers,
        json={
            "message": "Automated commit from Lambda",
            "tree": new_tree_sha,
            "parents": [latest_commit_sha],
        },
    )
    new_commit_resp.raise_for_status()
    new_commit_sha = new_commit_resp.json()["sha"]

    # 6. Update the branch ref
    update_ref_resp = requests.patch(
        f"{api}/git/refs/heads/{branch}",
        headers=headers,
        json={"sha": new_commit_sha},
    )
    update_ref_resp.raise_for_status()

    return {
        "committed_files": changed_files,
        "commit_sha": new_commit_sha,
    }
