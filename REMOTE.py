#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
REMOTE.py — 用 rsync 把 agent 的家（记忆 + 工作区）同步到远程设备
用法:  python3 REMOTE.py
流程:  选择同步范围 → 输入远程设备(IP/用户名/端口) → 选择方向 → 确认 → rsync 执行

配置文件（可选，保存后下次自动读取作为默认值）:
  ~/.config/stilledge/remote.json
"""
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path

HOME = Path.home()
CONFIG_PATH = Path(os.environ.get("XDG_CONFIG_HOME", HOME / ".config")) / "stilledge" / "remote.json"

# 默认同步范围：agent 的家
DEFAULT_PATHS = {
    "记忆仓库": HOME / ".memory",
    "工作空间": HOME / ".opencode",
}

def load_config() -> dict:
    if CONFIG_PATH.is_file():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}

def save_config(cfg: dict):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  💾 配置已保存: {CONFIG_PATH}")

def ask(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    val = input(f"  {prompt}{suffix}: ").strip()
    return val or default

def rsync_one(local: Path, remote_target: str, direction: str, port: str, dry: bool):
    local_s = str(local)
    if direction == "push":
        src, dst = local_s.rstrip("/") + "/", remote_target
    else:  # pull
        src, dst = remote_target, local_s.rstrip("/") + "/"
    cmd = [
        "rsync", "-avz", "--progress", "--delete",
        "-e", f"ssh -p {port}",
        src, dst,
    ]
    if dry:
        cmd.insert(1, "--dry-run")
    print("  $", shlex.join(cmd))
    return subprocess.run(cmd).returncode

def main():
    print("🌐  Stilledge REMOTE — 把 agent 的家搬到远程设备\n")
    cfg = load_config()

    # 1. 同步范围
    print("== 选择同步范围 ==")
    keys = list(DEFAULT_PATHS.keys())
    for i, k in enumerate(keys, 1):
        print(f"  [{i}] {k} ({DEFAULT_PATHS[k]})")
    print(f"  [{len(keys)+1}] 全部")
    print(f"  [0] 自定义路径")
    while True:
        raw = input(">> ").strip()
        if not raw:
            continue
        if raw.isdigit():
            idx = int(raw)
            if 1 <= idx <= len(keys):
                selected = [keys[idx - 1]]
                break
            if idx == len(keys) + 1:
                selected = list(keys)
                break
            if idx == 0:
                p = input("  自定义路径: ").strip()
                if p:
                    selected = [os.path.expanduser(p)]
                    break
        print("  !! 无效选择")

    # 2. 远程设备
    print("\n== 远程设备 ==")
    host = ask("IP 或主机名", cfg.get("host", ""))
    if not host:
        print("  !! 需要远程地址")
        sys.exit(1)
    user = ask("用户名", cfg.get("user", ""))
    port = ask("SSH 端口", str(cfg.get("port", 22)))
    remote_base = ask("远程基础路径", cfg.get("remote_base", "~/"))
    # 注意：远程路径不做本地展开，`~` 留给远程端 ssh 展开

    # 3. 方向
    print("\n== 同步方向 ==")
    print("  [1] push（本地 → 远程）")
    print("  [2] pull（远程 → 本地）")
    while True:
        d = input(">> ").strip()
        if d in ("1", "2"):
            direction = "push" if d == "1" else "pull"
            break
        print("  !! 请输入 1 或 2")

    # 4. 确认
    print("\n" + "=" * 60)
    print("  即将同步：")
    for label in selected:
        print(f"    {label}: {DEFAULT_PATHS[label] if label in DEFAULT_PATHS else label}")
    print(f"  目标: {user}@{host} (端口 {port})")
    print(f"  远程基础路径: {remote_base}")
    print(f"  方向: {'本地 → 远程' if direction == 'push' else '远程 → 本地'}")
    print("=" * 60)
    if input("确认无误，开始同步? [y/N] ").strip().lower() != "y":
        print("  已取消。")
        sys.exit(0)

    # 5. 保存配置 + 执行
    save_config({"host": host, "user": user, "port": port, "remote_base": remote_base})
    print()

    results = []
    for label in selected:
        local = Path(DEFAULT_PATHS[label]) if label in DEFAULT_PATHS else Path(label)
        remote_target = f"{user}@{host}:{remote_base}/{label}"
        print(f"==> [{label}] {'推送' if direction == 'push' else '拉取'}")
        results.append(rsync_one(local, remote_target, direction, port, dry=False))

    ok = sum(1 for r in results if r == 0)
    print(f"\n{'🎉 同步完成' if ok == len(results) else '⚠️  部分失败'}（{ok}/{len(results)}）")

if __name__ == "__main__":
    main()
