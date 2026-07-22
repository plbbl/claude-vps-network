# VPS 与 Hysteria 2

## 架构

```text
Mac/iPhone → Hysteria 2 加密 UDP → Ubuntu VPS → 目标网站
```

基本要求：

- 用户拥有或获授权管理服务器；
- Ubuntu 22.04 LTS 或更新版本；
- SSH 密钥登录；
- 最终静态 IPv4，或已指向它的域名；
- 云防火墙和系统防火墙均允许 UDP 443；
- 保留断网后的恢复入口。

## AWS Lightsail 顺序

1. 创建实例。
2. 先绑定 Static IP，再生成客户端节点。
3. Networking 中开放：
   - TCP 22：尽量限制管理来源；
   - UDP 443：供 Hysteria 2 使用。
4. 单独检查 UFW；Lightsail 规则不会自动修改系统防火墙。
5. 记录实例名、区域、静态 IP、系统和 SSH 密钥指纹，不记录私钥内容。

绑定静态 IP 本身不会破坏协议。绑定后不能连接，通常是客户端仍使用旧 IP、DNS 未更新、UDP 443 未开放或参数不一致。

## 安装前盘点

```bash
uname -a
lsb_release -a 2>/dev/null || cat /etc/os-release
df -h
sudo ss -lntup
sudo systemctl status hysteria-server.service --no-pager
sudo ufw status verbose
```

若已有 `/etc/hysteria/config.yaml`，先建立权限为 `600` 的时间戳备份，不覆盖未知的工作配置。

## 安装

使用 [Hysteria 官方脚本](https://v2.hysteria.network/docs/getting-started/Server-Installation-Script/)：

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl openssl
bash <(curl -fsSL https://get.hy2.sh/)
```

高安全要求下，先下载并检查脚本。安装器会建立 systemd 服务，但仍需配置 `/etc/hysteria/config.yaml`。

分别生成认证密码和 Salamander 混淆密码。不要把密码写进聊天或 Shell 历史。

推荐使用域名和 ACME：

```yaml
listen: :443

acme:
  domains:
    - tunnel.example.com
  email: operator@example.com

auth:
  type: password
  password: REPLACE_WITH_AUTH_SECRET

obfs:
  type: salamander
  salamander:
    password: REPLACE_WITH_OBFS_SECRET

masquerade:
  type: proxy
  proxy:
    url: https://news.ycombinator.com/
    rewriteHost: true
```

Salamander 不是必需项。启用后，服务端和客户端必须完全一致。字段说明见 [Hysteria 官方配置](https://v2.hysteria.network/docs/advanced/Full-Server-Config/)。

若 UFW 已启用：

```bash
sudo ufw allow 443/udp
```

不要在没有 SSH 放行规则和恢复控制台时盲目启用或重写 UFW。

启动并检查：

```bash
sudo systemctl enable --now hysteria-server.service
sudo systemctl restart hysteria-server.service
sudo systemctl status hysteria-server.service --no-pager
sudo journalctl --no-pager -e -u hysteria-server.service
sudo ss -lunp | rg ':443\b'
```

## TLS 选择

### 域名与 ACME：推荐

- A 记录指向最终静态 IP；
- 等待公共 DNS 生效；
- 客户端 `sni` 使用证书域名；
- `insecure=0`。

### 自签名：兼容备用

无域名时才考虑。客户端支持时优先使用证书指纹固定；使用 `insecure=1` 会关闭正常证书校验，必须明确告知风险。

不要使用无关网站的域名伪装证书身份。伪装页面地址不等于证书域名。

## 验证

```bash
sudo systemctl is-active hysteria-server.service
sudo ss -lunp | rg ':443\b'
sudo journalctl --since '-10 min' -u hysteria-server.service --no-pager
curl -fsS https://api.ipify.org
```

连接一个客户端并同时观察日志。`nc -u` 不能证明 UDP 服务正常，成功完成 Hysteria 认证才是有效的端到端测试。

## 排错

依次检查：

1. 节点是否使用最终静态 IP；
2. Lightsail 是否开放 **UDP** 443；
3. UFW/nftables 是否允许 UDP 443；
4. systemd 服务是否运行并监听 UDP 443；
5. 认证和混淆密码是否一致；
6. SNI 与证书模式是否匹配；
7. 客户端是否仍使用旧 IP 或端口；
8. 当前网络是否允许 UDP/QUIC；
9. ACME 所需的 DNS、时间和验证端口是否正常。

回退时恢复备份配置、重启服务，并选择上一个已验证的客户端节点。
