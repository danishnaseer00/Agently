import { useEffect, useMemo, useRef, useState } from 'react'

const STORAGE_KEY = 'react-agent.conversations.v1'
const API_BASE = import.meta.env.VITE_API_URL || ''

const createConversation = () => ({
  id: typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : Date.now().toString(),
  title: 'New chat',
  createdAt: Date.now(),
  messages: [],
})

const loadConversations = () => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return [createConversation()]
    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed) || parsed.length === 0) return [createConversation()]
    return parsed
  } catch {
    return [createConversation()]
  }
}

const saveConversations = (conversations) => {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations))
}

const chunkedHistory = (messages) =>
  messages.map((message) => ({ role: message.role, content: message.content }))

const parseSsePayload = (text) => {
  const lines = text.split('\n')
  let event = 'message'
  let data = ''
  for (const line of lines) {
    if (line.startsWith('event:')) event = line.replace('event:', '').trim()
    if (line.startsWith('data:')) data += line.replace('data:', '').trim()
  }
  return { event, data }
}

function App() {
  const [conversations, setConversations] = useState(loadConversations)
  const [activeId, setActiveId] = useState(null)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [isThinking, setIsThinking] = useState(false)
  const [statusText, setStatusText] = useState('')
  const [inputValue, setInputValue] = useState('')
  const bottomRef = useRef(null)

  const activeConversation = useMemo(
    () => conversations.find((item) => item.id === activeId) || conversations[0],
    [conversations, activeId],
  )

  useEffect(() => {
    saveConversations(conversations)
  }, [conversations])

  useEffect(() => {
    if (!activeId && conversations.length > 0) {
      setActiveId(conversations[0].id)
      return
    }
    if (activeId && !conversations.some((item) => item.id === activeId)) {
      setActiveId(conversations[0]?.id || null)
    }
  }, [activeId, conversations])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [activeConversation?.messages, isThinking, statusText])

  const updateConversation = (id, updater) => {
    setConversations((prev) =>
      prev.map((conversation) =>
        conversation.id === id ? updater(conversation) : conversation,
      ),
    )
  }

  const createNewChat = () => {
    const fresh = createConversation()
    setConversations((prev) => [fresh, ...prev])
    setActiveId(fresh.id)
    setSidebarOpen(false)
  }

  const sendMessage = async () => {
    const trimmed = inputValue.trim()
    if (!trimmed || !activeConversation) return

    const history = chunkedHistory(activeConversation.messages)
    const assistantId = `assistant-${Date.now()}`

    updateConversation(activeConversation.id, (conversation) => {
      const nextMessages = [
        ...conversation.messages,
        { id: `user-${Date.now()}`, role: 'user', content: trimmed },
        { id: assistantId, role: 'assistant', content: '' },
      ]
      const title = conversation.title === 'New chat' ? trimmed.slice(0, 42) : conversation.title
      return { ...conversation, title, messages: nextMessages }
    })

    setInputValue('')
    setIsThinking(true)
    setStatusText('Thinking...')

    try {
      const response = await fetch(`${API_BASE}/api/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: trimmed, history }),
      })

      if (!response.body) {
        throw new Error('No response body')
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { value, done } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const parts = buffer.split('\n\n')
        buffer = parts.pop() || ''

        for (const part of parts) {
          if (!part.trim()) continue
          const { event, data } = parseSsePayload(part)
          let payload = {}
          try {
            payload = JSON.parse(data)
          } catch {
            payload = { text: data }
          }

          if (event === 'status') {
            setStatusText(payload.state || 'Thinking...')
          }

          if (event === 'tool') {
            setStatusText(`Using tool: ${payload.tool || 'tool'}`)
          }

          if (event === 'chunk') {
            updateConversation(activeConversation.id, (conversation) => {
              const updated = conversation.messages.map((message) =>
                message.id === assistantId
                  ? { ...message, content: `${message.content}${payload.text || ''}` }
                  : message,
              )
              return { ...conversation, messages: updated }
            })
          }

          if (event === 'done') {
            setIsThinking(false)
            setStatusText('')
          }
        }
      }
    } catch (error) {
      updateConversation(activeConversation.id, (conversation) => {
        const updated = conversation.messages.map((message) =>
          message.id === assistantId
            ? { ...message, content: `Error: ${error.message}` }
            : message,
        )
        return { ...conversation, messages: updated }
      })
      setIsThinking(false)
      setStatusText('')
    }
  }

  const handleKeyDown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      sendMessage()
    }
  }

  const toggleCollapse = () => {
    setSidebarCollapsed((prev) => !prev)
  }

  const linkify = (text) => {
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

  return (
    <div className="app-shell">
      <aside className={`sidebar ${sidebarOpen ? 'open' : ''} ${sidebarCollapsed ? 'collapsed' : ''}`}>
        <div className="sidebar-header">
          <div className="brand-row">
            <button className="icon-button ghost desktop-only" onClick={toggleCollapse} aria-label="Toggle sidebar">
              {sidebarCollapsed ? '»' : '«'}
            </button>
          </div>
          <div className="mobile-header-row">
            <button className="icon-button ghost mobile-only" onClick={() => setSidebarOpen(false)} aria-label="Close sidebar">
              ✕
            </button>
          </div>
          <button className="primary" onClick={createNewChat}>
            New chat
          </button>
        </div>
        <div className="conversation-list">
          {conversations.map((conversation) => (
            <div
              key={conversation.id}
              className={`conversation-item ${conversation.id === activeConversation?.id ? 'active' : ''}`}
              onClick={() => {
                setActiveId(conversation.id)
                setSidebarOpen(false)
              }}
            >
              <span className="conversation-title">{conversation.title}</span>
              <small>{new Date(conversation.createdAt).toLocaleDateString()}</small>
              <div className="conversation-actions" onClick={(e) => e.stopPropagation()}>
                <button
                  className="action-btn"
                  onClick={() => {
                    const newTitle = prompt('Edit chat name:', conversation.title)
                    if (newTitle && newTitle.trim()) {
                      updateConversation(conversation.id, (c) => ({ ...c, title: newTitle.trim() }))
                    }
                  }}
                  aria-label="Edit chat name"
                >
                  ✎
                </button>
                <button
                  className="action-btn delete"
                  onClick={() => {
                    if (confirm('Delete this chat?')) {
                      setConversations((prev) => prev.filter((c) => c.id !== conversation.id))
                    }
                  }}
                  aria-label="Delete chat"
                >
                  🗑
                </button>
              </div>
            </div>
          ))}
        </div>
      </aside>

      <main className="chat-panel">
        <header className="chat-header">
          <button className="icon-button ghost mobile-only" onClick={() => setSidebarOpen(true)} aria-label="Show history">
            ☰
          </button>
          <h2 className="chat-title">Agently</h2>
        </header>

        <section className="message-list">
          {activeConversation?.messages.map((message) => (
            <div key={message.id} className={`message-bubble ${message.role}`}>
              <span className="message-text">{linkify(message.content)}</span>
            </div>
          ))}
          {isThinking && (
            <div className="thinking">
              <div className="dot"></div>
              <span>{statusText || 'Thinking...'}</span>
            </div>
          )}
          <div ref={bottomRef} />
        </section>

        <footer className="composer">
          <textarea
            placeholder="Ask something current..."
            value={inputValue}
            onChange={(event) => setInputValue(event.target.value)}
            onKeyDown={handleKeyDown}
            rows={1}
          />
          <button className="primary" onClick={sendMessage} disabled={isThinking} aria-label="Send">
            <span className="send-label">Send</span>
            <span className="send-icon">➤</span>
          </button>
        </footer>
      </main>

      {sidebarOpen && <div className="sidebar-backdrop" onClick={() => setSidebarOpen(false)} />}
    </div>
  )
}

export default App
