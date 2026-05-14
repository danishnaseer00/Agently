import { useState, useEffect, useRef } from 'react'

const COMMANDS = [
  {
    id: 'summarize',
    label: 'Summarize',
    description: 'Summarize the entire conversation',
    // icon: '📄',
  },
  {
    id: 'deepThink',
    label: 'Deep Think',
    description: 'Research thoroughly from multiple sources',
    // icon: '🔍',
  },
]

/**
 * Detect if the input value is a slash command.
 * Returns the matched command and any text after the command name.
 */
export function parseSlashCommand(input) {
  if (!input || !input.startsWith('/')) return null

  const trimmed = input.slice(1).trim() // remove leading /

  if (!trimmed) {
    // Just "/" typed, showing all commands
    return { partial: '', matched: null, fullText: '' }
  }

  // Split on first space to get command and args
  const spaceIdx = trimmed.indexOf(' ')
  const cmdPart = spaceIdx >= 0 ? trimmed.slice(0, spaceIdx) : trimmed
  const argsPart = spaceIdx >= 0 ? trimmed.slice(spaceIdx + 1) : ''

  // Find exact match
  const exact = COMMANDS.find((c) => c.id === cmdPart)
  if (exact) return { partial: cmdPart, matched: exact, fullText: argsPart }

  // Find partial matches for filtering
  return { partial: cmdPart, matched: null, fullText: '' }
}

export default function SlashCommandsDropdown({ inputValue, onSelect, onClose }) {
  const [selectedIndex, setSelectedIndex] = useState(0)
  const dropdownRef = useRef(null)

  const parsed = parseSlashCommand(inputValue)

  // Filter commands based on partial input
  const filtered = parsed
    ? COMMANDS.filter(
        (c) =>
          !parsed.partial ||
          c.id.startsWith(parsed.partial.toLowerCase()),
      )
    : []

  const visible = parsed !== null && filtered.length > 0

  useEffect(() => {
    setSelectedIndex(0)
  }, [inputValue])

  useEffect(() => {
    if (!visible) return

    const handleKeyDown = (e) => {
      if (e.key === 'ArrowDown') {
        e.preventDefault()
        setSelectedIndex((prev) => (prev + 1) % filtered.length)
      } else if (e.key === 'ArrowUp') {
        e.preventDefault()
        setSelectedIndex((prev) => (prev - 1 + filtered.length) % filtered.length)
      } else if (e.key === 'Enter' || e.key === 'Tab') {
        if (filtered[selectedIndex]) {
          e.preventDefault()
          onSelect(filtered[selectedIndex])
        }
      } else if (e.key === 'Escape') {
        e.preventDefault()
        onClose?.()
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [visible, filtered, selectedIndex, onSelect, onClose])

  if (!visible) return null

  return (
    <>
      {/* Backdrop to detect clicks outside */}
      <div
        style={{
          position: 'fixed',
          inset: 0,
          zIndex: 90,
        }}
        onClick={onClose}
      />

      <div
        ref={dropdownRef}
        style={{
          position: 'absolute',
          bottom: 'calc(100% + 8px)',
          left: 0,
          width: '320px',
          background: '#ffffff',
          border: '1px solid #e5e7eb',
          borderRadius: '12px',
          boxShadow: '0 10px 25px rgba(0,0,0,0.1)',
          zIndex: 100,
          overflow: 'hidden',
          animation: 'slideUp 0.15s ease-out',
        }}
      >
        <div style={{
          padding: '10px 14px',
          borderBottom: '1px solid #f3f4f6',
          fontSize: '0.75rem',
          color: '#9ca3af',
          textTransform: 'uppercase',
          letterSpacing: '0.05em',
          fontWeight: 600,
        }}>
          Commands
        </div>

        {filtered.map((cmd, idx) => (
          <button
            key={cmd.id}
            onClick={() => onSelect(cmd)}
            onMouseEnter={() => setSelectedIndex(idx)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              width: '100%',
              padding: '10px 14px',
              border: 'none',
              background: idx === selectedIndex ? '#f3f4f6' : 'transparent',
              cursor: 'pointer',
              textAlign: 'left',
              transition: 'background 0.1s ease',
              fontFamily: '"Computer Modern Serif", serif',
            }}
          >
            <span style={{ fontSize: '1.1rem', flexShrink: 0 }}>
              {cmd.icon}
            </span>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{
                fontWeight: 600,
                fontSize: '0.9rem',
                color: '#0b0b0d',
              }}>
                <span style={{ color: '#6b7280', fontWeight: 400 }}>/</span>
                {cmd.label}
              </div>
              <div style={{
                fontSize: '0.8rem',
                color: '#6b7280',
                marginTop: '2px',
              }}>
                {cmd.description}
              </div>
            </div>
            <kbd style={{
              fontSize: '0.7rem',
              color: '#9ca3af',
              background: '#f3f4f6',
              padding: '2px 6px',
              borderRadius: '4px',
              border: '1px solid #e5e7eb',
              fontFamily: '"Computer Modern Serif", serif',
            }}>
              ↵
            </kbd>
          </button>
        ))}
      </div>
    </>
  )
}
