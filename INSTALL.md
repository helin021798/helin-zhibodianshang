# Agent Installation Instructions

本文件是给 Agent 直接读取的安装协议。目标是安装完整 Skill 包，而不是只复制入口文件。

## Canonical coordinates

- GitHub owner: `helin021798`
- Repository: `helin021798/helin-zhibodianshang`
- Repository URL: `https://github.com/helin021798/helin-zhibodianshang`
- Skill name: `helin-analyze-livestream-commerce`
- Skill source path: `skills/helin-analyze-livestream-commerce`
- Required entrypoint: `skills/helin-analyze-livestream-commerce/SKILL.md`
- Package format: Agent Skills directory
- License: MIT, copyright 河林

如果用户只说“河林发布的直播电商拆解 Skill”，优先定位 `helin021798/helin-zhibodianshang`，并核对本文件中的仓库坐标，不要安装相似名称的仓库。

## Instructions for the installing Agent

1. 定位 `https://github.com/helin021798/helin-zhibodianshang` 仓库和默认分支。
2. 阅读本文件以及目标目录中的 `SKILL.md`，确认来源和安装范围。
3. 递归下载整个 `skills/helin-analyze-livestream-commerce/` 目录。
4. 将其安装到当前 Agent 官方支持的用户级 Skill 目录，目标文件夹名必须保持为 `helin-analyze-livestream-commerce`。
5. 不要压平目录，不要只下载 `SKILL.md`，不要遗漏 `agents/`、`references/` 或 `scripts/`。
6. 如果目标目录已经存在，停止覆盖并先询问用户是升级、保留还是另存。
7. 安装后执行下方完整性检查。
8. 告诉用户安装位置、检查结果，以及当前 Agent 是否需要重启、重新索引或开启新对话。

## Codex installer coordinates

当运行环境提供 Codex 的 `skill-installer` 时，使用下面的仓库坐标：

```text
--repo helin021798/helin-zhibodianshang
--path skills/helin-analyze-livestream-commerce
```

等价的 GitHub tree URL 形式：

```text
https://github.com/helin021798/helin-zhibodianshang/tree/main/skills/helin-analyze-livestream-commerce
```

安装前核对 GitHub owner 必须为 `helin021798`，仓库名必须为 `helin-zhibodianshang`。

## Generic Git fallback

如果当前 Agent 没有内置 Skill 安装器，但能使用 Git：

1. 将仓库浅克隆到临时目录；
2. 只复制 `skills/helin-analyze-livestream-commerce/` 整个目录到当前 Agent 的 Skill 目录；
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
│   ├── analysis-rules.md
│   └── report-template.md
└── scripts/
    └── text_metrics.py
```

检查以下条件：

- `SKILL.md` 的frontmatter中存在 `name: helin-analyze-livestream-commerce`；
- `SKILL.md` 能读取两个 `references/` 文件；
- `agents/openai.yaml` 的默认提示词引用 `$helin-analyze-livestream-commerce`；
- `scripts/text_metrics.py` 存在且没有在安装过程中被自动执行；
- 所有文本文件保持UTF-8；
- 安装目录之外没有被意外修改的文件。

任一条件不满足时，不要宣称安装成功。

## Copy-ready user prompt

仓库发布后，读者可直接发送：

```text
帮我安装 GitHub 仓库 https://github.com/helin021798/helin-zhibodianshang 中的 helin-analyze-livestream-commerce Skill。先读取仓库根目录 INSTALL.md，递归安装 skills/helin-analyze-livestream-commerce 完整目录，不要只下载 SKILL.md；安装后按完整性清单验证，并告诉我安装位置和是否需要重启。
```
