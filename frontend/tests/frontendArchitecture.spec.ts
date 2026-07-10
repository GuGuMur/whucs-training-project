import { existsSync, readFileSync, readdirSync } from 'node:fs'
import { resolve } from 'node:path'

import { describe, expect, it } from 'vitest'

const srcRoot = resolve(__dirname, '..', 'src')
const layoutsRoot = resolve(srcRoot, 'layouts')
const frontendRoot = resolve(__dirname, '..')

describe('frontend source architecture', () => {
  it('keeps the agreed top-level feature boundaries', () => {
    expect(readdirSync(srcRoot).sort()).toEqual([
      'App.vue',
      'assets',
      'auth',
      'client',
      'components',
      'composables',
      'layouts',
      'main.ts',
      'plugins',
      'router',
      'stores',
      'views',
    ])
  })

  it('does not keep the deprecated services or starter icon folders', () => {
    expect(existsSync(resolve(srcRoot, 'services'))).toBe(false)
    expect(existsSync(resolve(srcRoot, 'components', 'icons'))).toBe(false)
    expect(existsSync(resolve(srcRoot, 'components', '__tests__'))).toBe(false)
    expect(existsSync(resolve(srcRoot, '__tests__'))).toBe(false)
  })

  it('splits workspace layouts by desktop and mobile shells', () => {
    expect(readdirSync(layoutsRoot).sort()).toEqual([
      'DesktopWorkspaceLayout.vue',
      'MobileWorkspaceLayout.vue',
    ])
    expect(existsSync(resolve(layoutsRoot, 'WorkspaceShell.vue'))).toBe(false)
  })

  it('keeps the OpenAPI generated client isolated under client', () => {
    const packageJson = JSON.parse(readFileSync(resolve(frontendRoot, 'package.json'), 'utf-8')) as {
      scripts: Record<string, string>
    }
    const configPath = resolve(frontendRoot, 'openapi-ts.config.ts')
    const config = readFileSync(configPath, 'utf-8')

    expect(packageJson.scripts['openapi:export']).toContain('uv run')
    expect(packageJson.scripts['openapi:generate']).toBe('openapi-ts')
    expect(packageJson.scripts['generate:client']).toContain('openapi:export')
    expect(existsSync(resolve(srcRoot, 'client', 'openapi', 'workspace.openapi.json'))).toBe(true)
    expect(existsSync(resolve(srcRoot, 'client', 'generated'))).toBe(true)
    expect(config).toContain("input: 'src/client/openapi/workspace.openapi.json'")
    expect(config).toContain("output: 'src/client/generated'")
  })

  it('routes workspace API calls through the generated SDK', () => {
    const workspaceClient = readFileSync(resolve(srcRoot, 'client', 'workspace.ts'), 'utf-8')

    expect(workspaceClient).toContain("@/client/generated")
    expect(workspaceClient).toContain('workspaceSnapshotApiV2WorkspaceSnapshotGet')
    expect(workspaceClient).not.toContain("from 'axios'")
  })

  it('proxies same-origin API calls to the FastAPI backend during local development', () => {
    const viteConfig = readFileSync(resolve(frontendRoot, 'vite.config.ts'), 'utf-8')

    expect(viteConfig).toMatch(/["']\/api["']/)
    expect(viteConfig).toMatch(/target:\s*["']http:\/\/127\.0\.0\.1:8000["']/)
    expect(viteConfig).toContain('changeOrigin: true')
  })
})
