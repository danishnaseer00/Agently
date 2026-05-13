export default function DocumentItem({ doc, isSelected, onToggle, onDelete }) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '6px',
        padding: '6px',
        borderRadius: '4px',
        background: isSelected ? '#f3f4f6' : 'transparent',
        cursor: 'pointer',
        marginBottom: '4px',
      }}
      onClick={() => onToggle(doc.id)}
    >
      <input
        type="checkbox"
        checked={isSelected}
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
          onDelete(doc.id)
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
  )
}
