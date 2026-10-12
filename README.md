# helin-zhibodianshang

河林发布的直播电商拆解 Agent Skill。给它一份直播回放语音转写稿，再说“拆解直播”，即可以“憋单—卡单—踢单—促单”循环为主框架，生成基于文稿证据的五模块直播拆解报告，适配视频号、抖音、小红书。

当前版本：`v2.0.0`（更新记录见 [`CHANGELOG.md`](CHANGELOG.md)）。已发布于 `https://github.com/helin021798/helin-zhibodianshang`，结构校验、12 项脚本测试和一份 2.5 小时真实视频号文稿的前向测试均已通过。

> 本仓库是**公开版**，收录精简版河林方法论。四段节奏参照、节奏判断解读与完整案例拆解属于河林付费完整版内容。

> **给 Agent 的安装入口：[`INSTALL.md`](INSTALL.md)**  
> **Skill 完整目录：`skills/helin-analyze-livestream-commerce/`**  
> **Skill 详细说明：[`SKILL_DETAILS.md`](SKILL_DETAILS.md)**

## 给读者的一句话

仓库发布后，推荐把下面这句话直接发给自己的 Agent：

```text
帮我安装 GitHub 仓库 https://github.com/helin021798/helin-zhibodianshang 中的 helin-analyze-livestream-commerce Skill。请先读取仓库根目录 INSTALL.md，安装完整 Skill 目录，不要只下载 SKILL.md；安装完成后按 INSTALL.md 的清单验证，并告诉我是否需要重启或开启新对话。
```

简短版也可以这样说：

```text
帮我安装 GitHub 上 helin021798/helin-zhibodianshang 仓库里的 helin-analyze-livestream-commerce Skill。
```

## 它能做什么

- 用台账脚本把长文稿切段、计量，自动校准语速，统计每个商品的出场、返场和累计时长；
- 识别全场商品、价格机制、核心卖点，用 A–F 六项信号综合判定货盘角色；
- 还原包含开场、抽奖、下场预告等非商品段的完整排品动线；
- 逐轮拆解主推品的憋单、卡单、踢单、促单循环，并对照平台节奏做判断；
- 整理主播复述或回答过的用户问题，找出没被接住的高意向提问；
- 从转写稿中整理最多两个主推品的话术，标注极限词、虚构稀缺、功效宣称等合规风险；
- 抽象带合规提示的可复用话术框架，输出有文稿依据的亮点和优化建议；
- 用户提供直播数据时，可以把动作和数据变化对齐做对照。

它不分析投流、付费流量、ROI或广告策略，也不会从直播话术反推真实销量、在线人数和GMV。

## 最简使用方法

提供：

- 必需：直播回放语音转写稿；
- 建议：平台（视频号/抖音/小红书）、品类或行业；
- 可选：账号名称、实际直播时长、已知主推品、直播数据截图或导出表。

然后说：

```text
请使用 $helin-analyze-livestream-commerce。
附件是某美妆直播间的视频号回放转写稿，直播时长约90分钟。
拆解直播。
```

## 固定报告结构

1. 直播货盘总览；
2. 排品策略与节奏拆解；
3. 主推品话术整理；
4. 可复用话术框架；
5. 综合点评。

## 关键分析边界

- 有原始时间戳时按实测语速计时；没有时间戳但给了实际时长时按“总字数÷时长”校准；两者都没有才按每分钟250字估算，并标注“估算”。
- 小红书直播节奏偏慢，缺少憋卡踢循环不算缺陷，改拆“信任转化链”。
- 合规标注是风险提醒，不是法律意见。
- “拉停留、促转化、拉GMV”是策略作用推断，不代表已经取得相应效果。
- 产品名、规格、价格、库存、功效和售后不能根据常识擅自纠正。
- 文稿信息不足时必须写“文稿中未体现”，不能补齐标准答案。
- 模块三是基于原文的去重整理，不是重新编写一套新话术。

## 仓库结构

```text
helin-zhibodianshang/
├── README.md
├── INSTALL.md
├── SKILL_DETAILS.md
├── LICENSE
├── skills/
│   └── helin-analyze-livestream-commerce/
│       ├── SKILL.md
│       ├── agents/openai.yaml
│       ├── references/
│       │   ├── helin-method.md
│       │   ├── analysis-rules.md
│       │   ├── report-template.md
│       │   └── example-report.md
│       └── scripts/transcript_ledger.py
├── CHANGELOG.md
├── evals/
└── tests/
```

## 本地开发与验证

验证 Skill 结构：

```powershell
skills-ref validate .\skills\helin-analyze-livestream-commerce
```

运行脚本测试：

```powershell
python -m unittest discover -s tests -p "test_*.py"
```

对UTF-8文稿生成分段目录、信号线索和出场台账（macOS/Linux 用 `python3`）：

```powershell
python .\skills\helin-analyze-livestream-commerce\scripts\transcript_ledger.py outline .\transcript.md
python .\skills\helin-analyze-livestream-commerce\scripts\transcript_ledger.py signals .\transcript.md
python .\skills\helin-analyze-livestream-commerce\scripts\transcript_ledger.py ledger .\transcript.md .\boundaries.tsv
```

无时间戳文稿可在子命令前加 `--duration-min 实际分钟数` 校准语速。

## 隐私与安全

真实直播文稿可能包含主播、品牌、客户和消费者信息。提交 Issue、Pull Request 或测试样本前请先匿名化；不要提交账号密码、Cookie、API Key、订单数据、用户个人信息或未经授权的客户资料。

## 许可证

本项目使用 [MIT License](LICENSE)，版权署名为河林。
