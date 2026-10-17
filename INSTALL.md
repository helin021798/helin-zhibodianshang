# Agent Installation Instructions

本文件是给 Agent 直接读取的安装协议。目标是安装完整 Skill 包，而不是只复制入口文件。本仓库包含两个 Skill，用户要哪个就装哪个；用户只说“河林的直播 Skill”且没有指明时，两个都装。

## Canonical coordinates

- GitHub owner: `helin021798`
- Repository: `helin021798/helin-zhibodianshang`
- Repository URL: `https://github.com/helin021798/helin-zhibodianshang`
- Skill 1 name: `helin-analyze-livestream-commerce`（直播拆解）
  - source path: `skills/helin-analyze-livestream-commerce`
  - required entrypoint: `skills/helin-analyze-livestream-commerce/SKILL.md`
- Skill 2 name: `helin-livestream-planning-master`（直播策划大师）
  - source path: `skills/helin-livestream-planning-master`
  - required entrypoint: `skills/helin-livestream-planning-master/SKILL.md`
- Package format: Agent Skills directory
- License: MIT, copyright 河林

如果用户只说“河林发布的直播电商拆解 Skill”或“河林的直播策划 Skill”，优先定位 `helin021798/helin-zhibodianshang`，并核对本文件中的仓库坐标，不要安装相似名称的仓库。

## Instructions for the installing Agent

1. 定位 `https://github.com/helin021798/helin-zhibodianshang` 仓库和默认分支。
2. 阅读本文件以及目标目录中的 `SKILL.md`，确认来源和安装范围。
3. 递归下载要安装的每个 Skill 目录（`skills/helin-analyze-livestream-commerce/`、`skills/helin-livestream-planning-master/`）。
4. 将其安装到当前 Agent 官方支持的用户级 Skill 目录，目标文件夹名必须与源目录名保持一致。
5. 不要压平目录，不要只下载 `SKILL.md`，不要遗漏 `agents/`、`references/` 或 `scripts/`。
6. 如果目标目录已经存在，停止覆盖并先询问用户是升级、保留还是另存。
7. 安装后执行下方完整性检查。
8. 告诉用户安装位置、检查结果，以及当前 Agent 是否需要重启、重新索引或开启新对话。

## Codex installer coordinates

当运行环境提供 Codex 的 `skill-installer` 时，使用下面的仓库坐标：

```text
--repo helin021798/helin-zhibodianshang
--path skills/helin-analyze-livestream-commerce

--repo helin021798/helin-zhibodianshang
--path skills/helin-livestream-planning-master
```

等价的 GitHub tree URL 形式：

```text
https://github.com/helin021798/helin-zhibodianshang/tree/main/skills/helin-analyze-livestream-commerce
https://github.com/helin021798/helin-zhibodianshang/tree/main/skills/helin-livestream-planning-master
```

安装前核对 GitHub owner 必须为 `helin021798`，仓库名必须为 `helin-zhibodianshang`。

## Generic Git fallback

如果当前 Agent 没有内置 Skill 安装器，但能使用 Git：

1. 将仓库浅克隆到临时目录；
2. 只复制要安装的 `skills/<skill-name>/` 整个目录到当前 Agent 的 Skill 目录；
3. 删除临时克隆；
4. 按下面的文件清单验收。

不得假设所有 Agent 使用相同的本地安装路径。应优先遵循当前 Agent 的官方 Skill 目录约定。

## Required package integrity

安装后的目标目录至少必须包含：

```text
helin-analyze-livestream-commerce/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── references/
│   ├── helin-method.md
│   ├── analysis-rules.md
│   ├── report-template.md
│   └── example-report.md
└── scripts/
    └── transcript_ledger.py
```

```text
helin-livestream-planning-master/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── references/
│   ├── helin-method.md
│   ├── platform-channels.md
│   ├── platform-douyin.md
│   ├── platform-xhs.md
│   ├── model-knowledge-leads.md
│   ├── playbook-merch.md
│   ├── playbook-scripts.md
│   ├── playbook-traffic-ads.md
│   ├── playbook-private.md
│   ├── playbook-ops-review.md
│   ├── compliance.md
│   └── example-plan.md
└── scripts/
    └── live_calc.py
```

检查以下条件：

- 每个 `SKILL.md` 的frontmatter中存在与目录同名的 `name:`；
- 拆解 Skill 有 4 个 `references/` 文件，策划 Skill 有 12 个；
- `agents/openai.yaml` 的默认提示词引用对应的 `$<skill-name>`；
- `scripts/transcript_ledger.py`、`scripts/live_calc.py` 存在且没有在安装过程中被自动执行；
- 所有文本文件保持UTF-8；
- 安装目录之外没有被意外修改的文件。

任一条件不满足时，不要宣称安装成功。

## Copy-ready user prompt

仓库发布后，读者可直接发送：

```text
帮我安装 GitHub 仓库 https://github.com/helin021798/helin-zhibodianshang 中的 helin-analyze-livestream-commerce 和 helin-livestream-planning-master 两个 Skill。先读取仓库根目录 INSTALL.md，递归安装 skills/ 下这两个完整目录，不要只下载 SKILL.md；安装后按完整性清单验证，并告诉我安装位置和是否需要重启。
```
