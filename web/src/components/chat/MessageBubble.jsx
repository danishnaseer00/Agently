import { formatMarkdown, linkify } from '../../utils/markdown.jsx'

export default function MessageBubble({ message, onImageClick }) {
  return (
    <div key={message.id} className={`message-bubble ${message.role}`}>
      {message.image && (
        <div style={{ marginBottom: '8px' }}>
          <img
            src={message.image}
            alt="Uploaded"
            onClick={() => onImageClick?.(message.image)}
            style={{
              maxWidth: '120px',
              maxHeight: '100px',
              borderRadius: '6px',
              border: '1px solid #e5e7eb',
              objectFit: 'cover',
              cursor: 'pointer',
            }}
          />
        </div>
      )}
      <div className="message-text">
        {message.role === 'assistant' ? formatMarkdown(message.content) : linkify(message.content)}
      </div>
    </div>
  )
}
