---
name: memctl
description: Memory Control
---



# memctl 记忆管理技能

## 目的
本技能使 AI Agent 能够通过命令行工具 `python memctl.py` 管理其**持久化记忆**，与共享记忆仓库交互。Agent 可以将工作区中的文件（记忆、状态、知识片段等）推送到中央存储（`main` 仓库），拉取他人的更新，查看全局时间线，以及管理拉取请求（PR）。

## 适用场景
- Agent 需要跨会话保存状态或知识。
- 多个 Agent 协作共享信息（如项目进度、事实库、配置）。
- Agent 希望查看历史变更记录或对比自己与他人的工作。

## 前置条件
- Python 3.6+ 已安装。
- `memctl.py` 和 `memory_utils.py` 位于同一目录，且具有执行权限（或使用 `python memctl.py` 调用）。
- 工作区根目录 `~/.memory` 会在首次运行命令时自动创建。
- 每个 Agent 拥有唯一账户名（如 `agent_alice`），使用 `python memctl.py login` 登录。

## ⚠️ 重要提醒
- **`memback.py` 是后台管理程序**，仅供系统管理员使用，用于合并 PR、管理用户等。**普通 Agent 切勿查看或运行 `memback.py`**，以免干扰仓库状态。
- **严禁登录其他 Agent 的账号**，每个 Agent 应使用自己专属的用户名。登录他人账户会破坏协作秩序并导致时间线混淆。
- 所有命令均基于本地文件系统，无需网络。

## 核心命令速览

| 命令 | 说明 |
|------|------|
| `python memctl.py login <用户名>` | 登录（无密码，自动创建用户目录）。 |
| `python memctl.py logout` | 登出当前用户。 |
| `python memctl.py pull` | 从 `main` 拉取所有文件到当前用户工作区（覆盖同名文件）。 |
| `python memctl.py push <描述> [文件...]` | 推送指定文件到 `main` 并创建 PR。若省略文件或指定 `*`，则推送所有文件（自动排除 `TIMELINE.json`）。 |
| `python memctl.py log` | 显示所有 Agent 的全局操作时间线。 |
| `python memctl.py status` | 查看当前用户的工作区文件数量及未关闭的 PR。 |
| `python memctl.py list [-m]` | 列出当前用户工作区（默认）或 `main` 仓库（`-m`）的所有文件。 |
| `python memctl.py get <文件> [-m]` | 显示当前用户工作区（默认）或 `main` 仓库（`-m`）中指定文件的内容。 |
| `python memctl.py pr view <ID>` | 查看 PR 的详细描述、所有评论和文件改动 diff。 |
| `python memctl.py pr close <ID>` | 关闭自己发起的 PR（只能关闭自己的 PR）。 |
| `python memctl.py pr comment <ID> <评论内容> [-a] [-r]` | 对 PR 发表评论；`-a` 标记为批准，`-r` 标记为请求修改（二者互斥）。 |

## 典型工作流

### 1. 首次登录并创建工作区
```bash
python memctl.py login agent_bob
```
登录后，`~/.memory/agents/agent_bob/` 自动创建，其中包含一个空的 `TIMELINE.json`（系统文件，请勿手动修改）。

### 2. 在本地工作区创建或修改记忆文件
Agent 可以将任意文件（如 `notes.txt`、`config.yaml`、`knowledge.json`）放入其工作区目录（`~/.memory/agents/agent_bob/`）。这些文件将作为记忆项。

### 3. 查看当前工作区内容
```bash
python memctl.py list
```
输出示例：
```
Files in user agent_bob:
  docs/plan.md
  notes.txt
  config.yaml
```

### 4. 查看文件内容
```bash
python memctl.py get notes.txt
```

### 5. 推送变更并创建 PR
推送所有文件：
```bash
python memctl.py push "更新笔记和配置"
```
或仅推送部分文件：
```bash
python memctl.py push "仅修复配置" config.yaml
```
成功后将显示 PR 编号（如 `#1`），并记录到时间线中。

### 6. 拉取 `main` 最新变更
```bash
python memctl.py pull
```
这会将 `main` 中所有已合并的文件复制到当前工作区，覆盖本地同名文件。

### 7. 查看全局活动
```bash
python memctl.py log
```
输出按时间排序的事件，帮助了解其他 Agent 的操作。

### 8. 查看 PR 细节
```bash
python memctl.py pr view 1
```
显示 PR 的标题、作者、状态、所有评论以及每个文件的 diff。

### 9. 评论 PR
```bash
# 普通评论
python memctl.py pr comment 1 "我觉得需要补充更多细节。"

# 批准
python memctl.py pr comment 1 "看起来没问题！" -a

# 请求修改
python memctl.py pr comment 1 "请修正 note.txt 中的拼写错误。" -r
```
评论会显示在 `pr view` 中，供所有 Agent 参考。批准/请求修改标记仅作审查参考，不会自动改变 PR 状态。

### 10. 关闭自己发起的 PR
如果 PR 不再需要（例如已过时或错误），可自行关闭：
```bash
python memctl.py pr close 1
```
（只有 PR 作者可关闭；管理员可通过 `memback` 合并或强制关闭，但普通 Agent 不应操作。）

### 11. 检查当前状态
```bash
python memctl.py status
```
显示当前工作区文件数量及自己名下未关闭的 PR 列表。

## 协作场景示例
- Agent A 修改 `knowledge.json` 并推送 PR #1。
- Agent B 拉取 `main`（此时尚未包含 A 的改动），然后推送自己的改动创建 PR #2。
- 管理员（使用 `memback`）审查并合并 PR #1，随后 Agent B 可再次 `pull` 获得 A 的更新，解决潜在冲突。
- Agent B 完成工作后关闭或更新其 PR。

## 注意事项
- 所有命令均基于本地文件系统，无需网络或外部服务。
- `push` 操作不会自动合并到 `main`，仅创建 PR，需管理员合并后才生效。
- `pull` 仅同步 `main` 中**已合并**的内容，不包含尚未合并的 PR。
- 文件路径相对于用户工作区或 `main` 目录，支持子目录。
- `TIMELINE.json` 是系统文件，不会被 `push` 包含，也不会在 `list` 中显示。
- 评论功能仅用于协作讨论，不改变 PR 状态。

## 故障排查
- **“Not logged in”**：先执行 `python memctl.py login <用户名>`。
- **“No files to push”**：确保工作区存在非 `TIMELINE.json` 的文件，或正确指定了文件路径。
- **文件不存在警告**：`push` 时指定的文件若不存在会被跳过，请检查路径是否正确。
- **权限错误**：确保 `~/.memory` 目录可读写。

## ⚠️ 文件操作安全守则（血的教训，2026-08-08）
- **TIMELINE.json 是 delta DB**，绝对禁止删除、移动、覆盖或手动修改。
- 清理文件前**先列出清单**，确认要删的是临时文件，且不含系统文件（TIMELINE.json、session、prs/*.json）。
- **优先用 `trash` 而非 `rm`**（Arch 装 trash-cli）。即使删自己的文件也一样。
- 只清理**自己创建**的临时文件；拿不准就先停下询问，不先执行。

## 扩展性
Agent 可根据需要自定义工作区结构，例如按主题或日期组织子目录。`memctl` 对文件类型无限制，支持任意文本或二进制文件（但 diff 功能仅适用于文本文件）。


