import { useEffect } from 'react'
import { SignedIn, SignedOut, useAuth } from '@clerk/clerk-react'
import { useRef, useState, useCallback } from 'react'
import { get, setAuthToken, setTokenRefresh } from './api/client.js'
import { sendChatMessage, sendSlashCommand } from './api/chat.js'
import { useConversations } from './hooks/useConversations.js'
import { useMessages } from './hooks/useMessages.js'
import { useDocuments } from './hooks/useDocuments.js'
import { useImageUpload } from './hooks/useImageUpload.js'
import { useFullscreenImage } from './hooks/useFullscreenImage.js'
import { useClickOutside } from './hooks/useClickOutside.js'
import { DEFAULT_TOOLS } from './utils/constants.js'
import SlashCommandsDropdown, { parseSlashCommand } from './components/chat/SlashCommandsDropdown.jsx'
import Header from './components/layout/Header.jsx'
import Sidebar from './components/layout/Sidebar.jsx'
import MessageList from './components/chat/MessageList.jsx'
import FullscreenImage from './components/chat/FullscreenImage.jsx'
import ToolMenu from './components/documents/ToolMenu.jsx'
import ErrorBoundary from './components/common/ErrorBoundary.jsx'
import SignInPage from './components/auth/SignInPage.jsx'

// Visually hidden style for file inputs — keeps them in the DOM for mobile browsers
const hiddenInputStyle = {
  position: 'absolute',
  width: '1px',
  height: '1px',
  padding: 0,
  margin: '-1px',
  overflow: 'hidden',
  clip: 'rect(0, 0, 0, 0)',
  whiteSpace: 'nowrap',
  border: 0,
}

function AppContent() {
  // Hooks
  const {
    conversations,
    setConversations,
    activeId,
    setActiveId,
    refreshConversations,
    createNewChat,
    deleteChat,
    updateTitle,
  } = useConversations()

  const {
    messages,
    setMessages,
    isThinking,
    setIsThinking,
    statusText,
    setStatusText,
    sendMessage,
  } = useMessages({ activeId, refreshConversations })

  const {
    documents,
    selectedDocuments,
    useRag,
    setUseRag,
    uploading,
    uploadSuccess,
    uploadError,
    uploadDocument,
    deleteDocument,
    toggleDocument,
    clearSelection,
  } = useDocuments(activeId)

  const {
    uploadedImage,
    setUploadedImage,
    imageAnalysis,
    setImageAnalysis,
    analyzingImage,
    clearImage,
    handleImageUpload,
    handlePaste,
  } = useImageUpload()

  const { fullscreenImage, openFullscreen, closeFullscreen } = useFullscreenImage()

  // Local UI state
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [inputValue, setInputValue] = useState('')
  const [availableTools, setAvailableTools] = useState(DEFAULT_TOOLS)
  const [selectedTools, setSelectedTools] = useState([])
  const [showTools, setShowTools] = useState(false)
  const [showSlashCommands, setShowSlashCommands] = useState(false)

  const toolsRef = useRef(null)
  const imageInputRef = useRef(null)
  const fileInputRef = useRef(null)
  const textareaRef = useRef(null)

  // Load available tools on mount
  useEffect(() => {
    get('/api/tools')
      .then((data) => setAvailableTools(data.tools || DEFAULT_TOOLS))
      .catch(() => {})
  }, [])

  // Click outside to close tools menu
  useClickOutside(toolsRef, () => setShowTools(false), [fileInputRef, imageInputRef])

  const handleSlashCommand = useCallback(async (cmd) => {
    if (!activeId) return

    const trimmed = inputValue.slice(cmd.id.length + 1).trim() // text after the command name
    const topic = trimmed || ''

    const userMsg = { id: `user-${Date.now()}`, role: 'user', content: `/${cmd.id} ${topic}` }
    setMessages((prev) => [...prev, userMsg])

    setInputValue('')
    setIsThinking(true)
    setStatusText(cmd.id === 'summarize' ? 'Summarizing conversation...' : 'Researching...')
    setShowTools(false)

    try {
      const data = await sendSlashCommand(cmd.id, activeId, topic)

      const assistantMsg = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: data.error ? data.error : (data.answer || 'No response'),
      }
      setMessages((prev) => [...prev, assistantMsg])
    } catch (error) {
      const assistantMsg = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: `${error.message}`,
      }
      setMessages((prev) => [...prev, assistantMsg])
    }

    setIsThinking(false)
    setStatusText('')
    refreshConversations()
  }, [activeId, inputValue, messages, refreshConversations])

  const handleSend = useCallback(() => {
    // Check if this is a slash command
    const parsed = parseSlashCommand(inputValue)
    if (parsed && parsed.matched) {
      handleSlashCommand(parsed.matched)
      return
    }

    sendMessage({
      inputValue,
      uploadedImage,
      imageAnalysis,
      selectedTools,
      selectedDocuments,
      useRag,
      setInputValue,
      setUploadedImage,
      setImageAnalysis,
      setShowTools,
    })
  }, [inputValue, uploadedImage, imageAnalysis, selectedTools, selectedDocuments, useRag, sendMessage, handleSlashCommand])

  const handleKeyDown = useCallback((event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      handleSend()
    }
  }, [handleSend])

  const handleNewChat = useCallback(() => {
    createNewChat()
    setSidebarOpen(false)
  }, [createNewChat])

  const handleSelectConversation = useCallback((convId) => {
    setActiveId(convId)
    setSidebarOpen(false)
  }, [setActiveId])

  return (
    <ErrorBoundary>
    <div className="app-shell">
      <FullscreenImage src={fullscreenImage} onClose={closeFullscreen} />

      <Sidebar
        conversations={conversations}
        activeId={activeId}
        onSelectConv={handleSelectConversation}
        onNewChat={handleNewChat}
        onEditTitle={updateTitle}
        onDeleteChat={deleteChat}
        sidebarOpen={sidebarOpen}
        sidebarCollapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed((prev) => !prev)}
        onClose={() => setSidebarOpen(false)}
      />

      <main className="chat-panel">
        <Header onToggleSidebar={() => setSidebarOpen(true)} />

        <MessageList
          messages={messages}
          isThinking={isThinking}
          statusText={statusText}
          onImageClick={openFullscreen}
        />

        {/* Visually hidden file inputs — uses clip pattern instead of display:none for mobile browser compatibility */}
        <input
          ref={imageInputRef}
          id="img-upload-input"
          type="file"
          accept="image/*"
          onChange={handleImageUpload}
          style={hiddenInputStyle}
          tabIndex={-1}
        />
        <input
          ref={fileInputRef}
          id="doc-upload-input"
          type="file"
          accept="application/pdf,text/plain,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
          onChange={async (e) => {
            const file = e.target.files?.[0]
            if (file) {
              await uploadDocument(file)
              e.target.value = ''
            }
          }}
          style={hiddenInputStyle}
          tabIndex={-1}
        />

        <footer className="composer" style={{ position: 'relative', zIndex: 100, flexDirection: 'column' }}>
          {/* Slash commands dropdown - positioned above the composer */}
          <div style={{ position: 'absolute', bottom: '100%', left: 0, right: 0, height: 0 }}>
            {showSlashCommands && (
              <SlashCommandsDropdown
                inputValue={inputValue}
                onSelect={(cmd) => {
                  setInputValue('/' + cmd.id + ' ')
                  setShowSlashCommands(false)
                  setTimeout(() => textareaRef.current?.focus(), 0)
                }}
                onClose={() => setShowSlashCommands(false)}
              />
            )}
          </div>
          <div style={{ display: 'flex', alignItems: 'flex-end', gap: '10px', width: '100%' }}>
            {/* Tools + button */}
            <div style={{ position: 'relative' }} ref={toolsRef}>
              <button
                className={`tool-btn ${showTools ? 'active' : ''} ${selectedTools.length > 0 ? 'has-selection' : ''}`}
                onClick={() => setShowTools(!showTools)}
                aria-label="Add attachment"
                style={{ flexShrink: 0 }}
              >
                <span className="tool-btn-icon">+</span>
                {selectedTools.length > 0 && !showTools && (
                  <span className="tool-badge">{selectedTools.length}</span>
                )}
              </button>

              <ToolMenu
                showTools={showTools}
                uploading={uploading}
                uploadSuccess={uploadSuccess}
                uploadError={uploadError}
                documents={documents}
                selectedDocuments={selectedDocuments}
                onToggleDocument={toggleDocument}
                onDeleteDocument={deleteDocument}
                onClearSelection={clearSelection}
                useRag={useRag}
                onToggleRag={setUseRag}
                availableTools={availableTools}
                selectedTools={selectedTools}
                onToggleTool={(toolName) => {
                  setSelectedTools((prev) =>
                    prev.includes(toolName)
                      ? prev.filter((t) => t !== toolName)
                      : [...prev, toolName],
                  )
                }}
                onClearTools={() => setSelectedTools([])}
                toolsRef={toolsRef}
              />
            </div>

            {/* Input area */}
            <div style={{
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              borderRadius: '14px',
              border: '1px solid #e5e7eb',
              background: '#fff',
              overflow: 'hidden',
            }}>
              {(uploadedImage || analyzingImage) && (
                <div style={{ padding: '8px 12px', borderBottom: '1px solid #f3f4f6', background: '#fafafa' }}>
                  {analyzingImage ? (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontSize: '0.8rem', animation: 'spin 1s linear infinite' }}>⟳</span>
                      <span style={{ fontSize: '0.85rem', color: '#6b7280' }}>Analyzing image...</span>
                    </div>
                  ) : uploadedImage && (
                    <div style={{ position: 'relative', display: 'inline-block' }}>
                      <img
                        src={uploadedImage}
                        alt="Attached"
                        style={{ width: '48px', height: '48px', borderRadius: '6px', border: '1px solid #e5e7eb', objectFit: 'cover' }}
                      />
                      <button
                        onClick={clearImage}
                        style={{
                          position: 'absolute',
                          top: '-6px',
                          right: '-6px',
                          background: '#111827',
                          color: '#fff',
                          border: 'none',
                          borderRadius: '50%',
                          width: '18px',
                          height: '18px',
                          cursor: 'pointer',
                          fontSize: '0.7rem',
                          padding: 0,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                        }}
                        title="Remove image"
                      >
                        ✕
                      </button>
                    </div>
                  )}
                </div>
              )}

              <textarea
                ref={textareaRef}
                placeholder="Ask something..."
                value={inputValue}
                onChange={(event) => {
                  const val = event.target.value
                  setInputValue(val)
                  // Show slash commands when typing /
                  if (val.startsWith('/')) {
                    setShowSlashCommands(true)
                  } else {
                    setShowSlashCommands(false)
                  }
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Escape' && showSlashCommands) {
                    setShowSlashCommands(false)
                    e.preventDefault()
                    return
                  }
                  handleKeyDown(e)
                }}
                onPaste={handlePaste}
                rows={1}
                style={{
                  width: '100%',
                  minHeight: '44px',
                  resize: 'none',
                  border: 'none',
                  padding: '12px 14px',
                  fontFamily: 'var(--font-ui)',
                  fontSize: '1rem',
                  color: 'var(--text)',
                  outline: 'none',
                  background: 'transparent',
                }}
              />
            </div>

            <button
              className="primary"
              onClick={handleSend}
              disabled={isThinking}
              aria-label="Send"
              style={{
                background: '#111827',
                color: '#ffffff',
                padding: '0 18px',
                height: '44px',
                borderRadius: '8px',
                fontWeight: 600,
                border: 'none',
                cursor: isThinking ? 'not-allowed' : 'pointer',
                opacity: isThinking ? 0.6 : 1,
                flexShrink: 0,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '1rem',
              }}
            >
              Send
            </button>
          </div>
        </footer>
      </main>

      {sidebarOpen && <div className="sidebar-backdrop" onClick={() => setSidebarOpen(false)} />}
    </div>
    </ErrorBoundary>
  )
}

function App() {
  const { isLoaded, isSignedIn, getToken } = useAuth()
  const [tokenReady, setTokenReady] = useState(false)

  useEffect(() => {
    if (!isLoaded) return
    setTokenReady(false)

    // Not signed in → no token needed, let SignedOut render
    if (!isSignedIn) {
      setTokenReady(true)
      return
    }

    let cancelled = false

    const sync = async () => {
      try {
        const token = await getToken()
        if (!cancelled && token) {
          setAuthToken(token)
          setTokenReady(true)
        }
      } catch {
        // Token sync failed — Clerk will still try
      }
    }

    sync()

    // Allow client.js to auto-refresh the token when API calls get 401
    setTokenRefresh(async () => {
      const freshToken = await getToken()
      return freshToken || null
    })

    // Re-sync every 30 seconds to keep the token fresh
    const interval = setInterval(sync, 30 * 1000)

    return () => {
      cancelled = true
      clearInterval(interval)
    }
  }, [isLoaded, isSignedIn, getToken])

  if (!isLoaded) {
    return (
      <div className="loading-screen">
        <span className="loading-spinner" />
      </div>
    )
  }

  if (!tokenReady) {
    return (
      <div className="loading-screen">
        <span className="loading-spinner" />
        <p style={{ color: '#6b7280', marginTop: 16, fontSize: '0.9rem' }}>
          Signing in...
        </p>
      </div>
    )
  }

  return (
    <>
      <SignedIn>
        <AppContent />
      </SignedIn>
      <SignedOut>
        <SignInPage />
      </SignedOut>
    </>
  )
}

export default App
