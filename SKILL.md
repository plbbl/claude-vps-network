---
name: claude-vps-network
description: 审计并清理 Claude Code 的代理、环境变量和 Base URL 残留；检查时区暴露、邮件远程内容与浏览器隐私；在 AWS Lightsail 或 Ubuntu VPS 部署、修复 Hysteria 2；生成 Clash/Mihomo 与 Karing 配置；配置 TUN、验证出口并准备回退。适用于“清理 CC 网络配置”“检查邮件追踪”“搭建私人 VPS 节点”“导入 hysteria2 链接”“排查静态 IP、UDP 443、TLS、Karing 失效或 TUN 断网”等请求。
---

# Claude VPS 网络

建立可验证、可回退的私人网络。把技术事实与“防封”“不可检测”等未经证实的说法分开。

## 边界

- 仅管理用户拥有或获授权的设备、账号和服务器。
- 不承诺某种 IP、时区、手机号、TLS 或缓存清理能避免审核或封禁。
- 不伪造所在地、身份、支付资料、设备信息或时区。
- 代理是正常网络配置。只删除已确认过期或冲突的设置。
- 不直接删除整个 `~/.claude`、钥匙串、项目历史或凭据。
- 不在聊天、日志或 Git 中输出私钥、密码、完整节点链接和访问令牌。

## 流程

### 1. 收集事实

确认：

- 操作系统、Claude Code 版本；
- Clash/Mihomo、Karing 或其他客户端及内核版本；
- 路由范围：仅 Claude Code、指定应用或全机 TUN；
- VPS 提供商、区域、系统、当前 IP、静态 IP、域名、SSH 用户；
- 是否有真实域名和有效证书；
- 用户真实时区；
- 本次只审计，还是允许修改。

不要索要秘密内容。优先使用脱敏截图、文件路径和密钥指纹。

### 2. 只读审计

先读 [Claude Code 清理](references/claude-code-hygiene.md)，再运行：

```bash
python3 scripts/audit_claude_network.py
```

只有在用户同意查询公网出口后才加 `--online`。把结果分为：正常、过期、冲突、已泄露需轮换。

不要把代理残留统称为缓存。区分网络配置、Claude 设置、登录状态、历史记录和临时缓存。

### 3. 可回退清理

1. 列出要修改的具体文件和键。
2. 保留原权限，为每个文件建立时间戳备份。
3. 脱敏展示修改差异。
4. 只删除用户确认的残留项。
5. 新开终端，再运行一次审计。

仅在用户明确要求重置登录时运行 `claude logout`。本地清理不会删除服务端记录。

### 4. 配置 VPS

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

### 5. 邮件与浏览器隐私

需要检查 Anthropic 邮件或浏览器隔离时，读取 [邮件与浏览器隐私](references/email-and-browser-privacy.md)。

- 不把“每封邮件都有追踪器”写成事实；检查具体 `.eml` 源码。
- 优先使用邮件客户端的远程内容保护，并从书签或手动输入访问官方域名。
- 使用更新及时的标准浏览器和独立工作配置文件。
- 不使用“指纹浏览器”伪造 User-Agent、Canvas、WebGL、时区或设备身份。

### 6. 生成客户端配置

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

### 7. 配置 TUN

需要全机路由或应用不支持系统代理时才使用 TUN。若采用纯 TUN，关闭客户端的“系统代理”开关，避免重复代理。

分别验证：系统代理、TUN 网卡、路由、DNS、公网出口、Claude Code 连接、重启后恢复和回退。

`scutil --proxy` 为空只表示 macOS 没配置系统代理，不代表代理不可识别。

### 8. 分层排错

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

### 9. 汇报

明确说明：发现的事实、修改的文件和服务、测试结果、备份位置、节点文件位置、回退方法、失败层面和仍未证实的文章说法。所有秘密必须脱敏。

## 参考

- [Claude Code 清理](references/claude-code-hygiene.md)
- [VPS 与 Hysteria 2](references/vps-hysteria2.md)
- [客户端、TUN 与导入](references/client-tun-and-import.md)
- [邮件与浏览器隐私](references/email-and-browser-privacy.md)
- [证据与安全边界](references/evidence-and-safety.md)
