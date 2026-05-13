import { expect, test } from '@playwright/test'

test('roundtable decision flow persists discussion and follow-up', async ({ page }) => {
  const browserErrors: string[] = []
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
  await page.getByRole('button', { name: '全选' }).click()
  await page.getByRole('button', { name: '创建圆桌会话' }).click()
  const sessionPanel = page.locator('section', { hasText: '会话' })
  await expect(sessionPanel.getByText('ready')).toBeVisible()

  const sessionText = await sessionPanel.innerText()
  const sessionId = sessionText.match(/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/)?.[0]
  expect(sessionId).toBeTruthy()

  await page.getByRole('button', { name: '开始讨论流' }).click()
  await expect(sessionPanel.getByText('completed')).toBeVisible({ timeout: 15_000 })
  await page.getByText('建议').waitFor()

  await page.locator('#follow-up-question').fill('如果只能先做一件事，应该是什么？')
  await page.getByRole('button', { name: '提交追问' }).click()
  await page.getByText('追问').waitFor({ timeout: 15_000 })

  await page.goto(`/roundtable?session=${sessionId}`, { waitUntil: 'networkidle' })
  await page.getByText(sessionId ?? '').waitFor()
  await expect(page.locator('section', { hasText: '会话' }).getByText('completed')).toBeVisible()

  expect(browserErrors).toEqual([])
})
