export const sidebar = [
  {
    text: '概览',
    link: '/',
  },
  {
    text: 'Claude Code 指南',
    collapsed: false,
    items: [
      { text: '项目配置架构解析', link: '/claude/architecture' },
      { text: '速查手册', link: '/claude/cheatsheet' },
      { text: '进阶定制指南', link: '/claude/customization' },
    ],
  },
  {
    text: '后端架构',
    collapsed: false,
    items: [
      { text: '后端架构与开发规范', link: '/backend/architecture' },
      { text: '依赖注入架构指南', link: '/backend/dependency-injection' },
    ],
  },
  {
    text: '前端开发',
    collapsed: false,
    items: [
      { text: '前端开发指南', link: '/frontend/development' },
      { text: 'Electron 桌面端开发指南', link: '/frontend/electron' },
    ],
  },
  {
    text: '共享包（Packages）',
    collapsed: false,
    items: [
      { text: 'Core 基础设施', link: '/packages/core' },
      { text: 'LLM 能力封装', link: '/packages/llm' },
      { text: 'Knowledge 知识库', link: '/packages/knowledge' },
    ],
  },
  {
    text: 'Superpowers',
    collapsed: false,
    items: [
      {
        text: '设计文档',
        collapsed: false,
        items: [
          { text: 'Bedrock 设计文档', link: '/superpowers/specs/2026-04-01-bedrock-design' },
        ],
      },
      {
        text: '实现计划',
        collapsed: false,
        items: [
          { text: 'Bedrock 实现计划', link: '/superpowers/plans/2026-04-01-bedrock-implementation' },
        ],
      },
    ],
  },
]
