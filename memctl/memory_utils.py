# memory_utils.py - Shared utilities for memory management
# Copyright (c) 2026 John Chiao
# SPDX-License-Identifier: MIT

import os
import json
import shutil
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

ROOT = Path(os.path.expanduser("~/.memory"))
MAIN_DIR = ROOT / "main"
PRS_DIR = MAIN_DIR / "prs"
AGENTS_DIR = ROOT / "agents"
SESSION_FILE = ROOT / "session"
TIMELINE_FILE = "TIMELINE.json"

def ensure_dirs():
    """创建必要的目录结构"""
    for d in [ROOT, MAIN_DIR, PRS_DIR, AGENTS_DIR]:
        d.mkdir(parents=True, exist_ok=True)

def get_current_user() -> Optional[str]:
    """从会话文件读取当前登录用户名"""
    if SESSION_FILE.exists():
        return SESSION_FILE.read_text().strip()
    return None

def set_current_user(username: str):
    """写入会话文件"""
    SESSION_FILE.write_text(username)

def clear_session():
    """登出时删除会话"""
    if SESSION_FILE.exists():
        SESSION_FILE.unlink()

def get_user_dir(username: str) -> Path:
    return AGENTS_DIR / username

def ensure_user(username: str):
    """确保用户目录存在，并创建空的TIMELINE.json（如不存在）"""
    user_dir = get_user_dir(username)
    user_dir.mkdir(parents=True, exist_ok=True)
    tl = user_dir / TIMELINE_FILE
    if not tl.exists():
        tl.write_text(json.dumps([], indent=2))

def read_timeline(username: str) -> List[Dict[str, Any]]:
    """读取用户的TIMELINE.json"""
    tl_file = get_user_dir(username) / TIMELINE_FILE
    if not tl_file.exists():
        return []
    return json.loads(tl_file.read_text())

def append_timeline_event(username: str, event: Dict[str, Any]):
    """向用户TIMELINE追加事件"""
    tl = read_timeline(username)
    event.setdefault("timestamp", datetime.datetime.now().isoformat())
    tl.append(event)
    tl_file = get_user_dir(username) / TIMELINE_FILE
    tl_file.write_text(json.dumps(tl, indent=2))

def list_users() -> List[str]:
    """返回所有存在的用户名（目录名）"""
    if AGENTS_DIR.exists():
        return [d.name for d in AGENTS_DIR.iterdir() if d.is_dir()]
    return []

def get_pr_path(pr_id: int) -> Path:
    return PRS_DIR / f"{pr_id}.json"

def get_next_pr_id() -> int:
    """基于现有PR文件生成下一个ID"""
    existing = [f.stem for f in PRS_DIR.glob("*.json") if f.stem.isdigit()]
    if not existing:
        return 1
    return max(int(x) for x in existing) + 1

def read_pr(pr_id: int) -> Optional[Dict[str, Any]]:
    path = get_pr_path(pr_id)
    if not path.exists():
        return None
    return json.loads(path.read_text())

def write_pr(pr_id: int, data: Dict[str, Any]):
    path = get_pr_path(pr_id)
    path.write_text(json.dumps(data, indent=2))

def copy_main_to_user(username: str):
    """将main目录下的所有文件复制到用户目录（覆盖）"""
    user_dir = get_user_dir(username)
    if MAIN_DIR.exists():
        for item in MAIN_DIR.rglob("*"):
            if item.is_file() and item.parent != PRS_DIR and not str(item).startswith(str(PRS_DIR)):
                rel = item.relative_to(MAIN_DIR)
                target = user_dir / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, target)

def copy_user_to_pr(username: str, pr_id: int) -> Dict[str, Any]:
    """将用户目录下的所有文件（除TIMELINE.json）复制到一个字典，用于PR"""
    user_dir = get_user_dir(username)
    files_dict = {}
    for item in user_dir.rglob("*"):
        if item.is_file() and item.name != TIMELINE_FILE:
            rel = str(item.relative_to(user_dir))
            files_dict[rel] = item.read_text(encoding="utf-8")
    return files_dict

def apply_pr_to_main(pr_data: Dict[str, Any]):
    """将PR中的文件内容写入main目录（覆盖）"""
    for rel_path, content in pr_data.get("files", {}).items():
        target = MAIN_DIR / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

def diff_text(a: str, b: str) -> str:
    """生成简单的统一diff格式（仅作示意）"""
    import difflib
    a_lines = a.splitlines(keepends=True)
    b_lines = b.splitlines(keepends=True)
    diff = difflib.unified_diff(a_lines, b_lines, fromfile="main", tofile="pr")
    return "".join(diff)

def add_comment_to_pr(pr_id: int, author: str, text: str, comment_type: str = "comment"):
    """给 PR 添加评论，comment_type 可为 'comment'、'approve'、'request_change'"""
    data = read_pr(pr_id)
    if not data:
        raise ValueError(f"PR #{pr_id} not found")
    if "comments" not in data:
        data["comments"] = []
    comment = {
        "author": author,
        "timestamp": datetime.datetime.now().isoformat(),
        "text": text,
        "type": comment_type,
    }
    data["comments"].append(comment)
    write_pr(pr_id, data)
