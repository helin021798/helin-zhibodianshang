# Codex 产出声明

本项目及本目录内产出由 OpenAI Codex 创建。

- 项目名称：helin-zhibodianshang
- 建立日期：2026-08-01
- 当前状态：v2.1.0 完整开源版（含直播拆解与直播策划两个 Skill），发布地址 `https://github.com/helin021798/helin-zhibodianshang`
- 更新记录：v2.0.0 起由 Claude Code 协助升级，v2.1.0 新增直播策划 Skill，详见 `CHANGELOG.md`
- 产出用途：将河林提供的直播拆解提示词封装为可开源、可验证、可由 Agent 安装的 Skill

## 主要文件

- `README.md`：项目首页、使用方式与一句话安装入口
- `INSTALL.md`：给 Agent 直接读取的安装协议
- `SKILL_DETAILS.md`：Skill 的来源、能力、实际状态和限制
- `LICENSE`：MIT 开源许可证，署名河林
- `skills/helin-analyze-livestream-commerce/SKILL.md`：Skill 主入口
- `skills/helin-analyze-livestream-commerce/references/helin-method.md`：河林直播拆解方法论
- `skills/helin-analyze-livestream-commerce/references/analysis-rules.md`：分析与证据规则
- `skills/helin-analyze-livestream-commerce/references/report-template.md`：五模块报告模板
- `skills/helin-analyze-livestream-commerce/references/example-report.md`：虚构的金标准样例
- `skills/helin-analyze-livestream-commerce/scripts/transcript_ledger.py`：分段目录、信号线索、出场台账与语速校准工具
- `skills/helin-livestream-planning-master/`：直播策划大师 Skill（SKILL.md、12 个参考文件、`scripts/live_calc.py`）
- `evals/`：触发、行为与失败测试
- `tests/`：脚本单元测试
