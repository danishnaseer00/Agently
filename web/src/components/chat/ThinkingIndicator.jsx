export default function ThinkingIndicator({ statusText }) {
  return (
    <div className="thinking">
      <div className="dot"></div>
      <span>{statusText || 'Thinking...'}</span>
    </div>
  )
}
