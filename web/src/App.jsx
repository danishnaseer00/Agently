import { useRef, useState, useCallback, useEffect } from 'react'
import { get } from './api/client.js'
import { useConversations } from './hooks/useConversations.js'
import { useMessages } from './hooks/useMessages.js'
import { useDocuments } from './hooks/useDocuments.js'
import { useImageUpload } from './hooks/useImageUpload.js'
import { useFullscreenImage } from './hooks/useFullscreenImage.js'
import { useClickOutside } from './hooks/useClickOutside.js'
import { DEFAULT_TOOLS } from './utils/constants.js'
import Header from './components/layout/Header.jsx'
import Sidebar from './components/layout/Sidebar.jsx'
import MessageList from './components/chat/MessageList.jsx'
import FullscreenImage from './components/chat/FullscreenImage.jsx'
import ToolMenu from './components/documents/ToolMenu.jsx'
import ErrorBoundary from './components/common/ErrorBoundary.jsx'

function App() {
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
    statusText,
    sendMessage,
  } = useMessages({ activeId, refreshConversations })

  const {
    documents,
    selectedDocuments,
    useRag,
    setUseRag,
    uploading,
    uploadSuccess,
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

  const toolsRef = useRef(null)
  const imageInputRef = useRef(null)
  const fileInputRef = useRef(null)

  // Load available tools on mount
  useEffect(() => {
    get('/api/tools')
      .then((data) => setAvailableTools(data.tools || DEFAULT_TOOLS))
      .catch(() => {})
  }, [])

  // Click outside to close tools menu
  useClickOutside(toolsRef, () => setShowTools(false), [fileInputRef, imageInputRef])

  const handleSend = useCallback(() => {
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
  }, [inputValue, uploadedImage, imageAnalysis, selectedTools, selectedDocuments, useRag, sendMessage])

  const handleKeyDown = useCallback((event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      handleSend()
    }
  }, [handleSend])

  const handleNewChat = useCallback(() => {
    createNewChat()
    setMessages([])
    setSidebarOpen(false)
  }, [createNewChat, setMessages])

  const handleSelectConversation = useCallback((convId) => {
    setActiveId(convId)
    setMessages([])
    setSidebarOpen(false)
  }, [setActiveId, setMessages])

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

        {/* Hidden file inputs */}
        <input
          ref={imageInputRef}
          type="file"
          accept="image/*"
          onChange={handleImageUpload}
          style={{ display: 'none' }}
        />
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.txt,.docx"
          onChange={async (e) => {
            const file = e.target.files?.[0]
            if (file) {
              await uploadDocument(file)
              e.target.value = ''
            }
          }}
          style={{ display: 'none' }}
        />

        <footer className="composer" style={{ position: 'relative', zIndex: 60, flexDirection: 'column' }}>
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
                setShowTools={setShowTools}
                imageInputRef={imageInputRef}
                fileInputRef={fileInputRef}
                onImageUploadClick={() => {
                  imageInputRef.current?.click()
                  setShowTools(false)
                }}
                uploading={uploading}
                uploadSuccess={uploadSuccess}
                documents={documents}
                selectedDocuments={selectedDocuments}
                onToggleDocument={toggleDocument}
                onDeleteDocument={deleteDocument}
                onClearSelection={clearSelection}
                useRag={useRag}
                onToggleRag={setUseRag}
                onUploadFile={() => fileInputRef.current?.click()}
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
                placeholder="Ask something..."
                value={inputValue}
                onChange={(event) => setInputValue(event.target.value)}
                onKeyDown={handleKeyDown}
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

export default App
