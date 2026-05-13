import ConversationItem from './ConversationItem.jsx'

export default function Sidebar({
  conversations,
  activeId,
  onSelectConv,
  onNewChat,
  onEditTitle,
  onDeleteChat,
  sidebarOpen,
  sidebarCollapsed,
  onToggleCollapse,
  onClose,
}) {
  return (
    <aside className={`sidebar ${sidebarOpen ? 'open' : ''} ${sidebarCollapsed ? 'collapsed' : ''}`}>
      <div className="sidebar-header">
        <div className="brand-row">
          <button className="icon-button ghost desktop-only" onClick={onToggleCollapse} aria-label="Toggle sidebar">
            {sidebarCollapsed ? '»' : '«'}
          </button>
        </div>
        <div className="mobile-header-row">
          <button className="primary new-chat-btn" onClick={onNewChat}>
            New chat
          </button>
          <button className="icon-button ghost mobile-only" onClick={onClose} aria-label="Close sidebar">
            ✕
          </button>
        </div>
        <button className="primary" onClick={onNewChat}>
          New chat
        </button>
      </div>
      <div className="conversation-list">
        {conversations.map((conversation) => (
          <ConversationItem
            key={conversation.id}
            conversation={conversation}
            isActive={conversation.id === activeId}
            onSelect={() => {
              onSelectConv(conversation.id)
              onClose()
            }}
            onEditTitle={onEditTitle}
            onDelete={onDeleteChat}
          />
        ))}
      </div>
    </aside>
  )
}
