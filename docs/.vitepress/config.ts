import { defineConfig } from 'vitepress'
import { sidebar } from './sidebar'

export default defineConfig({
  title: 'Bedrock 技术文档',
  description: '公司级规范示例项目技术文档 — 后端架构、前端开发、Claude Code 规范',

  // 忽略死链接检查（plans 目录的历史文档可能有失效链接）
  ignoreDeadLinks: true,

  themeConfig: {
    sidebar,
    search: {
      provider: 'local',
      options: {
        translations: {
          button: { buttonText: '搜索', buttonAriaLabel: '搜索' },
          modal: {
            noResultsText: '无结果',
            resetButtonTitle: '清除',
            footer: { selectText: '选择', navigateText: '导航', closeText: '关闭' },
          },
        },
      },
    },
    outline: {
      level: [2, 3],
      label: '目录',
    },
    lastUpdated: {
      text: '最后更新',
    },
    docFooter: {
      prev: '上一页',
      next: '下一页',
    },
    nav: [
      { text: 'Claude Code', link: '/claude/architecture' },
      { text: '后端', link: '/backend/architecture' },
      { text: '前端', link: '/frontend/development' },
      { text: '共享包', link: '/packages/core' },
      { text: 'Superpowers', link: '/superpowers/specs/2026-04-01-bedrock-design' },
    ],
  },

  markdown: {
    theme: {
      light: 'github-light',
      dark: 'github-dark',
    },
    lineNumbers: true,
  },
})
