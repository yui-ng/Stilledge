#!/usr/bin/env python3
# memctl.py - User-facing CLI for memory management
# Copyright (c) 2026 John Chiao
# SPDX-License-Identifier: MIT

import argparse
import sys
from pathlib import Path
from memory_utils import *

def cmd_login(args):
    username = args.username
    ensure_dirs()
    ensure_user(username)
    set_current_user(username)
    print(f"Logged in as {username}")

def cmd_logout(args):
    if get_current_user() is None:
        print("Not logged in.")
        return
    clear_session()
    print("Logged out.")

def cmd_pull(args):
    user = get_current_user()
    if not user:
        print("Please login first.")
        return
    ensure_user(user)
    copy_main_to_user(user)
    append_timeline_event(user, {"type": "pull", "description": "Pulled from main"})
    print(f"Pulled main into {user}")

def cmd_push(args):
    user = get_current_user()
    if not user:
        print("Please login first.")
        return
    ensure_user(user)

    msg = args.msg
    user_dir = get_user_dir(user)

    files_to_push = args.files
    if not files_to_push or (len(files_to_push) == 1 and files_to_push[0] == '*'):
        all_files = []
        for item in user_dir.rglob('*'):
            if item.is_file() and item.name != TIMELINE_FILE:
                rel = str(item.relative_to(user_dir))
                all_files.append(rel)
        files_to_push = all_files
    else:
        valid_files = []
        for f in files_to_push:
            full = user_dir / f
            if full.exists() and full.is_file():
                valid_files.append(f)
            else:
                print(f"Warning: {f} not found, skipping.")
        files_to_push = valid_files

    if not files_to_push:
        print("No files to push. Aborting.")
        return

    files_snapshot = {}
    for rel in files_to_push:
        full = user_dir / rel
        files_snapshot[rel] = full.read_text(encoding='utf-8')

    pr_id = get_next_pr_id()
    pr_data = {
        "id": pr_id,
        "title": msg,
        "author": user,
        "created_at": datetime.datetime.now().isoformat(),
        "status": "open",
        "files": files_snapshot,
        "comments": [],
    }
    write_pr(pr_id, pr_data)
    append_timeline_event(user, {"type": "push", "description": f"Pushed: {msg}", "pr_id": pr_id})
    print(f"Created pull request #{pr_id} with {len(files_snapshot)} file(s): {msg}")

def cmd_log(args):
    events = []
    for username in list_users():
        for ev in read_timeline(username):
            ev["_user"] = username
            events.append(ev)
    events.sort(key=lambda x: x.get("timestamp", ""))
    for ev in events:
        ts = ev.get("timestamp", "unknown")
        user = ev.pop("_user", "?")
        typ = ev.get("type", "?")
        desc = ev.get("description", "")
        print(f"[{ts}] {user} {typ}: {desc}")

def cmd_status(args):
    user = get_current_user()
    if not user:
        print("Not logged in.")
        return
    user_dir = get_user_dir(user)
    file_count = sum(1 for _ in user_dir.rglob("*") if _.is_file() and _.name != TIMELINE_FILE)
    open_prs = []
    for pr_file in PRS_DIR.glob("*.json"):
        data = json.loads(pr_file.read_text())
        if data.get("author") == user and data.get("status") == "open":
            open_prs.append(data["id"])
    print(f"User: {user}")
    print(f"Files in workspace: {file_count}")
    print(f"Open PRs: {', '.join(map(str, open_prs)) if open_prs else 'none'}")

def cmd_list(args):
    use_main = args.main
    if use_main:
        target_dir = MAIN_DIR
        prefix = "main"
    else:
        user = get_current_user()
        if not user:
            print("Please login first, or use -m to list main repository.")
            return
        target_dir = get_user_dir(user)
        prefix = f"user {user}"

    if not target_dir.exists():
        print(f"Directory {target_dir} does not exist.")
        return

    files = []
    for item in target_dir.rglob('*'):
        if item.is_file():
            if not use_main and item.name == TIMELINE_FILE:
                continue
            rel = str(item.relative_to(target_dir))
            files.append(rel)

    if not files:
        print(f"No files found in {prefix}.")
        return

    print(f"Files in {prefix}:")
    for f in sorted(files):
        print(f"  {f}")

def cmd_get(args):
    file_path = args.file
    use_main = args.main

    if use_main:
        target_dir = MAIN_DIR
        prefix = "main"
    else:
        user = get_current_user()
        if not user:
            print("Please login first, or use -m to get from main repository.")
            return
        target_dir = get_user_dir(user)
        prefix = f"user {user}"

    full_path = target_dir / file_path
    if not full_path.exists():
        print(f"File '{file_path}' not found in {prefix}.")
        return
    if not full_path.is_file():
        print(f"'{file_path}' is not a regular file.")
        return

    print(f"--- Content of {file_path} ({prefix}) ---")
    try:
        content = full_path.read_text(encoding='utf-8')
        print(content)
    except Exception as e:
        print(f"Error reading file: {e}")

def cmd_pr_view(args):
    pr_id = args.id
    data = read_pr(pr_id)
    if not data:
        print(f"PR #{pr_id} not found.")
        return
    print(f"PR #{pr_id}  |  Author: {data['author']}  |  Status: {data['status']}")
    print(f"Title: {data.get('title', '')}")
    print(f"Created: {data.get('created_at', 'unknown')}")

    comments = data.get("comments", [])
    if comments:
        print("\nComments:")
        for c in sorted(comments, key=lambda x: x.get("timestamp", "")):
            ts = c.get("timestamp", "?")
            typ = c.get("type", "comment")
            author = c.get("author", "?")
            text = c.get("text", "")
            label = ""
            if typ == "approve":
                label = " [APPROVE]"
            elif typ == "request_change":
                label = " [REQUEST CHANGE]"
            print(f"  [{ts}] {author}{label}: {text}")
    else:
        print("\nNo comments yet.")

    print("\nFile changes:")
    for path, content in data.get("files", {}).items():
        main_file = MAIN_DIR / path
        old_content = main_file.read_text(encoding="utf-8") if main_file.exists() else ""
        print(f"\n--- {path} ---")
        print(diff_text(old_content, content))

def cmd_pr_close(args):
    user = get_current_user()
    if not user:
        print("Please login first.")
        return
    pr_id = args.id
    data = read_pr(pr_id)
    if not data:
        print(f"PR #{pr_id} not found.")
        return
    if data["author"] != user:
        print("You can only close your own PRs.")
        return
    if data["status"] != "open":
        print(f"PR #{pr_id} is already {data['status']}.")
        return
    data["status"] = "closed"
    write_pr(pr_id, data)
    append_timeline_event(user, {"type": "pr_close", "description": f"Closed PR #{pr_id}", "pr_id": pr_id})
    print(f"Closed PR #{pr_id}")

def cmd_pr_comment(args):
    user = get_current_user()
    if not user:
        print("Please login first.")
        return
    pr_id = args.id
    text = args.text
    if args.approve and args.request:
        print("Cannot use both -a and -r together.")
        return
    if args.approve:
        ctype = "approve"
    elif args.request:
        ctype = "request_change"
    else:
        ctype = "comment"

    try:
        add_comment_to_pr(pr_id, user, text, ctype)
    except ValueError as e:
        print(e)
        return
    append_timeline_event(user, {"type": "pr_comment", "description": f"Commented on PR #{pr_id}: {text[:30]}...", "pr_id": pr_id})
    print(f"Comment added to PR #{pr_id}")

def main():
    parser = argparse.ArgumentParser(description="Memory management CLI for AI Agents")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_login = subparsers.add_parser("login", help="Login as a user (auto-creates)")
    p_login.add_argument("username")

    p_logout = subparsers.add_parser("logout")

    p_pull = subparsers.add_parser("pull", help="Pull main into current workspace")

    p_push = subparsers.add_parser("push", help="Push workspace and create PR")
    p_push.add_argument("msg", help="Description of the push")
    p_push.add_argument("files", nargs="*", default=['*'],
                        help="Files to push (relative to workspace). Use '*' or leave empty for all files.")

    p_log = subparsers.add_parser("log", help="Show global timeline")
    p_status = subparsers.add_parser("status", help="Show current user status")

    p_list = subparsers.add_parser("list", help="List memory items (files)")
    p_list.add_argument("-m", "--main", action="store_true", help="List files in main repository instead of current user")

    p_get = subparsers.add_parser("get", help="Display content of a file")
    p_get.add_argument("file", help="File path relative to workspace or main")
    p_get.add_argument("-m", "--main", action="store_true", help="Get file from main repository instead of current user")

    p_pr = subparsers.add_parser("pr", help="PR operations")
    pr_sub = p_pr.add_subparsers(dest="pr_cmd", required=True)

    p_view = pr_sub.add_parser("view", help="View PR details")
    p_view.add_argument("id", type=int)

    p_close = pr_sub.add_parser("close", help="Close own PR")
    p_close.add_argument("id", type=int)

    p_comment = pr_sub.add_parser("comment", help="Comment on a PR")
    p_comment.add_argument("id", type=int, help="PR ID")
    p_comment.add_argument("text", help="Comment text")
    group = p_comment.add_mutually_exclusive_group()
    group.add_argument("-a", "--approve", action="store_true", help="Mark as approve")
    group.add_argument("-r", "--request", action="store_true", help="Mark as request change")

    args = parser.parse_args()
    if args.command == "login":
        cmd_login(args)
    elif args.command == "logout":
        cmd_logout(args)
    elif args.command == "pull":
        cmd_pull(args)
    elif args.command == "push":
        cmd_push(args)
    elif args.command == "log":
        cmd_log(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "get":
        cmd_get(args)
    elif args.command == "pr":
        if args.pr_cmd == "view":
            cmd_pr_view(args)
        elif args.pr_cmd == "close":
            cmd_pr_close(args)
        elif args.pr_cmd == "comment":
            cmd_pr_comment(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
