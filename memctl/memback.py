#!/usr/bin/env python3
# memback.py - Backend management for memory system
# Copyright (c) 2026 John Chiao
# SPDX-License-Identifier: MIT

import argparse
import sys
from pathlib import Path
from memory_utils import *

def cmd_merge(args):
    pr_id = args.id
    data = read_pr(pr_id)
    if not data:
        print(f"PR #{pr_id} not found.")
        return
    if data["status"] != "open":
        print(f"PR #{pr_id} is already {data['status']}.")
        return
    apply_pr_to_main(data)
    data["status"] = "merged"
    write_pr(pr_id, data)
    author = data["author"]
    append_timeline_event(author, {"type": "pr_merge", "description": f"Merged PR #{pr_id}", "pr_id": pr_id})
    print(f"PR #{pr_id} merged into main.")

def cmd_pr_close_admin(args):
    pr_id = args.id
    data = read_pr(pr_id)
    if not data:
        print(f"PR #{pr_id} not found.")
        return
    if data["status"] == "closed" or data["status"] == "merged":
        print(f"PR #{pr_id} already {data['status']}.")
        return
    data["status"] = "closed"
    write_pr(pr_id, data)
    author = data["author"]
    append_timeline_event(author, {"type": "pr_close_admin", "description": f"Admin closed PR #{pr_id}", "pr_id": pr_id})
    print(f"PR #{pr_id} closed by admin.")

def cmd_user_list(args):
    users = list_users()
    print("Registered users:")
    for u in users:
        print(f"  - {u}")

def cmd_user_create(args):
    username = args.username
    ensure_dirs()
    ensure_user(username)
    print(f"User {username} created.")

def cmd_user_delete(args):
    username = args.username
    user_dir = get_user_dir(username)
    if not user_dir.exists():
        print(f"User {username} does not exist.")
        return
    import shutil
    shutil.rmtree(user_dir)
    print(f"User {username} deleted.")

def main():
    parser = argparse.ArgumentParser(description="Backend management for memory system")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_merge = subparsers.add_parser("merge", help="Merge a PR into main")
    p_merge.add_argument("id", type=int)

    p_pr_close = subparsers.add_parser("pr-close", help="Close any PR as admin")
    p_pr_close.add_argument("id", type=int)

    p_user = subparsers.add_parser("user", help="User management")
    user_sub = p_user.add_subparsers(dest="user_cmd", required=True)
    p_list = user_sub.add_parser("list")
    p_create = user_sub.add_parser("create")
    p_create.add_argument("username")
    p_delete = user_sub.add_parser("delete")
    p_delete.add_argument("username")

    args = parser.parse_args()
    if args.command == "merge":
        cmd_merge(args)
    elif args.command == "pr-close":
        cmd_pr_close_admin(args)
    elif args.command == "user":
        if args.user_cmd == "list":
            cmd_user_list(args)
        elif args.user_cmd == "create":
            cmd_user_create(args)
        elif args.user_cmd == "delete":
            cmd_user_delete(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
