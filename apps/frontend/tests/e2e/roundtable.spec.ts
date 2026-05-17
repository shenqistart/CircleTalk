import { expect, test } from '@playwright/test'

test('roundtable decision flow persists discussion and follow-up', async ({ page }) => {
  const browserErrors: string[] = []
  const sessionId = '26bb5d37-d217-4834-bc8f-516c71f5da7c'
  const createdAt = new Date('2026-05-13T00:00:00.000Z').toISOString()
  const personas = [
    {
      id: 'drucker',
      displayName: '彼得·德鲁克',
      skillName: 'nuwa-skill/drucker',
      summary: '关注目标、责任、组织绩效与可执行管理动作。',
      selectionReason: '适合把讨论收敛到责任人与下一步。',
    },
    {
      id: 'munger',
      displayName: '查理·芒格',
      skillName: 'nuwa-skill/munger',
      summary: '强调反向思考、激励机制与跨学科模型。',
      selectionReason: '适合发现明显但容易忽略的失败路径。',
    },
  ]
  let sessionStatus = 'ready'
  let hasFollowUp = false

  function sessionPayload() {
    return {
      id: sessionId,
      decisionPrompt: 'E2E 浏览器：是否现在把后端部署到 Render 并开放接口？',
      status: sessionStatus,
      selectedPersonas: personas.map((persona, index) => ({ ...persona, selectionSource: 'manual', sequence: index + 1 })),
      transcript: [
        {
          id: `${sessionId}-user`,
          role: 'user',
          content: 'E2E 浏览器：是否现在把后端部署到 Render 并开放接口？',
          roundName: 'system',
          sequence: 1,
          createdAt,
        },
        {
          id: `${sessionId}-opening`,
          role: 'persona',
          personaId: 'drucker',
          personaName: '彼得·德鲁克',
          content: '先定义目标、责任人与验收标准，再决定是否开放接口。',
          roundName: 'opening',
          sequence: 2,
          createdAt,
        },
        ...(hasFollowUp
          ? [
              {
                id: `${sessionId}-follow-up`,
                role: 'moderator',
                content: '追问后的建议是先确认接口责任人与回滚路径。',
                roundName: 'follow_up',
                sequence: 3,
                createdAt,
              },
            ]
          : []),
      ],
      artifacts: {
        memo: '先以受控试放验证链路。',
        recommendation: '建议先开放白名单接口，并设置回滚条件。',
        reasons: ['控制风险', '验证真实链路', '保留回滚余地'],
        debateMap: personas.map((persona) => ({
          personaName: persona.displayName,
          position: '支持受控试放。',
          keyConcern: persona.selectionReason,
        })),
      },
      createdAt,
      updatedAt: createdAt,
    }
  }

  await page.route('**/api/roundtable/personas?**', async (route) => {
    await route.fulfill({ contentType: 'application/json', json: personas })
  })
  await page.route('**/api/roundtable/personas/recommend', async (route) => {
    await route.fulfill({ contentType: 'application/json', json: personas })
  })
  await page.route('**/api/roundtable/sessions', async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      json: { recommendedPersonas: personas, session: sessionPayload() },
    })
  })
  await page.route(`**/api/roundtable/sessions/${sessionId}/stream`, async (route) => {
    sessionStatus = 'completed'
    await route.fulfill({ body: '圆桌讨论完成。', contentType: 'text/plain' })
  })
  await page.route(`**/api/roundtable/sessions/${sessionId}/follow-up/stream`, async (route) => {
    hasFollowUp = true
    await route.fulfill({ body: '追问完成。', contentType: 'text/plain' })
  })
  await page.route(`**/api/roundtable/sessions/${sessionId}`, async (route) => {
    await route.fulfill({ contentType: 'application/json', json: sessionPayload() })
  })

  page.on('pageerror', (error) => browserErrors.push(error.message))
  page.on('console', (message) => {
    if (message.type() === 'error') {
      browserErrors.push(message.text())
    }
  })

  await page.goto('/roundtable', { waitUntil: 'networkidle' })
  await page.locator('#app-language').selectOption('zh')
  await page
    .getByPlaceholder('例如：我是否应该在今年把团队从外包交付转成自研产品？')
    .fill('E2E 浏览器：是否现在把后端部署到 Render 并开放接口？')
  await page.getByRole('button', { name: '推荐人物' }).click()
  await expect(page.getByRole('heading', { name: '人物选择' })).toBeVisible()
  await page.getByRole('button', { name: '全选' }).click()
  await page.getByRole('button', { name: '创建圆桌会话' }).click()
  const sessionPanel = page.locator('section', { hasText: '会话' })
  await expect(sessionPanel.getByText('ready')).toBeVisible()

  await expect(page.getByText(sessionId)).toBeVisible()

  await page.getByRole('button', { name: '开始讨论流' }).click()
  await expect(page.getByRole('heading', { name: '讨论时间线' })).toBeVisible()
  await expect(page.getByRole('heading', { name: '结论' })).toBeHidden()
  await expect(page.getByText('圆桌讨论完成。')).toBeHidden()
  await page.getByRole('button', { name: /结论/ }).click()
  await expect(page.getByRole('heading', { name: '结论' })).toBeVisible()
  await expect(page.getByRole('heading', { name: '建议' })).toBeVisible()

  await page.getByRole('button', { name: /流式讨论与追问/ }).click()
  await expect(page.getByRole('heading', { name: '讨论时间线' })).toBeVisible()
  await expect(page.getByRole('heading', { name: '结论' })).toBeHidden()
  await expect(page.getByText('先定义目标、责任人与验收标准，再决定是否开放接口。')).toBeVisible()
  await page.locator('#follow-up-question').fill('如果只能先做一件事，应该是什么？')
  await page.getByRole('button', { name: '提交追问' }).click()
  await expect(page.getByText('追问后的建议是先确认接口责任人与回滚路径。')).toBeVisible()
  await expect(page.getByText('追问完成。')).toBeHidden()

  await page.goto(`/roundtable?session=${sessionId}`, { waitUntil: 'networkidle' })
  await expect(page.getByRole('heading', { name: '结论' })).toBeVisible()
  await expect(page.getByText('completed').first()).toBeVisible()

  expect(browserErrors).toEqual([])
})
