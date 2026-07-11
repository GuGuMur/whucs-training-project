import MarkdownIt from 'markdown-it'

const md = new MarkdownIt({ breaks: true, linkify: true })

export function renderMarkdown(text: string): string {
  // Replace [来源 N] and bare 来源 N with unique placeholder tokens.
  const citations: string[] = []
  let processed = text.replace(
    /(^|[^\w#-])(?:\[来源\s*(\d+(?:\s*[,，、]\s*\d+)*)\]|来源\s*(\d+(?:\s*[,，、]\s*\d+)*))/g,
    (_match: string, prefix: string, bracketNums?: string, bareNums?: string) => {
      const idx = citations.length
      citations.push(bracketNums ?? bareNums ?? '')
      return `${prefix}{{CITE${idx}}}`
    }
  )

  // Render markdown
  let html = md.render(processed)

  // Replace placeholders with clickable citation badges (post-markdown)
  citations.forEach((nums, i) => {
    const badges = nums.split(/[,，、]/).map((id: string) =>
      `<a class="citation-badge" href="#citation-${id.trim()}" data-citation="${id.trim()}" title="跳转到引用 ${id.trim()}">来源 ${id.trim()}</a>`
    ).join(' ')
    html = html.replace(`{{CITE${i}}}`, badges)
  })

  return html
}
