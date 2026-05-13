export default function FullscreenImage({ src, onClose }) {
  if (!src) return null

  return (
    <div
      onClick={onClose}
      style={{
        position: 'fixed',
        top: 0, left: 0, right: 0, bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.85)',
        zIndex: 9999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        cursor: 'zoom-out',
        padding: '20px',
      }}
    >
      <button
        onClick={onClose}
        style={{
          position: 'absolute',
          top: '20px',
          right: '20px',
          background: 'transparent',
          color: 'white',
          border: 'none',
          fontSize: '2rem',
          cursor: 'pointer',
          zIndex: 10000,
        }}
      >
        ✕
      </button>
      <img
        src={src}
        alt="Fullscreen"
        style={{
          maxHeight: '90vh',
          maxWidth: '90vw',
          objectFit: 'contain',
          borderRadius: '8px',
          cursor: 'default',
        }}
        onClick={(e) => e.stopPropagation()}
      />
    </div>
  )
}
