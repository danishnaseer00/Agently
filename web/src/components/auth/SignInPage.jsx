import { SignIn } from '@clerk/clerk-react'

export default function SignInPage() {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #0f1724 0%, #1a2332 50%, #0f1724 100%)',
      padding: '20px',
    }}>
      <div style={{
        marginBottom: '32px',
        textAlign: 'center',
      }}>
        <h1 style={{
          fontSize: '1.8rem',
          fontWeight: 700,
          color: '#ffffff',
          margin: '0 0 8px 0',
          letterSpacing: '-0.02em',
        }}>
          ReAct Agent
        </h1>
        <p style={{
          fontSize: '0.95rem',
          color: '#94a3b8',
          margin: 0,
        }}>
          Sign in to continue
        </p>
      </div>

      <div style={{
        width: '100%',
        maxWidth: '420px',
      }}>
        <SignIn
          routing="hash"
          signUpUrl="#"
          appearance={{
            elements: {
              rootBox: {
                width: '100%',
              },
              card: {
                background: '#1e293b',
                borderRadius: '12px',
                boxShadow: '0 4px 24px rgba(0,0,0,0.3)',
                border: '1px solid #334155',
              },
              headerTitle: {
                color: '#f1f5f9',
                fontSize: '1.25rem',
              },
              headerSubtitle: {
                color: '#94a3b8',
              },
              formButtonPrimary: {
                background: '#3b82f6',
                borderRadius: '8px',
                fontSize: '0.9rem',
                fontWeight: 600,
              },
              formFieldInput: {
                background: '#0f1724',
                border: '1px solid #334155',
                borderRadius: '8px',
                color: '#f1f5f9',
              },
              formFieldLabel: {
                color: '#94a3b8',
              },
              dividerLine: {
                background: '#334155',
              },
              dividerText: {
                color: '#64748b',
              },
              socialButtonsBlockButton: {
                background: '#0f1724',
                border: '1px solid #334155',
                borderRadius: '8px',
                color: '#f1f5f9',
              },
              footerActionLink: {
                color: '#60a5fa',
              },
              footer: {
                display: 'none',
              },
            },
          }}
        />
      </div>
    </div>
  )
}
