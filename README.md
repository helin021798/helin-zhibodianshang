# helin-zhibodianshang

河林发布的直播电商拆解 Agent Skill。给它一份直播回放语音转写稿，再说“拆解直播”，即可按照固定五模块框架生成基于文稿证据的直播拆解报告。

当前版本：`v0.1.0`。已发布于 `https://github.com/helin021798/helin-zhibodianshang`，本地结构、脚本测试和完整目录模拟安装均已通过。

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

- 识别全场产品、价格机制、核心卖点和货盘角色；
- 还原产品出场、转场和返场动线；
- 拆解主推品的亮价、库存、紧迫感和售后兜底节奏；
- 从ASR转写稿中提纯最多两个主推品的话术流程；
- 抽象可迁移的话术框架；
- 输出有具体文稿依据的操盘级亮点和优化建议。

它不分析投流、付费流量、ROI或广告策略，也不会从直播话术反推真实销量、在线人数和GMV。

## 最简使用方法

提供：

- 必需：直播回放语音转写稿；
- 建议：品类或行业；
- 可选：账号名称、实际直播时长、已知主推品。

然后说：

```text
请使用 $helin-analyze-livestream-commerce。
附件是某美妆直播间的完整转写稿，直播时长约90分钟。
拆解直播。
```

## 固定报告结构

1. 直播货盘总览；
2. 排品策略与节奏拆解；
3. 主推品话术整理；
4. 可复用话术框架；
5. 综合点评。

## 关键分析边界

- 没有原始时间戳时，只能按每分钟250个有效字估算，并明确标注“估算”。
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
│       │   ├── analysis-rules.md
│       │   └── report-template.md
│       └── scripts/text_metrics.py
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

计算UTF-8文稿或已切分话术的有效字数和预估时长：

```powershell
python .\skills\helin-analyze-livestream-commerce\scripts\text_metrics.py .\transcript.md
```

## 隐私与安全

真实直播文稿可能包含主播、品牌、客户和消费者信息。提交 Issue、Pull Request 或测试样本前请先匿名化；不要提交账号密码、Cookie、API Key、订单数据、用户个人信息或未经授权的客户资料。

## 许可证

本项目使用 [MIT License](LICENSE)，版权署名为河林。
