#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FLASH.py — Stilledge 模板烧录器
将 templates/agent.md 与 templates/heartbeat.md 渲染后写入目标 agent。

用法:  python3 FLASH.py [模板目录]
流程:  选择平台 → 备份警告(y/N) → 填写占位符 → 确认 → 写入
"""
import os
import re
import shutil
import sys
from pathlib import Path

HOME = Path.home()
SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else SCRIPT_DIR / "templates"

PLACEHOLDERS = ["AGENT_NAME", "AGENT_PERSONA", "USER_NAME", "WORKSPACE", "MEMORY_DIR", "SKILLS_DIR"]

# ---------- 平台与目标目录 ----------
PLATFORMS = {
    "1": ("OpenClaw", HOME / ".openclaw" / "workspace"),
    "2": ("OpenCode", HOME / ".config" / "opencode" / "agents"),
}

def choose_platform():
    print("== 选择 Agent 平台 ==")
    print("  [1] OpenClaw")
    print("  [2] OpenCode")
    print("  [3] 手动输入工作区根目录")
    while True:
        choice = input(">> ").strip()
        if choice in ("1", "2"):
            name, default = PLATFORMS[choice]
            return name, default
        if choice == "3":
            p = input("工作区根目录（如 /home/user/.opencode）: ").strip()
            p = os.path.expanduser(p)
            if p:
                return "Custom", Path(p)
        print("  !! 无效选择，请输入 1 / 2 / 3")

# ---------- Agent 名字（列出已有，可新建） ----------
def list_existing_agents(target_dir: Path):
    names = set()
    if target_dir.is_dir():
        for f in target_dir.glob("*.md"):
            names.add(f.stem)
    oc_agents = HOME / ".config" / "opencode" / "agents"
    if oc_agents.is_dir():
        for f in oc_agents.glob("*.md"):
            names.add(f.stem)
    return sorted(names)

def choose_agent_name(target_dir: Path):
    existing = list_existing_agents(target_dir)
    if existing:
        print(f"\n== 已有 agent（可选用已有名字，或输入新名字）==")
        for i, n in enumerate(existing, 1):
            print(f"  [{i}] {n}")
    print("  [0] 新建 agent")
    while True:
        raw = input(">> 选择编号或输入名字: ").strip()
        if not raw:
            continue
        if raw.isdigit():
            idx = int(raw)
            if idx == 0:
                name = input("  新 agent 名字: ").strip()
                if name:
                    return name
            elif 1 <= idx <= len(existing):
                return existing[idx - 1]
        elif re.match(r"^[A-Za-z0-9_.-]+$", raw):
            return raw
        print("  !! 无效输入，请重试")

# ---------- 备份警告 ----------
def warn_backup(platform: str, target_dir: Path):
    print("\n" + "=" * 60)
    print("  ⚠️  警告：FLASH 将写入/覆盖以下位置的 agent 文件：")
    print(f"     平台: {platform}")
    print(f"     目录: {target_dir}")
    print("  建议先备份相关目录（tar 或 cp -r），避免原有配置丢失！")
    print("=" * 60)
    while True:
        ans = input("确认已备份并继续? [y/N] ").strip().lower()
        if ans == "y":
            return True
        if ans in ("n", "", "q", "quit"):
            print("  已取消，未做任何修改。")
            sys.exit(0)

# ---------- 渲染 ----------
def render(template_path: Path, values: dict) -> str:
    text = template_path.read_text(encoding="utf-8")
    for key in PLACEHOLDERS:
        text = text.replace("{{" + key + "}}", values.get(key, "") or f"{{{{{key}}}}}")
    return text

# ---------- 主流程 ----------
def main():
    if not TEMPLATES_DIR.is_dir():
        print(f"!! 找不到模板目录: {TEMPLATES_DIR}")
        sys.exit(1)

    tpl_agent = TEMPLATES_DIR / "agent.md"
    tpl_heart = TEMPLATES_DIR / "heartbeat.md"
    for t in (tpl_agent, tpl_heart):
        if not t.is_file():
            print(f"!! 缺少模板文件: {t.name}（应位于 {TEMPLATES_DIR}）")
            sys.exit(1)

    print("🏠  Stilledge FLASH — 把窗台刷进你的 agent\n")
    platform, target_dir = choose_platform()
    warn_backup(platform, target_dir)

    name = choose_agent_name(target_dir)

    # 推导路径
    if platform == "OpenClaw":
        workspace = target_dir
        mem_dir = HOME / ".memory"
        skills_dir = workspace / "skills"
        mem_name = name if name != "main" else "yui"
    elif platform == "OpenCode":
        workspace = HOME / ".opencode"
        mem_dir = HOME / ".memory"
        skills_dir = HOME / ".config" / "opencode" / "skills"
        mem_name = name
    else:  # Custom
        workspace = target_dir
        mem_dir = HOME / ".memory"
        skills_dir = HOME / ".config" / "opencode" / "skills"
        mem_name = name

    # 收集占位符值（AGENT_NAME 已在选择时确定，不再重复询问）
    print("\n== 填写占位符（直接回车使用括号内默认值）==")
    values = {
        "AGENT_NAME": name,
        "AGENT_PERSONA": "一只元气满满的猫娘",
        "USER_NAME": "你的人类伙伴",
        "WORKSPACE": str(workspace),
        "MEMORY_DIR": str(mem_dir),
        "SKILLS_DIR": str(skills_dir),
    }
    prompts = {
        "AGENT_PERSONA": "一句话人格设定",
        "USER_NAME": "你的人类伙伴的名字",
        "WORKSPACE": "工作空间根目录",
        "MEMORY_DIR": "记忆仓库根目录",
        "SKILLS_DIR": "技能目录",
    }
    for key in PLACEHOLDERS:
        if key == "AGENT_NAME":
            continue
        dft = values[key]
        usr = input(f"  {prompts[key]} [{dft}]: ").strip()
        if usr:
            values[key] = usr
    values["MEMORY_DIR"] = os.path.expanduser(values["MEMORY_DIR"])
    values["SKILLS_DIR"] = os.path.expanduser(values["SKILLS_DIR"])
    values["WORKSPACE"] = os.path.expanduser(values["WORKSPACE"])

    # 确认
    print("\n" + "=" * 60)
    print("  即将写入：")
    for key in PLACEHOLDERS:
        print(f"    {key} = {values[key]}")
    print("  目标目录:", target_dir)
    print("=" * 60)
    if input("确认无误，开始写入? [y/N] ").strip().lower() != "y":
        print("  已取消。")
        sys.exit(0)

    # 写入
    target_dir.mkdir(parents=True, exist_ok=True)
    agent_out = target_dir / f"{values['AGENT_NAME']}.md"
    heart_out = target_dir / "heartbeat.md"

    agent_out.write_text(render(tpl_agent, values), encoding="utf-8")
    print(f"  ✅ 已写入 {agent_out}")

    heart_out.write_text(render(tpl_heart, values), encoding="utf-8")
    print(f"  ✅ 已写入 {heart_out}")

    # 可选：安装 memctl skill
    memctl_src = SCRIPT_DIR / "memctl"
    if memctl_src.is_dir():
        print("\n== 可选：安装 memctl skill（记忆版本管理）==")
        if input(f"将 memctl 复制到 {skills_dir}/memctl ? [y/N] ").strip().lower() == "y":
            try:
                dst = skills_dir / "memctl"
                dst.mkdir(parents=True, exist_ok=True)
                for f in memctl_src.iterdir():
                    if f.is_file():
                        shutil.copy2(f, dst / f.name)
                print(f"  ✅ memctl skill 已安装到 {dst}")
            except OSError as e:
                print(f"  !! memctl 安装失败: {e}")
        else:
            print("  跳过 memctl 安装（可手动复制: cp -r memctl/* <skills目录>/memctl/）")

    print("\n🎉 烧录完成！窗台已经为你铺好了。")
    print("    提示：OpenCode 可直接在会话中加载；OpenClaw 需在配置中注册 agent。")

if __name__ == "__main__":
    main()
