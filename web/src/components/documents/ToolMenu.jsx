import { useState } from 'react'
import DocumentItem from './DocumentItem.jsx'

export default function ToolMenu({
  showTools,
  uploading,
  uploadSuccess,
  uploadError,
  documents,
  selectedDocuments,
  onToggleDocument,
  onDeleteDocument,
  onClearSelection,
  useRag,
  onToggleRag,
  availableTools,
  selectedTools,
  onToggleTool,
  onClearTools,
  toolsRef,
}) {
  const [toolsExpanded, setToolsExpanded] = useState(false)

  if (!showTools) return null

  return (
    <div className="tools-box" style={{ bottom: 'calc(100% + 12px)', left: 0, width: '280px' }}>
      {/* Image Upload section */}
      <div style={{ paddingBottom: '12px', borderBottom: '1px solid #e5e7eb', marginBottom: '12px' }}>
        <div className="tools-box-header" style={{ paddingBottom: '8px', borderBottom: 'none' }}>
          <h3 style={{ margin: 0, fontSize: '0.9rem' }}> Image</h3>
        </div>
        <label
          htmlFor="img-upload-input"
          role="button"
          style={{
            width: '100%',
            padding: '8px 10px',
            background: '#f3f4f6',
            color: '#111827',
            border: '1px solid #e5e7eb',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '0.85rem',
            fontWeight: 500,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            boxSizing: 'border-box',
          }}
        >
          <span style={{ fontSize: '1.2rem' }}></span> Upload Image
        </label>
      </div>

      {/* Documents Section */}
      <div style={{ paddingBottom: '12px', borderBottom: '1px solid #e5e7eb' }}>
        <div className="tools-box-header" style={{ paddingBottom: '8px' }}>
          <div className="header-left">
            <h3 style={{ margin: 0, fontSize: '0.9rem' }}>Documents</h3>
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
              onChange={(e) => onToggleRag(e.target.checked)}
              disabled={selectedDocuments.length === 0}
            />
            Use RAG
          </label>
        </div>

        <div style={{ marginBottom: '8px' }}>
          <label
            htmlFor={uploading ? undefined : 'doc-upload-input'}
            role="button"
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
              display: 'block',
              textAlign: 'center',
              boxSizing: 'border-box',
            }}
          >
            {uploading ? 'Uploading...' : '+ Upload File'}
          </label>
        </div>

        {uploadError && (
          <div style={{
            padding: '6px 8px',
            background: '#fee2e2',
            color: '#991b1b',
            borderRadius: '4px',
            fontSize: '0.75rem',
            marginBottom: '8px',
            wordBreak: 'break-word',
          }}>
            ✗ {uploadError}
          </div>
        )}

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

        <div style={{ maxHeight: '150px', overflowY: 'auto', fontSize: '0.85rem' }}>
          {documents.length === 0 ? (
            <div style={{ padding: '8px', textAlign: 'center', color: '#6b7280' }}>
              No documents
            </div>
          ) : (
            documents.map((doc) => (
              <DocumentItem
                key={doc.id}
                doc={doc}
                isSelected={selectedDocuments.includes(doc.id)}
                onToggle={onToggleDocument}
                onDelete={onDeleteDocument}
              />
            ))
          )}
        </div>

        {selectedDocuments.length > 0 && (
          <button
            className="clear-btn"
            onClick={onClearSelection}
            style={{ width: '100%', marginTop: '8px', fontSize: '0.75rem' }}
          >
            Deselect All
          </button>
        )}
      </div>

      {/* Tools Section */}
      <div>
        <div
          className="tools-box-header"
          style={{
            paddingBottom: '8px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
          onClick={() => setToolsExpanded((prev) => !prev)}
        >
          <div className="header-left" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <h3 style={{ margin: 0, fontSize: '0.9rem' }}>Tools</h3>
            {selectedTools.length > 0 && (
              <span className="selected-count">{selectedTools.length}</span>
            )}
          </div>
          <span style={{ fontSize: '0.75rem', opacity: 0.6 }}>
            {toolsExpanded ? '▲' : '▼'}
          </span>
        </div>

        {toolsExpanded && (
          <>
            <div className="tools-list">
              {availableTools.map((tool) => (
                <div
                  key={tool.name}
                  className={`tool-item ${selectedTools.includes(tool.name) ? 'selected' : ''}`}
                  onClick={() => onToggleTool(tool.name)}
                >
                  <div className="tool-item-name">{tool.name}</div>
                  <div className="tool-item-desc">{tool.description}</div>
                </div>
              ))}
            </div>
            {selectedTools.length > 0 && (
              <button className="clear-btn" onClick={onClearTools} style={{ width: '100%', marginTop: '8px' }}>
                Clear
              </button>
            )}
          </>
        )}
      </div>
    </div>
  )
}
