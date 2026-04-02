---
layout: home

hero:
  name: Bedrock
  text: 公司级规范示例项目
  tagline: 所有子服务的规范源头、学习入口和设计语言参考
  actions:
    - theme: brand
      text: Claude Code 规范
      link: /superpowers/specs/2026-04-01-bedrock-design
    - theme: alt
      text: 后端架构
      link: /backend/architecture

features:
  - icon:
      src: /icons/terminal.svg
    title: Claude Code 规范
    details: 完整的 .claude/ 配置体系 — rules、skills、hooks、settings
    link: /claude/architecture
    linkText: 查看配置架构
  - icon:
      src: /icons/layers.svg
    title: 后端三层架构
    details: FastAPI + SQLAlchemy + dependency-injector，严格遵循 API → Service → Repository 分层规范
    link: /backend/architecture
    linkText: 查看架构文档
  - icon:
      src: /icons/palette.svg
    title: 前端设计系统
    details: React 19 + TypeScript + Tailwind CSS + shadcn/ui，features 模块化组织
    link: /frontend/development
    linkText: 查看开发指南
  - icon:
      src: /icons/blocks.svg
    title: Monorepo 工作区
    details: pnpm + uv 双工作区，packages/core、packages/llm、packages/knowledge 共享包
    link: /superpowers/plans/2026-04-01-bedrock-implementation
    linkText: 查看实现计划
---
