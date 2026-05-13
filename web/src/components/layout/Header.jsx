import { useClerk } from '@clerk/clerk-react'

export default function Header({ onToggleSidebar }) {
  const { signOut } = useClerk()

  return (
    <header className="chat-header">
      <button className="icon-button ghost mobile-only" onClick={onToggleSidebar} aria-label="Show history">
        ☰
      </button>
      <h2 className="chat-title">Agently</h2>
      <div className="header-spacer" />
      <button
        className="sign-out-button"
        onClick={() => signOut()}
        title="Sign out"
        aria-label="Sign out"
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
          <polyline points="16 17 21 12 16 7" />
          <line x1="21" y1="12" x2="9" y2="12" />
        </svg>
      </button>
    </header>
  )
}
