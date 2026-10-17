# helin-zhibodianshang

河林发布的两个直播电商 Agent Skill，完整版开源，共用“憋单—卡单—踢单—促单”这套术语：

| Skill | 做什么 | 一句话触发 |
|---|---|---|
| `helin-analyze-livestream-commerce` 直播拆解 | 给一份直播回放转写稿，生成基于文稿证据的五模块拆解报告 | “拆解直播” |
| `helin-livestream-planning-master` 直播策划大师 | 给产品资料和经营目标，输出整场直播策划或单模块方案 | “做直播策划” |

两者可以串起来用：先拆对标直播间或上一场回放，再把拆解报告交给策划 skill 做下一场。

当前版本：`v2.1.0`（更新记录见 [`CHANGELOG.md`](CHANGELOG.md)）。已发布于 `https://github.com/helin021798/helin-zhibodianshang`。

> **给 Agent 的安装入口：[`INSTALL.md`](INSTALL.md)**  
> **Skill 目录：`skills/helin-analyze-livestream-commerce/`、`skills/helin-livestream-planning-master/`**  
> **Skill 详细说明：[`SKILL_DETAILS.md`](SKILL_DETAILS.md)**

## 给读者的一句话

推荐把下面这句话直接发给自己的 Agent：

```text
帮我安装 GitHub 仓库 https://github.com/helin021798/helin-zhibodianshang 中的两个 Skill：helin-analyze-livestream-commerce 和 helin-livestream-planning-master。请先读取仓库根目录 INSTALL.md，安装完整 Skill 目录，不要只下载 SKILL.md；安装完成后按 INSTALL.md 的清单验证，并告诉我是否需要重启或开启新对话。
```

只装其中一个时，把句子里的另一个 Skill 名删掉即可。

## 直播拆解：它能做什么

- 用台账脚本把长文稿切段、计量，自动校准语速，统计每个商品的出场、返场和累计时长；
- 识别全场商品、价格机制、核心卖点，用 A–F 六项信号综合判定货盘角色；
- 还原包含开场、抽奖、下场预告等非商品段的完整排品动线；
- 逐轮拆解主推品的憋单、卡单、踢单、促单循环，并对照平台节奏做判断；
- 整理主播复述或回答过的用户问题，找出没被接住的高意向提问；
- 从转写稿中整理最多两个主推品的话术，标注极限词、虚构稀缺、功效宣称等合规风险；
- 抽象带合规提示的可复用话术框架，输出有文稿依据的亮点和优化建议；
- 用户提供直播数据时，可以把动作和数据变化对齐做对照。

它不分析投流、付费流量、ROI或广告策略，也不会从直播话术反推真实销量、在线人数和GMV。

## 直播策划：它能做什么

- 覆盖抖音、视频号、小红书三个平台 × 电商带货、知识付费/线索获客两种业态；
- 七模块工作流：流量获取、直播排品、营销玩法、塑品话术、投流策略（只到策划层）、私域联动、节奏与分工；
- 四种模式：整场策划、单模块速出、诊断救场（“直播间没人/不转化”）、根据上一场数据复盘校准；
- 写方案前先做可行性判断，用 `live_calc.py` 算保本 ROI、坑产缺口和机制让利；
- 每个关键数字和规则都标来源：〔河林方法〕〔行业经验·年月〕〔推断〕〔待确认〕；
- 内置合规红线：稀缺话术、价格对比、功效宣称、站外导流、教培资质都有替换写法。

它不承诺在线人数、GMV、ROI 或平台推荐结果，也不做投流账户搭建。

## 直播拆解：最简使用方法

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

策划 skill 的用法：

```text
请使用 $helin-livestream-planning-master。
视频号护肤品牌官号，周年专场 3 小时，目标 GMV 18 万，产品清单和毛利见附件。
帮我做直播策划。
```

## 拆解报告的固定结构

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
│   ├── helin-analyze-livestream-commerce/
│   │   ├── SKILL.md
│   │   ├── agents/openai.yaml
│   │   ├── references/
│   │   │   ├── helin-method.md
│   │   │   ├── analysis-rules.md
│   │   │   ├── report-template.md
│   │   │   └── example-report.md
│   │   └── scripts/transcript_ledger.py
│   └── helin-livestream-planning-master/
│       ├── SKILL.md
│       ├── agents/openai.yaml
│       ├── references/
│       │   ├── helin-method.md
│       │   ├── platform-channels.md / platform-douyin.md / platform-xhs.md
│       │   ├── model-knowledge-leads.md
│       │   ├── playbook-merch.md / playbook-scripts.md / playbook-traffic-ads.md
│       │   ├── playbook-private.md / playbook-ops-review.md
│       │   ├── compliance.md
│       │   └── example-plan.md
│       └── scripts/live_calc.py
├── CHANGELOG.md
├── evals/
└── tests/
```

## 本地开发与验证

验证 Skill 结构：

```powershell
skills-ref validate .\skills\helin-analyze-livestream-commerce
skills-ref validate .\skills\helin-livestream-planning-master
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

策划测算（百分比参数一律写百分数，30 表示 30%，1 表示 1%）：

```powershell
python .\skills\helin-livestream-planning-master\scripts\live_calc.py roi --margin 60 --sign-rate 85 --fee 5 --target-net 10
python .\skills\helin-livestream-planning-master\scripts\live_calc.py pit --items "主推A:299:300,福利B:39.9:800" --target 200000
python .\skills\helin-livestream-planning-master\scripts\live_calc.py mech --items "赠品小样:12:500,免单抽奖:299:3" --gmv 200000 --margin 40
```

## 隐私与安全

真实直播文稿可能包含主播、品牌、客户和消费者信息。提交 Issue、Pull Request 或测试样本前请先匿名化；不要提交账号密码、Cookie、API Key、订单数据、用户个人信息或未经授权的客户资料。

## 内容来源与使用边界

两个 Skill 的方法论由河林本人的专栏、文章、分享和操盘经验提炼；平台文件中的行业经验为转述提炼，均标注原资料时间。平台规则变化很快，引用时以平台现行规则为准；合规提示是风险提醒，不是法律意见。案例均已匿名。

## 许可证

本项目使用 [MIT License](LICENSE)，版权署名为河林。
