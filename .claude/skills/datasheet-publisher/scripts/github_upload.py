#!/usr/bin/env python3
"""
Create or update a single file in a GitHub repo via the Contents API.

Why a script: every run of the publishing skill would otherwise re-derive the
same dance (look up the file's current SHA so an update doesn't 422, base64 the
content, PUT it, surface a usable link). Doing it once here keeps each run fast
and consistent, and gives clear, actionable errors instead of a raw 401/404.

Auth: pass --token, or set GITHUB_TOKEN in the environment. Use a fine-grained
token scoped to just the target repo with Contents: read & write.

Network: talks only to https://api.github.com (allowed in this environment).

Usage:
  python github_upload.py \
      --repo owner/name \
      --path docs/specs/atlas-2.md \
      --file /mnt/user-data/outputs/atlas-2.md \
      [--branch main] \
      [--message "Add atlas-2.md (transcribed from ATLAS-2.pdf)"] \
      [--token ghp_xxx]

On success it prints a JSON object with the commit and the file's html_url so
the caller can show the user a direct link.
"""
import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request

API = "https://api.github.com"


def _request(method, url, token, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "datasheet-publisher-skill")
    if body is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        try:
            payload = json.loads(e.read().decode())
        except Exception:
            payload = {"message": e.reason}
        return e.code, payload


def main():
    p = argparse.ArgumentParser(description="Upload one file to a GitHub repo.")
    p.add_argument("--repo", required=True, help="owner/name")
    p.add_argument("--path", required=True, help="destination path inside the repo")
    p.add_argument("--file", required=True, help="local file to upload")
    p.add_argument("--branch", default=None, help="branch (default: repo default branch)")
    p.add_argument("--message", default=None, help="commit message")
    p.add_argument("--token", default=None, help="GitHub token (else $GITHUB_TOKEN)")
    args = p.parse_args()

    token = args.token or os.environ.get("GITHUB_TOKEN")
    if not token:
        print(json.dumps({"ok": False, "error": "no_token",
                          "detail": "Provide --token or set GITHUB_TOKEN."}))
        sys.exit(2)

    if "/" not in args.repo:
        print(json.dumps({"ok": False, "error": "bad_repo",
                          "detail": "Repo must be in owner/name form."}))
        sys.exit(2)

    try:
        with open(args.file, "rb") as f:
            raw = f.read()
    except OSError as e:
        print(json.dumps({"ok": False, "error": "file_unreadable", "detail": str(e)}))
        sys.exit(2)

    content_b64 = base64.b64encode(raw).decode()
    contents_url = f"{API}/repos/{args.repo}/contents/{args.path}"
    message = args.message or f"Add {os.path.basename(args.path)} via datasheet-publisher"

    # Look up an existing file's SHA (updates require it; a new file does not).
    get_url = contents_url + (f"?ref={args.branch}" if args.branch else "")
    status, existing = _request("GET", get_url, token)
    sha = existing.get("sha") if status == 200 and isinstance(existing, dict) else None

    if status not in (200, 404):
        hint = {
            401: "Token is missing/invalid or lacks Contents access to this repo.",
            403: "Forbidden — token scope, SSO authorization, or rate limit.",
            404: "",
        }.get(status, "")
        print(json.dumps({"ok": False, "error": f"github_{status}",
                          "detail": existing.get("message", ""), "hint": hint}))
        sys.exit(1)

    payload = {"message": message, "content": content_b64}
    if args.branch:
        payload["branch"] = args.branch
    if sha:
        payload["sha"] = sha  # turns a create into an update

    status, result = _request("PUT", contents_url, token, payload)
    if status in (200, 201):
        content = result.get("content", {}) or {}
        commit = result.get("commit", {}) or {}
        print(json.dumps({
            "ok": True,
            "action": "updated" if sha else "created",
            "html_url": content.get("html_url"),
            "path": content.get("path"),
            "branch": args.branch,
            "commit_sha": commit.get("sha"),
        }, indent=2))
        sys.exit(0)

    hint = {
        401: "Token is missing/invalid or lacks Contents: write on this repo.",
        403: "Forbidden — check token scope, org SSO authorization, or rate limit.",
        404: "Repo or branch not found, or token can't see this repo.",
        409: "Conflict — branch state changed; re-run to pick up the latest SHA.",
        422: "Validation failed — often a stale/missing SHA or a protected branch.",
    }.get(status, "")
    print(json.dumps({"ok": False, "error": f"github_{status}",
                      "detail": result.get("message", ""), "hint": hint}))
    sys.exit(1)


if __name__ == "__main__":
    main()
