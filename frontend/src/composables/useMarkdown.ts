import MarkdownIt from 'markdown-it'

const md = new MarkdownIt({ breaks: true, linkify: true })

export function renderMarkdown(text: string): string {
  // Replace [来源 N] with unique placeholder tokens
  const citations: string[] = []
  let processed = text.replace(
    /\[来源\s*(\d+(?:,\s*\d+)*)\]/g,
    (_match: string, nums: string) => {
      const idx = citations.length
      citations.push(nums)
      return `{{CITE${idx}}}`
    }
  )

  // Render markdown
  let html = md.render(processed)

  // Replace placeholders with clickable citation badges (post-markdown)
  citations.forEach((nums, i) => {
    const badges = nums.split(',').map((id: string) =>
      `<span class="citation-badge" data-citation="${id.trim()}" title="跳转到引用 ${id.trim()}">📎 来源 ${id.trim()}</span>`
    ).join(' ')
    html = html.replace(`{{CITE${i}}}`, badges)
  })

  return html
}
