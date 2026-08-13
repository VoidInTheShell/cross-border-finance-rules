# Cross-Border Finance Rules

面向 Mihomo/Clash.Meta 的跨境金融规则集，覆盖全球银行与支付金融科技、券商与传统/虚拟资产交易所，以及各国电信运营商和 ISP。

## 发布产物

| 文件 | 类型 | 来源/用途 |
|---|---|---|
| `rules/category-finance.mrs` | Mihomo MRS / domain | 每日从 MetaCubeX `category-finance.mrs` 自动同步 |
| `rules/category-cryptocurrency.mrs` | Mihomo MRS / domain | 每日从 MetaCubeX `category-cryptocurrency.mrs` 自动同步 |
| `rules/cross-border-finance-fallback.yaml` | Mihomo YAML / domain | 人工审计的缺口补充与硬编码保底，当前 476 个域名后缀 |
| `sources.lock.json` | JSON | 上游 URL、产物大小、SHA-256 与最后变更时间 |
| `sources/card-lengziyu-exchanges.json` | JSON | `card.lengziyu.cn` 卡片列表、筛选策略、卡片 ID 与官方根域核验清单 |

上游同步失败时，仓库中已经提交的上一版 MRS 不会被删除；fallback 仍独立可用。fallback 同时冗余保留渣打、American Express、N26、iFAST、PayPal、Bybit、OKX、Binance、O2、T-Mobile 等关键入口，以降低上游分类缺项或地区探测域变化带来的漏匹配风险。

## card.lengziyu.cn 补充

`sources/card-lengziyu-exchanges.json` 记录了 2026-08-11 从公开市场列表读取的 287 个卡片 ID（详情接口当次有 60 个成功响应、227 个未发布/错误响应）。其中明确带“交易所”标签的详情包括 Bitget、Bybit、Coinbase、Crypto.com 与 OKX；其它条目只有在卡片 ID 与官方站点可以交叉核验时才纳入，并区分 `exchange` 与 `card-platform`。卡片站自身占位地址、第三方评测站、广告地址和普通银行/银行卡条目被排除。

本次保底补充了 BingX、Pionex、CoinW、Zoomex、WhiteBIT、BitMart、CEX.IO、CoinZoom、Bitpanda、Bit2Me、SwissBorg、Nexo、CoinJar、Paybis、Busha、Fasset、Wirex 等交易/买卖或卡片平台，以及 ether.fi、RedotPay、KAST、Infini、MetaMask 生态、Gnosis Pay、Oobit、Coin98、Plasma One、钱包/链上支付等直接关联入口。Plasma One 按卡片/稳定币账户平台归类，`plasma.org` 与 `plasma.to`（覆盖 `app.plasma.to`）进入 fallback；卡片站占位地址和无关的 `plasma.io` 不加入。它们仍通过 `FinanceFallback` 统一进入“跨境金融”，不会把大域名表重新硬编码到九份模板。

域名筛选是路由用途，不是服务安全或可用性推荐；地区、KYC、卡片发行与产品条款仍以各官方站点当前状态为准。

## Mihomo provider 示例

```yaml
rule-providers:
  FinanceGlobal:
    type: http
    behavior: domain
    format: mrs
    path: ./RuleSet/FinanceGlobal.mrs
    url: "https://gh-proxy.org/https://raw.githubusercontent.com/VoidInTheShell/cross-border-finance-rules/main/rules/category-finance.mrs"
    interval: 86400
  CryptoGlobal:
    type: http
    behavior: domain
    format: mrs
    path: ./RuleSet/CryptoGlobal.mrs
    url: "https://gh-proxy.org/https://raw.githubusercontent.com/VoidInTheShell/cross-border-finance-rules/main/rules/category-cryptocurrency.mrs"
    interval: 86400
  FinanceFallback:
    type: http
    behavior: domain
    format: yaml
    path: ./RuleSet/FinanceFallback.yaml
    url: "https://gh-proxy.org/https://raw.githubusercontent.com/VoidInTheShell/cross-border-finance-rules/main/rules/cross-border-finance-fallback.yaml"
    interval: 86400

rules:
  - RULE-SET,FinanceFallback,跨境金融
  - RULE-SET,FinanceGlobal,跨境金融
  - RULE-SET,CryptoGlobal,跨境金融
```

建议把三条规则置于通用 GFW、GeoSite、国内直连与 MATCH 之前。这样 DNS 原始域名及 sniffer 识别出的 HTTP Host、TLS SNI、QUIC 域名会落到同一个策略组。Bybit 的 `bybit.eu`、`bybit.nl`、`bybit.com` 与常用备用母域均在 fallback 中，避免欧洲入口探测全球域名后改走其他出口。

## 自动同步

`.github/workflows/sync-upstreams.yml` 每日及手动运行：

1. 读取 `upstreams.json` 中的固定上游；
2. 下载 MRS，拒绝过小文件和 HTML/JSON 错误页；
3. 校验 fallback 的格式、重复项和关键域名；
4. 记录 SHA-256、大小和最后变化时间；
5. 仅在产物变化时自动提交。

同步脚本只允许 HTTPS 和 `raw.githubusercontent.com`，不执行上游内容。

## 范围说明

- 金融骨架沿用 v2fly/MetaCubeX 分类，不主动并入 `category-bank-cn`，避免把国内银行流量整体改为跨境出口。
- 虚拟资产分类是广义生态，包含交易所、钱包、链、DeFi 与行情服务；卡片站补充同样只用于将相关入口统一交给手动“跨境金融”组。
- 全球运营商缺少成熟统一上游，因此主要由人工维护 fallback 覆盖。
- 域名与地区入口会变化；欢迎通过 issue/PR 提交可验证的官方根域。

## 上游

- [MetaCubeX/meta-rules-dat](https://github.com/MetaCubeX/meta-rules-dat)
- [v2fly/domain-list-community](https://github.com/v2fly/domain-list-community)

## License

MIT

