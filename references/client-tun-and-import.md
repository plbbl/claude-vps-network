# 客户端、TUN 与导入

## 四种格式

- **分享链接**：一个 `hysteria2://...` 节点。
- **Clash/Mihomo YAML**：配置文件或 `proxies` 片段。
- **订阅 URL**：返回兼容配置内容的 HTTP(S) 地址。
- **Base64 内容**：某些订阅的编码，不是 URL。

Hysteria 官方 [URI 规范](https://v2.hysteria.network/docs/developers/URI-Scheme/) 定义了 `obfs`、`obfs-password`、`sni` 和 `insecure`。密码和节点名必须正确编码。

## Clash/Mihomo 节点

```yaml
proxies:
  - name: Private VPS
    type: hysteria2
    server: tunnel.example.com
    port: 443
    password: REPLACE_WITH_AUTH_SECRET
    sni: tunnel.example.com
    skip-cert-verify: false
    obfs: salamander
    obfs-password: REPLACE_WITH_OBFS_SECRET
```

只使用当前内核支持的字段，参考 [Mihomo Hysteria 2 文档](https://wiki.metacubex.one/en/config/proxies/hysteria2/)。

私人节点应使用独立本地配置或受保护的私人订阅，不要写进会被远程更新覆盖的商业订阅文件。

## Karing 导入

- 原始 `hysteria2://` 使用“单节点、分享链接或剪贴板导入”。
- “配置链接”输入框通常需要 URL。把 Base64 文本直接贴进去可能出现 `v2ray unsupported format: [://] was not found`。
- 原始节点没有订阅到期时间。“已失效”可能来自订阅元数据，应先确认来源。
- Salamander 兼容性通常比新混淆方式稳定。
- 不要复制文档中的脱敏示例，必须从真实服务端参数重新生成。

## TUN 与系统代理

- **系统代理**：macOS 发布 HTTP/HTTPS/SOCKS 代理，仅影响遵循这些设置的应用。
- **TUN**：虚拟网卡接管 IP 路由，可覆盖不支持系统代理的应用。

纯 TUN 配置：

1. 先准备客户端中的一键关闭方法；
2. 开启虚拟网卡/TUN；
3. 关闭客户端“系统代理”开关；
4. 按需求选择全局或规则模式；
5. 验证 DNS、IPv4 和 IPv6；
6. 测试睡眠、重启和断线恢复。

系统代理为空不等于代理不可识别，只代表 macOS 没有设置系统代理。

## macOS 验证

```bash
scutil --proxy
ifconfig | rg '^utun'
route -n get default
curl -fsS https://ipinfo.io/json
```

同时确认：

- 系统代理符合设计；
- 公网出口是预期 VPS；
- DNS 没有循环或断开；
- Claude Code 能访问正常服务端点。

回退：关闭 TUN → 关闭客户端 → 恢复旧配置 → 重连 Wi-Fi → 确认直连恢复。

## 常见问题

| 症状 | 优先检查 |
|---|---|
| 节点可导入但不连接 | UDP 443、防火墙、服务监听、旧 IP |
| Mac 可用、iPhone 不可用 | 客户端内核、URI 编码、当前网络 UDP 策略 |
| Karing 格式错误 | 导入入口错误、缺少 `hysteria2://`、重复编码 |
| 认证失败 | 认证密码错误；不要与混淆密码混淆 |
| 超时且服务端无日志 | IP、UDP 防火墙、运营商阻断 |
| TLS/SNI 错误 | 域名、证书、SNI、`insecure` 模式 |
| 绑定静态 IP 后失效 | 客户端仍使用旧公网 IP |
| TUN 后全机断网 | 路由或 DNS 循环；先回退再排查 |
| 更新订阅后节点消失 | 节点被写入远程管理配置，应改用独立配置 |
