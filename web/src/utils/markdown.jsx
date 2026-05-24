/**
 * Convert URLs in text to clickable <a> tags.
 */
export function linkify(text) {
  const regex = /https?:\/\/[^\s]+|www\.[^\s]+/g
  const tokens = []
  let lastIndex = 0
  for (const match of text.matchAll(regex)) {
    const start = match.index ?? 0
    if (start > lastIndex) {
      tokens.push(text.slice(lastIndex, start))
    }
    const rawUrl = match[0]
    const href = rawUrl.startsWith('http') ? rawUrl : `https://${rawUrl}`
    tokens.push(
      <a key={`${rawUrl}-${start}`} href={href} target="_blank" rel="noreferrer">
        {rawUrl}
      </a>,
    )
    lastIndex = start + rawUrl.length
  }
  if (lastIndex < text.length) {
    tokens.push(text.slice(lastIndex))
  }
  return tokens.length === 0 ? text : tokens
}

function parseInlineMarkdown(str) {
  const parts = []
  let lastIndex = 0
  // Match bold+italic, bold, italic, inline code, and links
  const regex = /\*\*\*([^*]+)\*\*\*|\*\*([^*]+)\*\*|\*([^*]+)\*|_([^_]+)_|`([^`]+)`|https?:\/\/[^\s]+|www\.[^\s]+/g

  for (const match of str.matchAll(regex)) {
    const start = match.index
    if (start > lastIndex) {
      parts.push(str.slice(lastIndex, start))
    }

    if (match[1]) {
      parts.push(<strong key={`${start}-bi`}><em>{match[1]}</em></strong>)
    } else if (match[2]) {
      parts.push(<strong key={`${start}-b`}>{match[2]}</strong>)
    } else if (match[3]) {
      parts.push(<em key={`${start}-i`}>{match[3]}</em>)
    } else if (match[4]) {
      parts.push(<em key={`${start}-i2`}>{match[4]}</em>)
    } else if (match[5]) {
      parts.push(<code key={`${start}-code`} className="inline-code">{match[5]}</code>)
    } else {
      const url = match[0]
      const href = url.startsWith('http') ? url : `https://${url}`
      parts.push(
        <a key={`${start}-link`} href={href} target="_blank" rel="noreferrer">
          {url}
        </a>,
      )
    }
    lastIndex = start + match[0].length
  }

  if (lastIndex < str.length) {
    parts.push(str.slice(lastIndex))
  }

  return parts.length === 0 ? str : parts
}

/**
 * Format assistant message text with rich formatting.
 * Supports: headings (##, ###), bold, italic, inline code, code blocks,
 * bullet lists, numbered lists, blockquotes, tables, and links.
 */
export function formatMarkdown(text) {
  // Remove <br> and <br/> tags
  text = text.replace(/<br\s*\/?>/gi, '\n')

  // Split into blocks (paragraphs, lists, headings, etc)
  const blocks = text.split(/\n{2,}/).map(block => block.trim()).filter(b => b)

  return blocks.map((block, idx) => {
    // ── Code block (```...``` or ````...````) ──────────────────────────
    if (block.startsWith('```') || block.startsWith('````')) {
      const match = block.match(/^`{3,4}(\w*)\n?([\s\S]*?)`{3,4}$/)
      if (match) {
        const lang = match[1] || ''
        const code = match[2].trim()
        return (
          <div key={idx} className="code-block-wrapper">
            {lang && <div className="code-lang">{lang}</div>}
            <pre className="code-block"><code>{code}</code></pre>
          </div>
        )
      }
      // Fallback: render as pre
      return (
        <pre key={idx} className="code-block">
          <code>{block.replace(/`{3,4}/g, '').trim()}</code>
        </pre>
      )
    }

    // ── Blockquote (lines starting with >) ────────────────────────────
    if (block.startsWith('>')) {
      const quoteLines = block.split('\n').filter(l => l.trim())
      return (
        <blockquote key={idx} className="blockquote">
          {quoteLines.map((line, i) => {
            const cleaned = line.replace(/^>\s?/, '')
            return <p key={i} style={{ margin: '4px 0' }}>{parseInlineMarkdown(cleaned)}</p>
          })}
        </blockquote>
      )
    }

    // ── Heading (### or ##) ───────────────────────────────────────────
    const headingMatch = block.match(/^(#{1,3})\s+(.+)/)
    if (headingMatch) {
      const level = headingMatch[1].length
      const text = headingMatch[2]
      const Tag = level === 1 ? 'h1' : level === 2 ? 'h2' : 'h3'
      return (
        <Tag key={idx} className={`heading heading-${level}`}>
          {parseInlineMarkdown(text)}
        </Tag>
      )
    }

    // ── Bullet list (lines starting with •, -, or *) ──────────────────
    if (block.includes('•') || block.match(/^\s*[-*]\s/m)) {
      const items = block.split('\n').filter(l => l.trim())
      return (
        <ul key={idx} className="list-bullet">
          {items.map((item, i) => {
            const cleaned = item.replace(/^[-*•]\s*/, '')
            return <li key={i}>{parseInlineMarkdown(cleaned)}</li>
          })}
        </ul>
      )
    }

    // ── Numbered list (lines starting with 1., 2., etc) ───────────────
    if (block.match(/^\d+\.\s/m)) {
      const items = block.split('\n').filter(l => l.trim())
      return (
        <ol key={idx} className="list-numbered">
          {items.map((item, i) => {
            const cleaned = item.replace(/^\d+\.\s*/, '')
            return <li key={i}>{parseInlineMarkdown(cleaned)}</li>
          })}
        </ol>
      )
    }

    // ── Table-like structure (contains | and ---) ─────────────────────
    if (block.includes('|') && block.includes('---')) {
      const lines = block.split('\n').filter(l => l.trim())
      const headerRow = lines[0].split('|').map(c => c.trim()).filter(Boolean)
      // Skip separator line (---|---)
      const dataRows = lines.slice(2).map(line =>
        line.split('|').map(c => c.trim()).filter(Boolean)
      )
      if (headerRow.length > 0 && dataRows.length > 0) {
        return (
          <div key={idx} className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>{headerRow.map((h, i) => <th key={i}>{parseInlineMarkdown(h)}</th>)}</tr>
              </thead>
              <tbody>
                {dataRows.map((row, ri) => (
                  <tr key={ri}>{row.map((cell, ci) => <td key={ci}>{parseInlineMarkdown(cell)}</td>)}</tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      }
      // Fallback table rendering (no separator line)
    }

    if (block.includes('|')) {
      const lines = block.split('\n').filter(l => l.trim())
      const rows = lines.map(line =>
        line.split('|').map(c => c.trim()).filter(Boolean)
      )
      if (rows.length > 1 && rows[0].length > 1) {
        const header = rows[0]
        const data = rows.slice(1).filter(r => r.length === header.length)
        return (
          <div key={idx} className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>{header.map((h, i) => <th key={i}>{parseInlineMarkdown(h)}</th>)}</tr>
              </thead>
              <tbody>
                {data.map((row, ri) => (
                  <tr key={ri}>{row.map((cell, ci) => <td key={ci}>{parseInlineMarkdown(cell)}</td>)}</tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      }
    }

    // ── Regular paragraph ─────────────────────────────────────────────
    return (
      <p key={idx} className="para">
        {parseInlineMarkdown(block)}
      </p>
    )
  })
}
