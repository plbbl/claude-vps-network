# Claude Code 清理

需要同时覆盖 Claude Desktop 和浏览器时，必须继续读取 [Claude 全量本地残留](claude-residue-cleanup.md)，不能只运行网络审计。

## 先区分状态

| 类型 | 示例 | 默认处理 |
|---|---|---|
| 网络配置 | 系统代理、`HTTP_PROXY`、`HTTPS_PROXY`、`ANTHROPIC_BASE_URL` | 审计，仅删除残留 |
| Claude 设置 | 用户或项目 `settings.json` | 精确修改，保留其他配置 |
| 登录状态 | OAuth、API 登录、钥匙串 | 默认保留 |
| 历史记录 | `~/.claude/projects`、会话和历史 | 默认保留 |
| 临时缓存 | 随版本变化的临时目录 | 查明路径后再处理 |

直接删除 `~/.claude` 不是“清缓存”，可能同时删除设置、历史和登录状态。

## 只读检查

优先运行：

```bash
python3 scripts/audit_claude_network.py
```

脚本会遮蔽敏感值。需要人工复核时，按文章中的完整清单逐项执行；输出可能含代理密码或内部 URL，不要原样贴进聊天：

```bash
# 1. macOS 系统代理
scutil --proxy | grep -E "HTTPEnable|HTTPSEnable|SOCKSEnable"

# 2. 当前 Shell 的代理环境变量
env | grep -iE "proxy"

# 3. Shell 启动文件中的硬编码代理
grep -iE "proxy" ~/.zshrc ~/.bashrc ~/.profile ~/.zshenv 2>/dev/null

# 4. npm 配置
npm config get proxy
npm config get https-proxy
cat ~/.npmrc 2>/dev/null | grep -i proxy

# 5. Git 全局代理
git config --global --get http.proxy
git config --global --get https.proxy

# 6. Claude Code 用户设置
cat ~/.claude/settings.json 2>/dev/null | grep -iE "proxy|base_url|anthropic_"

# 7. Anthropic / Claude 环境变量
env | grep -iE "anthropic|claude"

# 8. Homebrew
brew config | grep -i proxy
```

再补查其他常见作用域：

```bash
# 项目级 Claude 设置
grep -iE "proxy|base_url|anthropic_" \
  ~/.claude/settings.local.json \
  .claude/settings.json .claude/settings.local.json 2>/dev/null

# yarn / pnpm
yarn config get proxy 2>/dev/null
yarn config get https-proxy 2>/dev/null
pnpm config get proxy 2>/dev/null
pnpm config get https-proxy 2>/dev/null

# 当前 Claude Code 版本
claude --version
```

检查程序可见的系统时区：

```bash
readlink /etc/localtime
node -e "console.log(Intl.DateTimeFormat().resolvedOptions().timeZone)"
```

不要输出完整值。GUI、终端、IDE 和 `tmux` 可能继承不同环境。

按文章流程，将 Mac 与 iPhone 时区设置为 `Asia/Taipei`，并用 Node 命令确认 Claude Code 进程读到的时区。

Claude Code 官方支持 `HTTP_PROXY` 与 `HTTPS_PROXY`。存在代理变量不等于异常：[官方文档](https://docs.anthropic.com/en/docs/claude-code/corporate-proxy)。

## 清理规则

- 完整复刻文章时：备份后清理所有非空 proxy、`ANTHROPIC_BASE_URL` 和第三方中转残留。
- 用户明确要求保留某项工作代理或网关时：记录为跳过项，不擅自删除。
- `127.0.0.1` 代理已无监听程序：备份后删除对应启动项。
- Base URL 或密钥曾进入聊天、日志或公开文件：删除残留并轮换密钥。
- npm 残留：经确认后运行 `npm config delete proxy` 和 `npm config delete https-proxy`。
- Git 残留：经确认后删除 `http.proxy`、`https.proxy`。
- JSON 设置：按键修改，不用正则直接删行。
- 登录异常：仅在用户要求时执行 `claude logout`。

## 安全顺序

1. 正常退出 Claude Code。
2. 记录 `claude --version` 和审计结果。
3. 只备份将要编辑的文件；备份目录权限 `700`，文件权限 `600`。
4. 删除确认过期的设置。
5. 当前终端按需执行：

   ```bash
   unset HTTP_PROXY HTTPS_PROXY ALL_PROXY http_proxy https_proxy all_proxy
   unset ANTHROPIC_BASE_URL
   ```

6. 新开终端，重新审计并测试 Claude Code。

新 Shell 中再次确认：

```bash
env | grep -iE "proxy"
env | grep -iE "anthropic|claude"
```

如果秘密进入聊天、日志、Shell 历史、公开订阅或 Git，仅删除文件不够，必须轮换。

## 完成标准

- 需要的代理仍在，残留项已消失；
- JSON 仍可解析；
- Claude Code 能正常启动和登录；
- 没有误删历史或项目；
- 有备份和回退方法。

时区完成标准为 `readlink /etc/localtime` 与 Node API 均显示 `Asia/Taipei`。
