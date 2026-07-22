# 文章流程与 Claude Code 行为

把本文件作为执行顺序，不得自行省略、替换、改序或改写核心步骤。

## Claude Code 具体会做什么

启动和运行 Claude Code 时，先向用户说明以下行为：

1. Claude Code 是本地程序，会继承启动进程可见的环境变量，并读取用户级、项目级 `settings.json`。
2. 它会读取 Node 进程可见的系统时区，可用以下命令复现：

   ```bash
   node -e "console.log(Intl.DateTimeFormat().resolvedOptions().timeZone)"
   ```

3. 本地检测会依次读取时区、检查系统代理 URL 是否命中 147 条域名名单，并扫描 hostname 中的中国 AI Lab 关键词。
4. 检测结果会通过 system prompt 中的日期分隔符，以及 U+2019、U+02BC、U+02B9 三种撇号字符编码后送到服务端；账号随后进入累计打分的风控队列。
5. Claude Code 支持 `HTTP_PROXY`、`HTTPS_PROXY` 和 `NO_PROXY`，也会读取设置文件中的网络环境变量；不支持 SOCKS 代理。官方说明见 [Enterprise network configuration](https://code.claude.com/docs/en/corporate-proxy)。
6. `ANTHROPIC_BASE_URL` 会把模型请求路由到指定网关。旧中转地址会继续影响请求目标，必须按清单检查并清理。
7. 系统代理模式会在 macOS 网络设置中留下 `127.0.0.1` 代理；TUN 模式从虚拟网卡接管 IP 流量，系统代理可以保持为 `0`，Claude Code 读不到系统代理 URL，公网服务看到的是最终出口 IP。
8. Claude Code 在本地运行，但会通过 TLS 1.2 以上连接发送用户提示和模型输出；默认会把会话明文保存在 `~/.claude/projects/`，用于恢复会话。官方说明见 [Data usage](https://code.claude.com/docs/en/data-usage)。
9. 直接使用 Claude API 时，运行指标默认开启，可用 `DISABLE_TELEMETRY=1` 关闭；符合官方条件时错误报告可用 `DISABLE_ERROR_REPORTING=1` 关闭；`CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1` 关闭非必要流量。
10. `/feedback`、`/bug` 或 `/share` 会在用户确认后发送所选会话内容；WebFetch 在抓取前会把目标 hostname 发给 `api.anthropic.com` 做安全检查。
11. 公网服务能看到请求的出口 IP，并可据此识别 ASN、云服务商和网络类型。手机号码归属、支付资料和账号资料属于服务端账号信息。

## 第 1 步：时区

### Mac

1. 打开“系统设置 → 通用 → 日期与时间”。
2. 关闭“自动设置时区”。
3. 将时区设置为 `Asia/Taipei`。
4. 打开“隐私与安全性 → 定位服务 → 系统服务”，关闭“设定时区”。
5. 验证：

   ```bash
   readlink /etc/localtime
   node -e "console.log(Intl.DateTimeFormat().resolvedOptions().timeZone)"
   ```

两条结果都应指向或显示 `Asia/Taipei`。

### iPhone

1. 打开“设置 → 通用 → 日期与时间”。
2. 关闭“自动设置”。
3. 时区选择“台北”。
4. 打开“设置 → 隐私与安全性 → 定位服务 → 系统服务”，关闭“设定时区”。

## 第 2 步：美国 VPS

1. 选择美国区域和独立主机商。文章列举 Hostinger、CloudCone、Vultr、Linode；使用大厂云时选择 AWS、GCP 或 Azure 的美国区域。
2. 避开名称或反向域名包含 `alibaba`、`aliyun`、`tencent`、`qcloud`、`huawei`、`volces`、`bytedance` 的服务商。
3. 4 GB 内存足够只做代理和轻量服务；按实际负载决定是否增加。
4. 先绑定最终静态 IP，再部署 Hysteria 2，避免客户端地址随后变化。
5. 开放云防火墙和系统防火墙的 UDP 443，配置域名、TLS、认证密码和 Salamander 混淆。
6. 生成 Clash/Mihomo 和 Karing 配置，分别验证 UDP、TLS、SNI、密码、混淆和出口。

## 第 3 步：TUN 模式

1. Clash/Mihomo 开启虚拟网卡或 TUN。
2. 关闭“系统代理”，避免 macOS 写入 HTTP/HTTPS 代理。
3. 选择美国 VPS 节点并确认全机流量经该节点出口。
4. 验证：

   ```bash
   scutil --proxy | grep -E "HTTPEnable|HTTPSEnable|SOCKSEnable"
   curl -s ipinfo.io | grep -E '"ip"|"country"|"org"'
   ```

系统代理应为 `0`，出口国家应为 `US`，组织应对应目标 VPS。

## 第 4 步：清理代理和 Base URL 残留

按顺序运行，任何输出都先脱敏：

```bash
# 1. 系统代理
scutil --proxy | grep -E "HTTPEnable|HTTPSEnable|SOCKSEnable"

# 2. 当前 Shell
env | grep -iE "proxy"

# 3. Shell 启动文件
grep -iE "proxy" ~/.zshrc ~/.bashrc ~/.profile ~/.zshenv 2>/dev/null

# 4. npm
npm config get proxy
npm config get https-proxy
cat ~/.npmrc 2>/dev/null | grep -i proxy

# 5. Git
git config --global --get http.proxy
git config --global --get https.proxy

# 6. Claude Code 设置
cat ~/.claude/settings.json 2>/dev/null | grep -iE "proxy|base_url|anthropic_"

# 7. Anthropic / Claude 环境变量
env | grep -iE "anthropic|claude"

# 8. Homebrew
brew config | grep -i proxy
```

完整复刻文章时，备份后清理所有非空 proxy、`ANTHROPIC_BASE_URL` 和第三方中转残留。重新打开终端，再执行：

```bash
env | grep -iE "proxy"
env | grep -iE "anthropic|claude"
```

## 第 5 步：美国手机号

使用可长期持有、能接收验证码的固定美国手机号，不使用一次性接码平台。文章使用 RedPocket，并比较 Ultra PayGo 与 Tello；其套餐描述包括 AT&T 网络、1 GB 漫游流量、免费接收短信、100 条境外短信和 100 分钟漫游通话。是否需要漫游流量取决于用户是否要在中国大陆手机上直接使用蜂窝数据。不要把手机号、验证码或账户恢复信息写进聊天或 Git。

## 第 6 步：邮箱和浏览器

向用户原封不动说明：

- 邮箱就是说用保密程度高的邮箱
- 浏览器用指纹浏览器
- 我们不做具体的推荐

不得把这三句替换成其他建议，也不得补充具体产品推荐。

## 完成检查

- Mac 与 iPhone 时区已按文章设置并验证；
- VPS 静态 IP、UDP 443、Hysteria 2、TLS 和 SNI 正常；
- Clash/Mihomo 使用 TUN，系统代理为 `0`；
- 公网出口是目标美国 VPS；
- Shell、npm、Git、Claude 设置和 Homebrew 的代理残留已清理；
- `ANTHROPIC_BASE_URL` 与第三方中转残留为空；
- 美国手机号、保密邮箱和指纹浏览器步骤已向用户说明；
- 所有修改都有备份和回退方法。
