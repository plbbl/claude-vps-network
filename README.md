# Claude Code VPS 网络配置 Skill

一个面向 Codex 的中文 Skill，用于审计 Claude Code 网络配置、清理失效代理残留、部署私人 Hysteria 2 节点，并生成 Clash/Mihomo 与 Karing 客户端配置。

## 能做什么

- 审计 macOS 系统代理、环境变量、npm、Git、Homebrew 和 Claude Code 设置；
- 区分代理配置、登录状态、历史记录与缓存，避免误删 `~/.claude`；
- 在 AWS Lightsail 或 Ubuntu VPS 部署、修复 Hysteria 2；
- 生成 `hysteria2://` 分享链接和 Clash/Mihomo YAML；
- 配置并验证 TUN、DNS、公网出口和断网回退；
- 排查静态 IP、UDP 443、TLS、SNI、Karing 导入失效等问题；
- 检查邮件远程内容与浏览器隐私设置。

## 安装

```bash
git clone https://github.com/plbbl/configure-claude-code-vps-network.git \
  ~/.codex/skills/configure-claude-code-vps-network
```

重启 Codex，使其重新加载 Skill。

## 使用

直接对 Codex 说：

```text
使用 $configure-claude-code-vps-network 审计我的 Claude Code 网络配置。
```

也可以提出具体任务：

```text
帮我检查 Mac 上是否残留代理或 ANTHROPIC_BASE_URL。
帮我在自己的 Ubuntu VPS 上配置 Hysteria 2，并生成 Clash 和 Karing 配置。
帮我排查 Hysteria 2 的 UDP 443、TLS 或 SNI 问题。
```

## 本地审计

默认只读取本机配置，不查询公网出口：

```bash
python3 scripts/audit_claude_network.py
```

在用户同意查询公网出口后：

```bash
python3 scripts/audit_claude_network.py --online
```

## 生成客户端配置

```bash
python3 scripts/render_hysteria2_client.py \
  --server example.com \
  --port 443 \
  --sni example.com \
  --name "Private VPS" \
  --output /path/to/private-client.txt
```

脚本会隐藏密码输入，并将输出文件权限设为 `600`，即仅当前用户可读写。

## 安全边界

- 仅操作用户拥有或获得授权的设备、账号和服务器；
- 不承诺通过 IP、时区、TLS 或缓存清理规避平台审核；
- 不伪造所在地、身份、支付资料或设备信息；
- 不在聊天、日志或 Git 中输出私钥、密码、令牌和完整节点链接；
- 修改前备份，切换 TUN 前准备恢复入口和回退方法。

Codex 的完整执行规则见 [`SKILL.md`](SKILL.md)。
