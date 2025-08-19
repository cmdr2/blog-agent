import http.client
import json
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
            github_prefix: optional str, prefix path inside repo
    """
    owner = config["github_owner"]
    repo = config["github_repo"]
    branch = config["github_branch"]
    token = config["github_token"]
    prefix = config.get("github_prefix", "")
    if prefix:
        prefix = prefix.strip("/")

    api_base = f"/repos/{owner}/{repo}"

    # 1. Get the latest commit on the branch
    ref_data = _gh_request("GET", f"{api_base}/git/ref/heads/{branch}", token)
    latest_commit_sha = ref_data["object"]["sha"]

    commit_data = _gh_request("GET", f"{api_base}/git/commits/{latest_commit_sha}", token)
    base_tree_sha = commit_data["tree"]["sha"]

    # 2. Get the full tree of the branch
    tree_data = _gh_request("GET", f"{api_base}/git/trees/{base_tree_sha}?recursive=1", token)
    existing_files = {item["path"]: item["sha"] for item in tree_data.get("tree", []) if item["type"] == "blob"}

    # 3. Prepare tree entries for changed files only
    tree_entries = []
    changed_files = []

    for filepath, content in files:
        full_path = f"{prefix}/{filepath}" if prefix else filepath

        # Quick check: if file exists and has the same blob sha, skip
        if full_path in existing_files:
            data = f"blob {len(content)}\0{content}".encode("utf-8")
            computed_sha = hashlib.sha1(data).hexdigest()
            if computed_sha == existing_files[full_path]:
                continue  # unchanged

        # Create new blob
        blob_resp = _gh_request(
            "POST",
            f"{api_base}/git/blobs",
            token,
            {"content": content, "encoding": "utf-8"},
        )
        blob_sha = blob_resp["sha"]

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
    new_tree_resp = _gh_request(
        "POST",
        f"{api_base}/git/trees",
        token,
        {"base_tree": base_tree_sha, "tree": tree_entries},
    )
    new_tree_sha = new_tree_resp["sha"]

    # 5. Create a new commit
    new_commit_resp = _gh_request(
        "POST",
        f"{api_base}/git/commits",
        token,
        {
            "message": "Automated commit from Lambda",
            "tree": new_tree_sha,
            "parents": [latest_commit_sha],
        },
    )
    new_commit_sha = new_commit_resp["sha"]

    # 6. Update the branch ref
    _gh_request(
        "PATCH",
        f"{api_base}/git/refs/heads/{branch}",
        token,
        {"sha": new_commit_sha},
    )

    return {
        "committed_files": changed_files,
        "commit_sha": new_commit_sha,
    }


def _gh_request(method, path, token, body=None):
    conn = http.client.HTTPSConnection("api.github.com")
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "publish-to-github-script",
    }
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    else:
        data = None

    conn.request(method, path, body=data, headers=headers)
    resp = conn.getresponse()
    resp_data = resp.read().decode("utf-8")
    if resp.status >= 300:
        raise RuntimeError(f"GitHub API error {resp.status}: {resp_data}")
    if resp_data:
        return json.loads(resp_data)
    return None
