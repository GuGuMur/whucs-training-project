import { expect, test } from '@playwright/test'

test('redirects an unauthenticated workflow visit to login', async ({ page }) => {
  await page.goto('/workflow')

  await expect(page).toHaveURL(/\/login\?redirect=\/workflow/)
  await expect(page.getByRole('heading', { name: '智能文件管理平台' })).toBeVisible()
})

test('authors a Vue Flow graph in the browser', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('whu-workspace-session', JSON.stringify({
      accessToken: 'e2e-token',
      displayName: 'E2E 用户',
      refreshToken: 'e2e-refresh',
      userId: '1',
    }))
  })

  await page.route('**/api/v2/**', async (route) => {
    const url = new URL(route.request().url())
    const path = url.pathname
    const json = path === '/api/v2/users/me'
      ? { user: { id: 1, username: 'e2e', email: 'e2e@example.com', display_name: 'E2E 用户', roles: ['admin'] } }
      : path === '/api/v2/workspace/snapshot'
        ? {
            audit_logs: [], files: [], folders: [], knowledge_bases: [], teams: [], workflows: [],
            tools: [{
              id: 'calculator', name: 'calculator', version: '1.0.0', category: 'general',
              description: '安全计算表达式', enabled: true, risk_level: 'low',
              input_schema: { type: 'object', properties: { expression: { type: 'string' } }, required: ['expression'] },
              output_schema: { type: 'object' },
            }],
            summary: { file_count: 0, indexed_count: 0, knowledge_base_count: 0, running_workflows: 0, tools_enabled: 1, unread_notifications: 0 },
          }
        : path === '/api/v2/tools'
          ? { items: [{
              id: 'calculator', name: 'calculator', version: '1.0.0', category: 'general',
              description: '安全计算表达式', enabled: true, risk_level: 'low',
              input_schema: { type: 'object', properties: { expression: { type: 'string' } }, required: ['expression'] },
              output_schema: { type: 'object' },
            }] }
          : path === '/api/v2/workflows' || path === '/api/v2/agents/tasks'
            ? { items: [] }
            : { items: [] }
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(json) })
  })

  await page.goto('/workflow')

  await expect(page.getByText('节点库')).toBeVisible()
  await expect(page.locator('.vue-flow')).toBeVisible()
  await page.getByTestId('palette-input-text').click()
  await page.getByTestId('palette-tool-calculator').click()
  await page.getByRole('button', { name: '添加输出节点' }).click()

  await expect(page.locator('.graph-node')).toHaveCount(3)
  await expect(page.getByText('节点配置')).toBeVisible()
  await expect(page.getByText('calculator', { exact: true }).last()).toBeVisible()

  await page.getByRole('button', { name: '撤销' }).click()
  await expect(page.locator('.graph-node')).toHaveCount(2)
  await page.getByRole('button', { name: '重做' }).click()
  await expect(page.locator('.graph-node')).toHaveCount(3)

  await page.locator('.graph-node').first().click()
  await page.keyboard.press('Delete')
  await expect(page.locator('.graph-node')).toHaveCount(2)

  const canvasBounds = await page.locator('.workflow-canvas-shell').boundingBox()
  const viewport = page.viewportSize()
  expect(canvasBounds).not.toBeNull()
  expect(viewport).not.toBeNull()
  expect(canvasBounds!.y + canvasBounds!.height).toBeLessThanOrEqual(viewport!.height)
})
