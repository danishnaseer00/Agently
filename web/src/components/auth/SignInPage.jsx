import { useState } from 'react'
import { SignIn, SignUp } from '@clerk/clerk-react'

const cardStyles = {
  rootBox: {
    width: '100%',
  },
  card: {
    background: '#ffffff',
    borderRadius: '16px',
    boxShadow: '0 4px 24px rgba(0,0,0,0.08)',
    border: '1px solid #e5e7eb',
  },
  headerTitle: {
    color: '#0b0b0d',
    fontSize: '1.25rem',
    fontWeight: 700,
  },
  headerSubtitle: {
    color: '#6b7280',
  },
  formButtonPrimary: {
    background: '#111827',
    borderRadius: '8px',
    fontSize: '0.9rem',
    fontWeight: 600,
    transition: 'opacity 0.2s ease',
  },
  formFieldInput: {
    background: '#f9fafb',
    border: '1px solid #e5e7eb',
    borderRadius: '8px',
    color: '#0b0b0d',
    transition: 'border-color 0.2s ease',
  },
  formFieldInput__focused: {
    borderColor: '#111827',
  },
  formFieldLabel: {
    color: '#6b7280',
    fontWeight: 500,
  },
  dividerLine: {
    background: '#e5e7eb',
  },
  dividerText: {
    color: '#9ca3af',
  },
  socialButtonsBlockButton: {
    background: '#f9fafb',
    border: '1px solid #e5e7eb',
    borderRadius: '8px',
    color: '#0b0b0d',
    fontWeight: 500,
    transition: 'all 0.2s ease',
  },
  footerActionLink: {
    color: '#111827',
    fontWeight: 600,
  },
  footer: {
    display: 'none',
  },
  socialButtonsBlockButton__google: {
    background: '#ffffff',
  },
  socialButtonsBlockButton__github: {
    background: '#ffffff',
  },
  identityPreviewEditButton: {
    color: '#111827',
  },
  formFieldAction: {
    color: '#111827',
  },
  formFieldError: {
    color: '#dc2626',
  },
  alert: {
    borderRadius: '8px',
  },
  alertText: {
    color: '#0b0b0d',
  },
  otpCodeFieldInput: {
    background: '#f9fafb',
    border: '1px solid #e5e7eb',
    borderRadius: '8px',
    color: '#0b0b0d',
  },
}

export default function SignInPage() {
  const [mode, setMode] = useState('sign-in')

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '100vh',
      background: '#f7f7f8',
      padding: '20px',
    }}>
      <div style={{
        marginBottom: '32px',
        textAlign: 'center',
      }}>
        <h1 style={{
          fontSize: '1.8rem',
          fontWeight: 700,
          color: '#0b0b0d',
          margin: '0 0 8px 0',
          letterSpacing: '-0.02em',
          fontFamily: '"Playfair Display", serif',
        }}>
          ReAct Agent
        </h1>
        <p style={{
          fontSize: '0.95rem',
          color: '#6b7280',
          margin: 0,
          fontFamily: '"Computer Modern Serif", serif',
        }}>
          {mode === 'sign-in' ? 'Welcome back' : 'Create your account'}
        </p>
      </div>

      {/* Mode toggle */}
      <div style={{
        display: 'flex',
        gap: '4px',
        marginBottom: '24px',
        background: '#e5e7eb',
        borderRadius: '10px',
        padding: '4px',
      }}>
        <button
          onClick={() => setMode('sign-in')}
          style={{
            padding: '8px 24px',
            borderRadius: '8px',
            border: 'none',
            background: mode === 'sign-in' ? '#111827' : 'transparent',
            color: mode === 'sign-in' ? '#ffffff' : '#6b7280',
            fontWeight: 600,
            fontSize: '0.9rem',
            cursor: 'pointer',
            transition: 'all 0.2s ease',
            fontFamily: '"Computer Modern Serif", serif',
          }}
        >
          Sign In
        </button>
        <button
          onClick={() => setMode('sign-up')}
          style={{
            padding: '8px 24px',
            borderRadius: '8px',
            border: 'none',
            background: mode === 'sign-up' ? '#111827' : 'transparent',
            color: mode === 'sign-up' ? '#ffffff' : '#6b7280',
            fontWeight: 600,
            fontSize: '0.9rem',
            cursor: 'pointer',
            transition: 'all 0.2s ease',
            fontFamily: '"Computer Modern Serif", serif',
          }}
        >
          Sign Up
        </button>
      </div>

      <div style={{
        width: '100%',
        maxWidth: '420px',
      }}>
        {mode === 'sign-in' ? (
          <SignIn
            routing="hash"
            appearance={{ elements: cardStyles }}
          />
        ) : (
          <SignUp
            routing="hash"
            appearance={{ elements: cardStyles }}
          />
        )}
      </div>
    </div>
  )
}
