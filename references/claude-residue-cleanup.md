# Claude 全量本地残留

覆盖 Claude Code CLI、Claude Desktop 和浏览器中的 Claude 站点数据。先盘点，再按范围备份和清理。

## 目录

- 1. 只读盘点
- 2. 必须区分的范围
- 3. 清理前固定动作
- 4. Claude Code CLI
- 5. Claude Desktop
- 6. 浏览器和指纹浏览器
- 7. 验证
- 8. 本地清理不会删除的内容

## 1. 只读盘点

运行：

```bash
python3 scripts/audit_claude_network.py
python3 scripts/audit_claude_residue.py
```

第二个脚本只输出路径、类别、删除影响和可读取的 Claude 域名 Cookie 数量，不输出 Cookie 值、会话正文、密码或令牌。

## 2. 必须区分的范围

| 范围 | 主要位置 | 删除影响 |
|---|---|---|
| 网络残留 | 系统代理、Shell、npm、Git、Homebrew、`settings.json` | 可能改变联网方式 |
| CLI 可重建缓存 | `paste-cache`、`image-cache`、`debug`、`plans`、`tasks`、`session-env`、`shell-snapshots` | 下次运行重建 |
| CLI 会话和记忆 | `projects`、`history.jsonl`、`file-history`、`stats-cache.json` | 丢失恢复、历史、记忆或统计 |
| CLI 配置和插件 | `settings*.json`、`~/.claude.json`、`plugins` | 丢失设置、项目状态或插件 |
| CLI 登录 | macOS Keychain；Linux/Windows 的 `.credentials.json` | 退出登录 |
| Desktop 数据 | Application Support、Cookies、HTTPStorages、WebKit、Preferences、Containers | 退出登录并重置 Desktop |
| 浏览器 Claude 站点数据 | Cookie、Local Storage、IndexedDB、Cache Storage、Service Worker、Session Storage、权限 | 退出 Claude 网页登录并清空站点状态 |
| 浏览器全局缓存 | 浏览器整个 Cache/Code Cache | 影响所有网站，不默认执行 |

官方列出的 Claude Code 应用数据和影响见 [Explore the .claude directory](https://code.claude.com/docs/en/claude-directory)。

## 3. 清理前固定动作

1. 记录 `claude --version` 和两份审计结果。
2. 正常退出全部 Claude Code 会话。
3. 退出 Claude Desktop，不只关闭窗口。
4. 退出所有要清理的浏览器和指纹浏览器。
5. 确认没有相关进程：

   ```bash
   pgrep -ifl 'Claude|Google Chrome|Microsoft Edge|Brave|Arc|Firefox|Safari'
   ```

6. 建立权限为 `700` 的时间戳备份目录；备份文件权限设为 `600`。
7. 列出本轮选择的范围：缓存、会话、配置、登录、Desktop、浏览器站点数据。

不要运行 `rm -rf ~/.claude`，不要删除整个浏览器配置文件，也不要在浏览器运行时编辑 Cookies SQLite 或 LevelDB。

## 4. Claude Code CLI

### 缓存清理

把审计确认存在的以下目录逐个移动到备份目录，不使用通配符：

```text
~/.claude/paste-cache
~/.claude/image-cache
~/.claude/debug
~/.claude/plans
~/.claude/tasks
~/.claude/todos
~/.claude/session-env
~/.claude/shell-snapshots
```

### 会话、历史和记忆

先预览 Claude 官方清理计划：

```bash
claude project purge --all --dry-run
```

用户确认后交互清理：

```bash
claude project purge --all -i
```

需要完全清空全部项目记录且用户明确同意后才使用：

```bash
claude project purge --all --yes
```

该操作会删除项目 transcript、auto memory、任务、调试记录、文件历史、匹配的 prompt history 和 `~/.claude.json` 中的项目状态。它不会自动删除 `shell-snapshots` 和 `backups`。

### 配置、插件和登录

- 只有用户明确要求“完整重置 CLI”时，才备份并移走 `~/.claude/settings.json`、`settings.local.json`、`~/.claude.json` 和 `~/.claude/plugins/`。
- macOS 凭据在钥匙串中，优先使用 `claude logout`；不要猜测并批量删除钥匙串项目。
- Linux/Windows 的 `.credentials.json` 先备份，再由 `claude logout` 管理。
- 删除本地内容不会删除 Anthropic 服务端记录。

## 5. Claude Desktop

macOS bundle 标识为 `com.anthropic.claudefordesktop`。按审计脚本实际命中的路径操作，不假设所有路径都存在。

### 仅清缓存

退出 Desktop 后，备份并移走审计命中的：

```text
~/Library/Caches/com.anthropic.claudefordesktop
~/Library/Caches/com.anthropic.claudefordesktop.ShipIt
~/Library/Logs/Claude
~/Library/Saved Application State/com.anthropic.claudefordesktop.savedState
```

### 完整重置 Desktop

只有用户明确同意退出登录并重置 Desktop 后，才额外备份并移走审计命中的：

```text
~/Library/Application Support/Claude
~/Library/Application Support/com.anthropic.claudefordesktop
~/Library/Preferences/com.anthropic.claudefordesktop.plist
~/Library/Cookies/com.anthropic.claudefordesktop.binarycookies
~/Library/HTTPStorages/com.anthropic.claudefordesktop
~/Library/WebKit/com.anthropic.claudefordesktop
~/Library/Containers/com.anthropic.claudefordesktop
~/Library/Group Containers/com.anthropic.claudefordesktop
```

重新打开 Desktop，确认出现首次启动或登录界面，再决定是否删除备份。

## 6. 浏览器和指纹浏览器

对每个浏览器、每个配置文件分别清理以下域名及其子域名：

```text
claude.ai
claude.com
anthropic.com
claudeusercontent.com
```

清除范围必须包括：

- Cookie；
- Local Storage；
- IndexedDB；
- Cache Storage 和普通站点缓存；
- Service Worker；
- Session Storage；
- 站点权限和通知权限。

操作方式：

1. 使用浏览器自己的“网站数据”“站点数据”或“清除存储”界面。
2. 对上述四个域名逐个搜索并删除。
3. 指纹浏览器按其中每个独立配置文件执行同样操作。
4. 不推荐具体浏览器或指纹浏览器产品。
5. 只有用户明确要求影响所有网站时，才清空整个浏览器 Cache、Code Cache 或整个配置文件。

不要直接删除 Chromium/Firefox 的整个 Cookies 数据库，因为它包含其他网站的数据。Safari 也使用其“管理网站数据”界面按域名清理。

## 7. 验证

1. 再次运行：

   ```bash
   python3 scripts/audit_claude_network.py
   python3 scripts/audit_claude_residue.py
   ```

2. 系统代理和代理环境变量符合文章要求。
3. CLI 缓存路径已消失或重新生成且为空。
4. 若执行会话清理，`claude project purge --all --dry-run` 不再列出目标数据。
5. 若执行登录清理，CLI、Desktop 和网页都要求重新登录。
6. 浏览器网站数据中不再出现四个 Claude/Anthropic 域名。
7. 汇报每个范围的“已清理、保留、跳过、需重新登录”状态和备份路径。

在用户验证新状态前保留备份。恢复时退出相关程序，把对应路径从备份移回原位置。

## 8. 本地清理不会删除的内容

- Claude API 的 prompt cache 位于模型提供商服务器，不是 Mac 本地文件；本地清理不能直接删除，只能等待提供商过期。
- 网页或 Desktop 中已经同步到账号的远端对话，不会因清除 Cookie 或本地缓存而从服务端删除。
- Anthropic 服务端的账号、风控、登录和请求记录不会因本地重置消失。

如果用户还要求删除远端对话或账号数据，必须单独使用对应产品中的删除功能，不能把本地清理结果当成服务端删除证明。
