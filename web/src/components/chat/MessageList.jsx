import { useEffect, useRef } from 'react'
import MessageBubble from './MessageBubble.jsx'
import ThinkingIndicator from './ThinkingIndicator.jsx'

export default function MessageList({ messages, isThinking, statusText, onImageClick }) {
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages, isThinking, statusText])

  return (
    <section className="message-list">
      {messages.map((message) => (
        <MessageBubble
          key={message.id}
          message={message}
          onImageClick={onImageClick}
        />
      ))}
      {isThinking && (
        <ThinkingIndicator statusText={statusText} />
      )}
      <div ref={bottomRef} />
    </section>
  )
}
