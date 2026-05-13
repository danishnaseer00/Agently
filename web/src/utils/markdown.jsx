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
  // Match bold, italic, and links
  const regex = /\*\*\*([^*]+)\*\*\*|\*\*([^*]+)\*\*|\*([^*]+)\*|_([^_]+)_|https?:\/\/[^\s]+|www\.[^\s]+/g

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
 * Format assistant message text with markdown-like formatting.
 * Supports: bold, italic, lists (•), tables, links, paragraphs.
 */
export function formatMarkdown(text) {
  // Remove <br> and <br/> tags
  text = text.replace(/<br\s*\/?>/gi, '\n')

  // Split into blocks (paragraphs, lists, etc)
  const blocks = text.split(/\n{2,}/).map(block => block.trim()).filter(b => b)

  return blocks.map((block, idx) => {
    // Check if it's a list
    if (block.includes('•') || block.match(/^\s*[-*]\s/m)) {
      const items = block.split('\n').filter(l => l.trim())
      return (
        <ul key={idx} style={{ marginLeft: '20px', marginBottom: '12px' }}>
          {items.map((item, i) => {
            const cleaned = item.replace(/^[-*•]\s*/, '')
            return <li key={i} style={{ marginBottom: '6px' }}>{parseInlineMarkdown(cleaned)}</li>
          })}
        </ul>
      )
    }

    // Check if it's a table-like structure
    if (block.includes('|')) {
      return (
        <div key={idx} style={{ marginBottom: '12px', overflowX: 'auto' }}>
          <pre style={{ background: '#f5f5f5', padding: '10px', borderRadius: '4px', fontSize: '12px' }}>
            {block}
          </pre>
        </div>
      )
    }

    // Regular paragraph
    return (
      <p key={idx} style={{ marginBottom: '12px', lineHeight: '1.6' }}>
        {parseInlineMarkdown(block)}
      </p>
    )
  })
}
