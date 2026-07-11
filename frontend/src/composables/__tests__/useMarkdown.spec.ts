import { describe, expect, it } from 'vitest'

import { renderMarkdown } from '@/composables/useMarkdown'

describe('renderMarkdown', () => {
  it('renders source markers as anchor links to citation cards', () => {
    const html = renderMarkdown('结论来自课程大纲。[来源 1, 2]')

    expect(html).toContain('href="#citation-1"')
    expect(html).toContain('href="#citation-2"')
    expect(html).toContain('data-citation="1"')
    expect(html).toContain('来源 1')
  })

  it('renders bare source markers from LLM output as citation anchors', () => {
    const html = renderMarkdown('依据部分显示为 来源 1，另一个依据为 来源 2。')

    expect(html).toContain('href="#citation-1"')
    expect(html).toContain('href="#citation-2"')
    expect(html).toContain('data-citation="1"')
  })
})
