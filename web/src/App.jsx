import { useEffect, useMemo, useRef, useState } from 'react'

const API_BASE = import.meta.env.VITE_API_URL || ''

const createConversation = () => ({
  id: `conv-${Date.now()}`,
  title: 'New chat',
  createdAt: Date.now(),
  messages: [],
})

const loadConversationsFromApi = async () => {
  try {
    const res = await fetch(`${API_BASE}/api/conversations`)
    if (!res.ok) return [createConversation()]
    const data = await res.json()
    if (!Array.isArray(data) || data.length === 0) return [createConversation()]
    return data.map((c) => ({
      id: c.id,
      title: c.title,
      createdAt: new Date(c.created_at).getTime(),
      messages: [],
    }))
  } catch {
    return [createConversation()]
  }
}

const loadMessagesFromApi = async (convId) => {
  try {
    const res = await fetch(`${API_BASE}/api/conversations/${convId}/messages`)
    if (!res.ok) return []
    const data = await res.json()
    return data.map((m) => ({
      id: m.id,
      role: m.role,
      content: m.content,
    }))
  } catch {
    return []
  }
}

const deleteConversationApi = async (convId) => {
  try {
    await fetch(`${API_BASE}/api/conversations/${convId}`, { method: 'DELETE' })
  } catch {}
}

const updateTitleApi = async (convId, title) => {
  try {
    await fetch(`${API_BASE}/api/conversations/${convId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title }),
    })
  } catch {}
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

const loadDocumentsFromApi = async (convId) => {
  try {
    const res = await fetch(`${API_BASE}/api/documents?conversation_id=${convId}`)
    if (!res.ok) return []
    return await res.json()
  } catch {
    return []
  }
}

const uploadDocumentToApi = async (file, convId) => {
  try {
    const formData = new FormData()
    formData.append('file', file)
    const res = await fetch(`${API_BASE}/api/documents/upload?conversation_id=${convId}`, {
      method: 'POST',
      body: formData,
    })
    if (!res.ok) return null
    return await res.json()
  } catch {
    return null
  }
}

const deleteDocumentFromApi = async (docId, convId) => {
  try {
    await fetch(`${API_BASE}/api/documents/${docId}?conversation_id=${convId}`, { method: 'DELETE' })
  } catch {}
}

function App() {
  const [conversations, setConversations] = useState([])
  const [activeId, setActiveId] = useState(null)
  const [messages, setMessages] = useState([])
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [isThinking, setIsThinking] = useState(false)
  const [statusText, setStatusText] = useState('')
  const [inputValue, setInputValue] = useState('')
  const [loaded, setLoaded] = useState(false)
  const [availableTools, setAvailableTools] = useState([])
  const [selectedTools, setSelectedTools] = useState([])
  const [showTools, setShowTools] = useState(false)
  const [documents, setDocuments] = useState([])
  const [selectedDocuments, setSelectedDocuments] = useState([])
  const [useRag, setUseRag] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadSuccess, setUploadSuccess] = useState('')
  const bottomRef = useRef(null)
  const toolsRef = useRef(null)
  const fileInputRef = useRef(null)

  const activeConversation = useMemo(
    () => conversations.find((item) => item.id === activeId) || conversations[0],
    [conversations, activeId],
  )

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (toolsRef.current && !toolsRef.current.contains(event.target)) {
        setShowTools(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  useEffect(() => {
    if (uploadSuccess) {
      const timer = setTimeout(() => setUploadSuccess(''), 3000)
      return () => clearTimeout(timer)
    }
  }, [uploadSuccess])

  useEffect(() => {
    if (!loaded) {
      loadConversationsFromApi().then((data) => {
        setConversations(data)
        setLoaded(true)
      })
    }
    fetch(`${API_BASE}/api/tools`)
      .then((r) => r.json())
      .then((data) => setAvailableTools(data.tools || []))
      .catch(() => {})
  }, [])

  useEffect(() => {
    if (activeId && loaded) {
      loadMessagesFromApi(activeId).then(setMessages)
      loadDocumentsFromApi(activeId).then(setDocuments)
      setSelectedDocuments([])
    }
  }, [activeId, loaded])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages, isThinking, statusText])

  const createNewChat = () => {
    const fresh = createConversation()
    setConversations((prev) => [fresh, ...prev])
    setActiveId(fresh.id)
    setMessages([])
    setSidebarOpen(false)
  }

  const sendMessage = async () => {
    const trimmed = inputValue.trim()
    if (!trimmed || !activeId) return

    const history = chunkedHistory(messages)
    const currentConv = conversations.find((c) => c.id === activeId)
    const title = currentConv?.title === 'New chat' ? trimmed.slice(0, 42) : currentConv?.title

    const userMsg = { id: `user-${Date.now()}`, role: 'user', content: trimmed }
    setMessages((prev) => [...prev, userMsg, { id: `assistant-${Date.now()}`, role: 'assistant', content: '' }])

    setInputValue('')
    setIsThinking(true)
    setStatusText('Thinking...')
    setShowTools(false)

    try {
      const response = await fetch(`${API_BASE}/api/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: trimmed,
          history,
          conversation_id: activeId,
          title,
          tool_names: selectedTools.length > 0 ? selectedTools : null,
          document_ids: selectedDocuments.length > 0 ? selectedDocuments : null,
          use_rag: useRag && selectedDocuments.length > 0,
        }),
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
            setMessages((prev) => {
              const lastIndex = prev.length - 1
              return prev.map((m, i) =>
                i === lastIndex && m.role === 'assistant'
                  ? { ...m, content: `${m.content}${payload.text || ''}` }
                  : m,
              )
            })
          }

          if (event === 'done') {
            setIsThinking(false)
            setStatusText('')
            loadConversationsFromApi().then(setConversations)
          }
        }
      }
    } catch (error) {
      setMessages((prev) =>
        prev.map((m) =>
          m.role === 'assistant' && m.content === ''
            ? { ...m, content: `Error: ${error.message}` }
            : m,
        ),
      )
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

  const formatMarkdown = (text) => {
    // Remove <br> and <br/> tags
    text = text.replace(/<br\s*\/?>/gi, '\n')

    // Split into blocks (paragraphs, lists, etc)
    const blocks = text.split(/\n{2,}/).map(block => block.trim()).filter(b => b)

    const parseInlineMarkdown = (str) => {
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
          // Bold italic ***text***
          parts.push(<strong key={`${start}-bi`}><em>{match[1]}</em></strong>)
        } else if (match[2]) {
          // Bold **text**
          parts.push(<strong key={`${start}-b`}>{match[2]}</strong>)
        } else if (match[3]) {
          // Italic *text*
          parts.push(<em key={`${start}-i`}>{match[3]}</em>)
        } else if (match[4]) {
          // Italic _text_
          parts.push(<em key={`${start}-i2`}>{match[4]}</em>)
        } else {
          // Link
          const url = match[0]
          const href = url.startsWith('http') ? url : `https://${url}`
          parts.push(
            <a key={`${start}-link`} href={href} target="_blank" rel="noreferrer">
              {url}
            </a>
          )
        }
        lastIndex = start + match[0].length
      }

      if (lastIndex < str.length) {
        parts.push(str.slice(lastIndex))
      }

      return parts.length === 0 ? str : parts
    }

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
            <button className="primary new-chat-btn" onClick={createNewChat}>
              New chat
            </button>
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
              className={`conversation-item ${conversation.id === activeId ? 'active' : ''}`}
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
                  onClick={async () => {
                    const newTitle = prompt('Edit chat name:', conversation.title)
                    if (newTitle && newTitle.trim()) {
                      await updateTitleApi(conversation.id, newTitle.trim())
                      loadConversationsFromApi().then(setConversations)
                    }
                  }}
                  aria-label="Edit chat name"
                >
                  ✎
                </button>
                <button
                  className="action-btn delete"
                  onClick={async () => {
                    if (confirm('Delete this chat?')) {
                      await deleteConversationApi(conversation.id)
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
          {messages.map((message) => (
            <div key={message.id} className={`message-bubble ${message.role}`}>
              <div className="message-text">
                {message.role === 'assistant' ? formatMarkdown(message.content) : linkify(message.content)}
              </div>
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

        <footer className="composer" style={{ position: 'relative', zIndex: 60 }}>
          <div className="tools-container" ref={toolsRef}>
            <button
              className={`tool-btn ${showTools ? 'active' : ''} ${selectedTools.length > 0 ? 'has-selection' : ''}`}
              onClick={() => setShowTools(!showTools)}
              aria-label="Select tools"
            >
              <span className="tool-btn-icon">+</span>
              {selectedTools.length > 0 && !showTools && (
                <span className="tool-badge">{selectedTools.length}</span>
              )}
            </button>

            {showTools && (
              <div className="tools-box">
                {/* Documents Section */}
                <div style={{ paddingBottom: '12px', borderBottom: '1px solid #e5e7eb' }}>
                  <div className="tools-box-header" style={{ paddingBottom: '8px' }}>
                    <div className="header-left">
                      <h3 style={{ margin: 0, fontSize: '0.9rem' }}>📄 Documents</h3>
                      {selectedDocuments.length > 0 && (
                        <span className="selected-count" style={{ fontSize: '0.75rem' }}>
                          {selectedDocuments.length}
                        </span>
                      )}
                    </div>
                  </div>

                  <div style={{ marginBottom: '8px', marginTop: '8px' }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem', cursor: 'pointer' }}>
                      <input
                        type="checkbox"
                        checked={useRag}
                        onChange={(e) => setUseRag(e.target.checked)}
                        disabled={selectedDocuments.length === 0}
                      />
                      Use RAG
                    </label>
                  </div>

                  <div style={{ marginBottom: '8px' }}>
                    <button
                      onClick={() => fileInputRef.current?.click()}
                      disabled={uploading}
                      style={{
                        width: '100%',
                        padding: '6px 10px',
                        background: '#111827',
                        color: '#fff',
                        border: 'none',
                        borderRadius: '6px',
                        cursor: uploading ? 'not-allowed' : 'pointer',
                        opacity: uploading ? 0.6 : 1,
                        fontSize: '0.8rem',
                        fontWeight: 500,
                      }}
                    >
                      {uploading ? 'Uploading...' : '+ Upload File'}
                    </button>
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".pdf,.txt,.docx"
                      onChange={async (e) => {
                        const file = e.target.files?.[0]
                        if (file && activeId) {
                          setUploading(true)
                          const result = await uploadDocumentToApi(file, activeId)
                          setUploading(false)
                          if (result) {
                            setUploadSuccess(`Uploaded: ${file.name}`)
                            await loadDocumentsFromApi(activeId).then((docs) => {
                              setDocuments(docs)
                              // Auto-select the newly uploaded document
                              if (result.document_id) {
                                setSelectedDocuments((prev) => [...prev, result.document_id])
                              }
                            })
                            fileInputRef.current.value = ''
                          }
                        }
                      }}
                      style={{ display: 'none' }}
                    />
                  </div>

                  {uploadSuccess && (
                    <div style={{
                      padding: '6px 8px',
                      background: '#dcfce7',
                      color: '#166534',
                      borderRadius: '4px',
                      fontSize: '0.75rem',
                      marginBottom: '8px',
                    }}>
                      ✓ {uploadSuccess}
                    </div>
                  )}

                  <div style={{ maxHeight: '200px', overflowY: 'auto', fontSize: '0.85rem' }}>
                    {documents.length === 0 ? (
                      <div style={{ padding: '8px', textAlign: 'center', color: '#6b7280' }}>
                        No documents
                      </div>
                    ) : (
                      documents.map((doc) => (
                        <div
                          key={doc.id}
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '6px',
                            padding: '6px',
                            borderRadius: '4px',
                            background: selectedDocuments.includes(doc.id) ? '#f3f4f6' : 'transparent',
                            cursor: 'pointer',
                            marginBottom: '4px',
                          }}
                          onClick={() => {
                            if (selectedDocuments.includes(doc.id)) {
                              setSelectedDocuments((prev) => prev.filter((id) => id !== doc.id))
                            } else {
                              setSelectedDocuments((prev) => [...prev, doc.id])
                            }
                          }}
                        >
                          <input
                            type="checkbox"
                            checked={selectedDocuments.includes(doc.id)}
                            onChange={() => {}}
                            style={{ cursor: 'pointer', width: '16px', height: '16px' }}
                          />
                          <div style={{ flex: 1, minWidth: 0 }}>
                            <div style={{ fontSize: '0.8rem', fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                              {doc.filename}
                            </div>
                            <div style={{ fontSize: '0.7rem', color: '#6b7280' }}>
                              {(doc.size_bytes / 1024).toFixed(1)}KB
                            </div>
                          </div>
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              deleteDocumentFromApi(doc.id, activeId).then(() => {
                                setDocuments((prev) => prev.filter((d) => d.id !== doc.id))
                                setSelectedDocuments((prev) => prev.filter((id) => id !== doc.id))
                              })
                            }}
                            style={{
                              background: 'transparent',
                              border: 'none',
                              cursor: 'pointer',
                              fontSize: '0.8rem',
                              padding: '2px',
                            }}
                            title="Delete document"
                          >
                            🗑
                          </button>
                        </div>
                      ))
                    )}
                  </div>

                  {selectedDocuments.length > 0 && (
                    <button
                      className="clear-btn"
                      onClick={() => setSelectedDocuments([])}
                      style={{ width: '100%', marginTop: '8px', fontSize: '0.75rem' }}
                    >
                      Deselect All
                    </button>
                  )}
                </div>

                {/* Tools Section */}
                <div>
                  <div className="tools-box-header" style={{ paddingBottom: '8px' }}>
                    <div className="header-left">
                      <h3 style={{ margin: 0, fontSize: '0.9rem' }}>Available Tools</h3>
                      {selectedTools.length > 0 && (
                        <span className="selected-count">{selectedTools.length}</span>
                      )}
                    </div>
                  </div>
                  <div className="tools-list">
                    {availableTools.map((tool) => (
                      <div
                        key={tool.name}
                        className={`tool-item ${selectedTools.includes(tool.name) ? 'selected' : ''}`}
                        onClick={() => {
                          if (selectedTools.includes(tool.name)) {
                            setSelectedTools((prev) => prev.filter((t) => t !== tool.name))
                          } else {
                            setSelectedTools((prev) => [...prev, tool.name])
                          }
                        }}
                      >
                        <div className="tool-item-name">{tool.name}</div>
                        <div className="tool-item-desc">{tool.description}</div>
                      </div>
                    ))}
                  </div>
                  {selectedTools.length > 0 && (
                    <button className="clear-btn" onClick={() => setSelectedTools([])} style={{ width: '100%', marginTop: '8px' }}>
                      Clear
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>
          <textarea
            placeholder="Ask something current..."
            value={inputValue}
            onChange={(event) => setInputValue(event.target.value)}
            onKeyDown={handleKeyDown}
            rows={1}
          />
          <button className="primary" onClick={sendMessage} disabled={isThinking} aria-label="Send" style={{ position: 'relative', zIndex: 61 }}>
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
