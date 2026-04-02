# Bedrock Project Skills

项目专用技能，通过 Claude Code 的 `/` 命令触发。

## 可用技能

| 技能 | 用途 | 触发方式 |
|------|------|---------|
| enforcing-project-standards | 代码审计（plan 对齐 + 静态分析 + 架构检查） | `/enforcing-project-standards` |
| running-project-tests | 测试执行（测试金字塔 + fixture + 智能选择） | `/running-project-tests` |
| delivering-changes | 交付流水线（lint → test → commit → PR） | `/delivering-changes` |
| upgrading-dependencies | 依赖升级（前端 pnpm + 后端 uv） | `/upgrading-dependencies` |

## 技能目录结构

每个技能包含：
- `SKILL.md` — 技能定义（描述 + 触发条件 + 执行步骤）
- 可选参考文件（如 FILTERS.md、PATTERNS.md）
