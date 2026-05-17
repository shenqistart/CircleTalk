---
title: "Understand-Anything 项目梳理流程"
---

# Understand-Anything 项目梳理流程

本文记录 Bedrock 当前仓库已采用的 Understand-Anything 用法，也可作为其他项目复用的安装、分析、验证流程。

## 适用场景

Understand-Anything 适合用在以下场景：

- 新成员快速理解陌生代码库
- 为大型仓库生成结构图谱、架构层和学习路径
- 在评审前查看变更影响面
- 把项目知识图谱提交到仓库，作为团队共享的 onboarding 资料

## 一次性安装

Codex 环境使用通用安装脚本：

```bash
curl -fsSL https://raw.githubusercontent.com/Lum1104/Understand-Anything/main/install.sh | bash -s codex
```

安装结果：

- 插件仓库位于 `~/.understand-anything/repo`
- 通用插件根链接位于 `~/.understand-anything-plugin`
- skills 链接到 `~/.agents/skills/understand*`

安装或更新后重启 Codex/CLI/IDE，让新 skills 生效。

## 每个项目的忽略规则

在目标项目根目录维护：

```text
.understand-anything/.understandignore
```

Bedrock 当前规则重点排除：

- 依赖目录：`node_modules/`、`.venv/`、`vendor/`
- 构建产物：`dist/`、`build/`、`.next/`、`coverage/`
- 缓存：`.pytest_cache/`、`.ruff_cache/`、`.cache/`、`__pycache__/`
- 锁文件：`pnpm-lock.yaml`、`uv.lock`、`package-lock.json`、`yarn.lock`
- 本地分析输出：`.understand-anything/intermediate/`、`.understand-anything/tmp/`、`.understand-anything/diff-overlay.json`
- 大型/二进制/生成文件：图片、字体、压缩包、PDF、source map、minified assets
- 本地环境文件：`.env`、`.env.*`，但保留 `!.env.example`

其他项目复用时，先复制这份规则，再根据项目栈补充：

```text
# Go
bin/
coverage.out

# Java
target/
.gradle/

# .NET
obj/
bin/

# Python
.mypy_cache/
.tox/
```

## 生成图谱

常规用法：

```bash
/understand --language zh
```

如果当前运行时尚未重新加载新安装的 skill，也可以让 Codex 按 Understand-Anything core 的方式执行确定性结构抽取：

1. 读取 `.understand-anything/.understandignore`
2. 使用插件 core 的 `TreeSitterPlugin`、内置 parser 和 schema
3. 写出 `.understand-anything/knowledge-graph.json`
4. 写出 `.understand-anything/meta.json`、`config.json`、`fingerprints.json`
5. 使用 `validateGraph` 验证图谱

Bedrock 当前已生成的图谱概况：

| 指标 | 数值 |
|------|------|
| 扫描文件 | 284 |
| 图谱节点 | 1773 |
| 图谱边 | 1542 |
| 架构层 | 7 |
| Tour 步骤 | 7 |
| 识别框架 | FastAPI、React |

## 启动 Dashboard

```bash
cd ~/.understand-anything/repo/understand-anything-plugin
GRAPH_DIR=/path/to/project corepack pnpm --filter @understand-anything/dashboard dev --host 127.0.0.1
```

终端会输出带 token 的地址：

```text
Dashboard URL: http://127.0.0.1:5173/?token=<token>
```

必须使用带 `token` 的 URL。没有 token 时，`knowledge-graph.json`、源码预览和 meta/config 接口会返回 `403`。

## 验证清单

生成后至少检查：

```bash
# schema 校验
node --input-type=module -e "import fs from 'node:fs'; import { validateGraph } from '~/.understand-anything/repo/understand-anything-plugin/packages/core/dist/index.js'; const g=JSON.parse(fs.readFileSync('.understand-anything/knowledge-graph.json','utf8')); console.log(validateGraph(g).success)"

# 忽略规则是否生效
node --input-type=module -e "import fs from 'node:fs'; const g=JSON.parse(fs.readFileSync('.understand-anything/knowledge-graph.json','utf8')); const paths=g.nodes.map(n=>n.filePath).filter(Boolean); console.log(paths.filter(p=>/node_modules|pnpm-lock\\.yaml|uv\\.lock|(^|\\/)dist(\\/|$)|(^|\\/)build(\\/|$)/.test(p)))"

# Dashboard 数据接口
curl 'http://127.0.0.1:5173/knowledge-graph.json?token=<token>' | jq '.nodes | length'
```

当前 Bedrock 验证结果：

- `validateGraph`：通过，0 个 issue
- 忽略规则命中检查：0 个 forbidden path
- dashboard token 接口：可读取 1773 个节点、1542 条边
- 无 token 访问图谱接口：返回 `403`
- 源码预览接口：可读取 `README.md`

## 团队共享建议

建议提交：

- `.understand-anything/.understandignore`
- `.understand-anything/knowledge-graph.json`
- `.understand-anything/meta.json`
- `.understand-anything/config.json`
- `.understand-anything/fingerprints.json`

不要提交：

- `.understand-anything/intermediate/`
- `.understand-anything/tmp/`
- `.understand-anything/diff-overlay.json`

如果图谱超过 10 MB，再考虑用 Git LFS 管理 `.understand-anything/*.json`。
