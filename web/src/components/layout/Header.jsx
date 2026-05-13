export default function Header({ onToggleSidebar }) {
  return (
    <header className="chat-header">
      <button className="icon-button ghost mobile-only" onClick={onToggleSidebar} aria-label="Show history">
        ☰
      </button>
      <h2 className="chat-title">Agently</h2>
    </header>
  )
}
