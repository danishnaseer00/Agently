export default function ConversationItem({ conversation, isActive, onSelect, onEditTitle, onDelete }) {
  return (
    <div
      className={`conversation-item ${isActive ? 'active' : ''}`}
      onClick={onSelect}
    >
      <span className="conversation-title">{conversation.title}</span>
      <small>{new Date(conversation.createdAt).toLocaleDateString()}</small>
      <div className="conversation-actions" onClick={(e) => e.stopPropagation()}>
        <button
          className="action-btn"
          onClick={async () => {
            const newTitle = prompt('Edit chat name:', conversation.title)
            if (newTitle && newTitle.trim()) {
              await onEditTitle(conversation.id, newTitle.trim())
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
              await onDelete(conversation.id)
            }
          }}
          aria-label="Delete chat"
        >
          🗑
        </button>
      </div>
    </div>
  )
}
