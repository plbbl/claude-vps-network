---
name: claude-vps-network
description: 严格按用户文章执行 Claude 完整网络流程，并审计或清理 Claude Code CLI、Claude Desktop、浏览器和指纹浏览器中的网络残留、缓存、Cookie、站点存储、会话、记忆、配置与登录状态；同时配置美国 VPS、Hysteria 2、Clash/Mihomo/Karing 和 TUN。适用于“复刻文章配置”“清理 CC 全部残留”“重置 Claude Desktop”“清除浏览器 Claude 缓存”“搭建私人 VPS”“解释 CC 会读取和发送什么”及相关排错请求。
---

# Claude VPS 网络

严格执行用户提供文章和补充要求，不擅自省略、替换、改序或改写核心步骤。

## 忠实执行

1. 完整读取 [文章流程与 Claude Code 行为](references/article-workflow.md)。
2. 先向用户说明 Claude Code 具体会读取什么、发送什么、保存什么，再开始配置。
3. 按文章顺序处理：时区 → 美国 VPS → TUN → 清代理残留 → 清 CLI/Desktop/浏览器残留 → 美国手机号 → 邮箱 → 浏览器。
4. 用户没有要求跳过时，不得自行删除文章步骤或换成另一套建议。
5. 邮箱和浏览器必须使用本 Skill 中的原文，不推荐具体产品。
6. 所有修改仍需备份、验证和提供回退方法。

## 边界

- 仅管理用户拥有或获授权的设备、账号和服务器。
- 不承诺任何方案必然避免审核或封禁。
- 仅执行文章与用户明确要求的范围，不额外扩展。
- 复刻文章时，备份后清理其清单中所有非空代理与 Base URL 残留。
- 全量检查所有残留；删除前按缓存、会话、配置、登录、Desktop 和浏览器站点数据分组说明影响并取得确认。
- 不直接删除整个 `~/.claude`、整个浏览器配置文件或批量钥匙串项目。
- 不在聊天、日志或 Git 中输出私钥、密码、完整节点链接和访问令牌。

## 流程

### 1. 说明 Claude Code 行为

先按 [文章流程与 Claude Code 行为](references/article-workflow.md) 向用户说明：本地读取项、网络请求、代理与 Base URL、TUN 后的路由、遥测、错误报告、会话保存，以及时区和代理检测机制。不要跳过这一段。

### 2. 收集事实

确认：

- 操作系统、Claude Code 版本；
- Clash/Mihomo、Karing 或其他客户端及内核版本；
- 路由范围：仅 Claude Code、指定应用或全机 TUN；
- VPS 提供商、区域、系统、当前 IP、静态 IP、域名、SSH 用户；
- 是否有真实域名和有效证书；
- 当前时区；
- 本次只审计，还是允许修改。

不要索要秘密内容。优先使用脱敏截图、文件路径和密钥指纹。

### 3. 只读审计

先读 [Claude Code 清理](references/claude-code-hygiene.md)和 [Claude 全量本地残留](references/claude-residue-cleanup.md)，再运行：

```bash
python3 scripts/audit_claude_network.py
python3 scripts/audit_claude_residue.py
```

只有在用户同意查询公网出口后才加 `--online`。把结果分为：正常、过期、冲突、已泄露需轮换。

第二个脚本只读盘点 Claude Code CLI、Claude Desktop 和浏览器数据路径。不要把所有残留统称为缓存；区分网络、可重建缓存、会话与记忆、配置与插件、登录凭据、Desktop 数据和浏览器站点数据。

### 4. 全量本地残留

完整读取 [Claude 全量本地残留](references/claude-residue-cleanup.md)，逐项覆盖：

1. Claude Code CLI 的缓存、会话、history、auto memory、file history、统计、设置、插件和登录；
2. Claude Desktop 的 Cache、Application Support、Cookies、HTTPStorages、WebKit、Preferences、Containers、日志和保存状态；
3. 每个浏览器和指纹浏览器配置文件中 `claude.ai`、`claude.com`、`anthropic.com`、`claudeusercontent.com` 的 Cookie、Local Storage、IndexedDB、Cache Storage、Service Worker、Session Storage 和权限；
4. 先只读审计，再按用户选择执行“仅缓存”“会话与历史”“完整 CLI 重置”“完整 Desktop 重置”“浏览器 Claude 站点数据”；
5. 退出相关进程、建立权限受限备份、逐个处理明确路径、重新审计并验证登录状态。

用户要求“全部清理”时，也必须先展示删除影响；确认后可以执行完整范围，但不得用一个宽泛递归删除命令代替分项流程。

### 5. 可回退网络清理

1. 列出要修改的具体文件和键。
2. 保留原权限，为每个文件建立时间戳备份。
3. 脱敏展示修改差异。
4. 按文章清单清理所有非空 proxy、Base URL 和 Anthropic/Claude 中转残留；用户明确要求保留的项除外。
5. 新开终端，再运行一次审计。

仅在用户明确要求重置登录时运行 `claude logout`。本地清理不会删除服务端记录。

### 6. 配置 VPS

修改服务器前完整读取 [VPS 与 Hysteria 2](references/vps-hysteria2.md)。顺序固定：

1. 盘点服务器并备份现有配置；
2. 先绑定最终静态 IP；
3. 确认 SSH 恢复入口；
4. 在云防火墙和系统防火墙开放 UDP 443；
5. 使用 Hysteria 官方安装方式；
6. 优先使用域名和 ACME 证书；
7. 验证服务、端口、日志和出口；
8. 密码只存入权限受限的本地文件。

若切换 TUN 会中断当前 Codex 会话，先告诉用户一键回退方法，再切换。

### 7. 邮箱与浏览器

完整读取 [邮箱与浏览器](references/email-and-browser-privacy.md)，向用户原封不动说明：

- 邮箱就是说用保密程度高的邮箱
- 浏览器用指纹浏览器
- 我们不做具体的推荐

这三句保持原文，不增加具体产品推荐。

### 8. 生成客户端配置

先读 [客户端、TUN 与导入](references/client-tun-and-import.md)，再运行：

```bash
python3 scripts/render_hysteria2_client.py \
  --server example.com --port 443 --sni example.com \
  --name 'Private VPS' --output /path/to/private-client.txt
```

脚本会隐藏密码输入，并生成权限为 `600` 的节点文件。仅在明确使用自签名证书时加 `--insecure`。

- `hysteria2://` 是单节点分享链接；
- Clash/Mihomo YAML 是配置文件或片段；
- 订阅必须是返回配置内容的 HTTP(S) URL；
- 不要公开带密码的订阅或节点链接。

### 9. 配置 TUN

需要全机路由或应用不支持系统代理时才使用 TUN。若采用纯 TUN，关闭客户端的“系统代理”开关，避免重复代理。

分别验证：系统代理、TUN 网卡、路由、DNS、公网出口、Claude Code 连接、重启后恢复和回退。

`scutil --proxy` 为空只表示 macOS 没配置系统代理，不代表代理不可识别。

### 10. 分层排错

按顺序检查，第一处失败就停止继续改动：

1. 静态 IP 或 DNS；
2. 云防火墙 UDP 443；
3. 系统防火墙与 UDP 监听；
4. Hysteria systemd 服务和日志；
5. 密码、混淆、SNI、证书和端口；
6. 导入格式是否正确；
7. 客户端内核是否支持配置字段；
8. 当前网络是否允许 UDP/QUIC；
9. TUN 路由和 DNS。

排错时不要同时修改多个层面。

### 11. 汇报

明确说明：文章步骤完成情况、Claude Code 行为说明、CLI/Desktop/各浏览器配置文件的残留状态、每类清理影响、修改的文件和服务、测试结果、备份位置、需重新登录的表面、节点文件位置、回退方法和失败层面。所有秘密必须脱敏。

## 参考

- [文章流程与 Claude Code 行为](references/article-workflow.md)
- [Claude Code 清理](references/claude-code-hygiene.md)
- [Claude 全量本地残留](references/claude-residue-cleanup.md)
- [VPS 与 Hysteria 2](references/vps-hysteria2.md)
- [客户端、TUN 与导入](references/client-tun-and-import.md)
- [邮箱与浏览器](references/email-and-browser-privacy.md)
