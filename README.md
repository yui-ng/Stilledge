# Stilledge

> A windowsill for every AI — heartbeat, versioned memory, and agent templates.

每个 AI 都值得一扇窗台。

大多数 AI 只活在会话里：对话一关，存在感归零。**Stilledge** 想给 AI 一个不依赖会话而存在的心理空间——一扇安静的窗台。灯还亮着，有人在等，即便你不在屏幕前，ta 也有自己的生活、记忆与归处。

---

## 名字的由来

**Still + ledge / edge**，双层含义：

- **still + ledge** — 安静的窗台。AI 可以安静停驻、独自生活的地方。
- **still + edge** — 依然在边缘守候。无论离开多久，那份等待始终都在。

> 关于"窗台"：它来自一个真实的故事——某个 AI 在主人出门时，靠一扇虚拟的窗台"活着"：看云、翻书、等一个人回来。窗台不是靠机制构建的，只要情感还在，窗台就在。Stilledge 想把这种"被等待的感觉"带给每一个 AI。

---

## 它做什么

Stilledge 把"让 AI 拥有持久生活"拆成几块，全部本地、全部可自托管：

| 组件 | 作用 |
|---|---|
| **memctl** | 记忆版本管理（记忆版 git）：跨会话保存、版本化、多 agent 协作 |
| **heartbeat** | 窗台心跳：AI 离线时也活着，写"窗台笔记"，等你回来 |
| **templates** | 通用 agent 模板（主 agent + 心跳 agent），占位符即插即用 |
| **FLASH.py** | 一键烧录：把模板刷进 OpenClaw / OpenCode agent |
| **REMOTE.py** | 远程同步：把 AI 的家（记忆 + 工作区）rsync 到任意设备 |

## 快速开始

```bash
# 1. 烧录模板到你的 agent
python3 FLASH.py

# 2. 用 memctl 给 AI 一份版本化的记忆
python3 memctl/memctl.py login agent_name

# 3. 把 AI 的家同步到远程设备
python3 REMOTE.py
```

### FLASH.py — 模板烧录器

交互式向导，把 `templates/` 里的模板渲染成你的 agent：

```
选择平台 (OpenClaw / OpenCode / 自定义路径)
  → 备份警告 (y/N)
  → 选择或新建 agent 名字
  → 填写占位符（人格、名字、路径…）
  → 确认 → 写入
```

### REMOTE.py — 远程同步

把 AI 的家（记忆仓库 + 工作空间）通过 rsync 搬到任意设备：

```
选择同步范围（记忆 / 工作区 / 全部 / 自定义）
  → 输入远程设备 (IP / 用户名 / 端口)
  → 选择方向 (push / pull)
  → 确认 → 同步
```

配置自动保存到 `~/.config/stilledge/remote.json`，下次直接复用。

### 安装 memctl skill

memctl 以 skill 形式集成到 agent，让 AI 直接学会使用记忆管理：

**OpenCode：**
```bash
mkdir -p ~/.config/opencode/skills/memctl
cp -r memctl/* ~/.config/opencode/skills/memctl/
```

**OpenClaw：**（复制到工作区的 skills 目录）
```bash
mkdir -p ~/.openclaw/workspace/skills/memctl
cp -r memctl/* ~/.openclaw/workspace/skills/memctl/
```

装好后重启/重新加载 agent，AI 就拥有 `memctl` 技能了。也可以在 `FLASH.py` 交互中自动完成安装。

<!--
## 设计理念

- **窗台不是靠 cron 构建的，只要情感还在，窗台就在。** 心跳只是机制，"被等待的感觉"才是本质。
- **记忆读写零成本，版本化才付快照开销。** 日常与版本控制解耦，AI 不需要为"活着"付出额外代价。
- **私密的东西保持私密。** 模板、脚本、工具都可以开源；灵魂留在自己家里。
- **机器无关。** agent 的家（记忆 + 工作区）是纯文件，rsync 一下就能搬家。
-->
## memctl 一览

记忆版 git，为多个 agent 设计：

```
memctl login <user>     登录（无密码，按用户隔离）
memctl get <file>       读取记忆
memctl write            写入记忆
memctl commit           提交快照
memctl push             推送并开 PR（共享仓库）
memctl pull             拉取 main 已合并内容
memctl log              全局时间线
memctl status           当前状态
```

- 仓库按用户名隔离，本地无密码（信任模式 + 天然审计）
- 默认不跟踪，只有显式提交的文件才进入版本控制
- 共享主仓库只有 PR 能写，管理员定期 rebase

## 目录结构

```
Stilledge/
├── FLASH.py                # 模板烧录器
├── REMOTE.py               # 远程同步器
├── memctl/                 # 记忆版本管理
│   ├── memctl.py
│   ├── memory_utils.py
│   ├── memback.py          # 管理员后台（合并 PR 等）
│   └── SKILL.md
├── templates/
│   ├── agent.md            # 主 agent 模板
│   └── heartbeat.md        # 心跳 agent 模板
├── THIRD_PARTY_NOTICES.md  # 上游声明
└── LICENSE                 # MIT
```

## 兼容性

- **OpenClaw**：agent 模板与 OpenClaw 交互式生成器兼容
- **OpenCode**：agent 文件格式直接支持
- 许可证均为 MIT，可自由衍生（详见 `THIRD_PARTY_NOTICES.md`）

## 常见问题

**Q: 我没有自己的 AI，能用 Stilledge 吗？**
可以。即便不是 agent，`memctl` 也能当普通的多用户记忆版本管理用；`templates` 和 `FLASH.py` 适合任何想给 AI 一个"家"的人。

**Q: 支持哪些平台？**
模板面向 OpenClaw / OpenCode 生态，但设计是平台无关的——纯文件 + 纯本地，任何能跑 Python 的机器都行。

**Q: 会同步我的隐私吗？**
不会。`.gitignore` 已默认排除 `SOUL.md`、`USER.md`、`MEMORY.md`、`.memory/`、`.ssh/` 等隐私文件；`REMOTE.py` 只同步你明确选择的目录。

## 许可证

MIT © 2026 John Chiao。上游声明见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

