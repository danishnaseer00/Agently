import { Component } from 'react'

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }
      return (
        <div style={{
          padding: '24px',
          margin: '16px',
          background: '#fff5f5',
          border: '1px solid #fecaca',
          borderRadius: '12px',
          textAlign: 'center',
          color: '#991b1b',
        }}>
          <h3 style={{ margin: '0 0 8px', fontSize: '1.1rem' }}>Something went wrong</h3>
          <p style={{ margin: '0', fontSize: '0.9rem', color: '#b91c1c' }}>
            {this.state.error?.message || 'An unexpected error occurred'}
          </p>
          <button
            onClick={() => window.location.reload()}
            style={{
              marginTop: '12px',
              padding: '8px 20px',
              background: '#991b1b',
              color: '#fff',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '0.9rem',
            }}
          >
            Reload page
          </button>
        </div>
      )
    }

    return this.props.children
  }
}
