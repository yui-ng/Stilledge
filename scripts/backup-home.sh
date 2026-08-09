#!/usr/bin/env bash
# =============================================================
# 备份脚本：home 目录迁移清单 → tar.gz（带 pv 进度条）
# 用于机器间迁移（如旧笔记本 → 新台式机）
# 依赖：pv（Arch: pacman -S pv；Debian: apt install pv）
# 用法：bash backup-home.sh
# 输出：~/backup-home-YYYYMMDD-HHMM.tar.gz
# =============================================================
set -euo pipefail

SRC="$HOME"
STAMP="$(date +%Y%m%d-%H%M)"
OUT="$HOME/backup-home-${STAMP}.tar.gz"

echo "==> 备份开始: $OUT"

# ---------- 收集包含项与排除项 ----------
INCLUDES=()
EXCLUDES=()

# .memory 记忆库（若使用 memctl，必须带！）
[ -d "$SRC/.memory" ] && INCLUDES+=(".memory")

# .opencode 工作空间（排除 node_modules）
[ -d "$SRC/.opencode" ] && { INCLUDES+=(".opencode"); EXCLUDES+=(".opencode/node_modules"); }

# .config 全量（排除纯缓存大块；即时通讯保留登录态）
[ -d "$SRC/.config" ] && INCLUDES+=(".config")
EXCLUDES+=(
  ".config/QQ/versions"      # QQ 程序本体 ~900M，重装可得
  ".config/mozilla"          # 浏览器缓存 ~280M
  ".config/chromium"         # 浏览器缓存 ~110M
)

# .local 挑重点（排除大缓存）
[ -d "$SRC/.local" ] && INCLUDES+=(".local")
EXCLUDES+=(
  ".local/share/icons"       # ~650M 图标主题，新机重装
  ".local/share/pnpm"        # ~620M 包缓存
  ".local/share/zed"         # ~220M 编辑器数据
  ".local/share/baloo"       # ~150M 索引
  ".local/share/akonadi"     # ~130M 邮件索引
  ".local/share/uv"          # ~110M 包缓存
  ".local/share/Trash"       # ~100M 回收站
  ".local/share/krita"       # ~90M 绘画数据
  ".local/share/flatpak"     # 扁平包
)

# ---------- 计算预计总大小（未压缩，供 pv 显示百分比） ----------
TOTAL=0
for p in "${INCLUDES[@]}"; do
  s=$(du -sb "$SRC/$p" 2>/dev/null | cut -f1)
  TOTAL=$((TOTAL + ${s:-0}))
done
for x in "${EXCLUDES[@]}"; do
  s=$(du -sb "$SRC/$x" 2>/dev/null | cut -f1)
  TOTAL=$((TOTAL - ${s:-0}))
done
[ "$TOTAL" -lt 0 ] && TOTAL=0
echo "==> 预计打包 $(numfmt --to=iec "$TOTAL" 2>/dev/null || echo "$TOTAL B")"

# ---------- 构造 tar 参数 ----------
TAR_ARGS=(-cf -)
for x in "${EXCLUDES[@]}"; do TAR_ARGS+=("--exclude=$x"); done
TAR_ARGS+=("${INCLUDES[@]}")

# ---------- 执行（tar | pv | gzip） ----------
cd "$SRC"
tar "${TAR_ARGS[@]}" 2>/dev/null | pv -s "$TOTAL" -W | gzip -1 > "$OUT"
echo ""
echo "==> 完成: $OUT"
echo "==> 大小: $(du -h "$OUT" | cut -f1)"

# ---------- 提示 ----------
if [ ! -e "$SRC/.config/clash" ] && [ ! -e "$SRC/.config/mihomo" ]; then
  echo "!! 提示: 本机未找到 clash 配置，若旧机有，需手动拷贝"
fi
