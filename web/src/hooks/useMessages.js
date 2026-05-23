import { useState, useCallback, useRef, useEffect } from 'react'
import { sendChatMessage } from '../api/chat.js'
import { parseSsePayload } from '../utils/sse.js'
import { loadMessagesFromApi } from '../api/conversations.js'

export function useMessages({ activeId, refreshConversations }) {
  const [messages, setMessages] = useState([])
  const [isThinking, setIsThinking] = useState(false)
  const [statusText, setStatusText] = useState('')
  const bottomRef = useRef(null)

  const chunkedHistory = (msgs) =>
    msgs.map((msg) => ({ role: msg.role, content: msg.content }))

  // Load messages from API when active conversation changes
  useEffect(() => {
    if (!activeId) return
    let cancelled = false
    loadMessagesFromApi(activeId).then((data) => {
      if (!cancelled) setMessages(data)
    })
    return () => {
      cancelled = true
    }
  }, [activeId])

  const sendMessage = useCallback(async ({
    inputValue,
    uploadedImage,
    imageAnalysis,
    selectedTools,
    selectedDocuments,
    useRag,
    setInputValue,
    setUploadedImage,
    setImageAnalysis,
    setShowTools,
  }) => {
    const trimmed = inputValue.trim()
    if ((!trimmed && !uploadedImage) || !activeId) return

    const history = chunkedHistory(messages)

    let messageContent = trimmed || (uploadedImage ? 'Please analyze the attached image' : '')

    const userMsg = { id: `user-${Date.now()}`, role: 'user', content: messageContent, image: uploadedImage }
    setMessages((prev) => [...prev, userMsg, { id: `assistant-${Date.now()}`, role: 'assistant', content: '' }])

    setInputValue('')
    setUploadedImage(null)
    setImageAnalysis(null)
    setIsThinking(true)
    setStatusText('Thinking...')
    setShowTools(false)

    try {
      // Build API message with optional image analysis context
      let apiMessage = messageContent
      if (imageAnalysis && imageAnalysis.length > 0) {
        apiMessage = messageContent
          ? `${messageContent}\n\n[System Note: The user has attached an image to this message. A vision model has already analyzed it and provided this description: ${imageAnalysis}. Base your response directly on this description. Do NOT output "Final Answer:" and do NOT mention that you cannot see the image directly, just answer the prompt naturally.]`
          : `[System Note: The user has attached an image to this message. A vision model has already analyzed it and provided this description: ${imageAnalysis}. Base your response directly on this description. Do NOT output "Final Answer:" and do NOT mention that you cannot see the image directly, just answer the prompt naturally.]`
      }

      const reader = await sendChatMessage({
        message: apiMessage,
        history,
        conversationId: activeId,
        toolNames: selectedTools,
        documentIds: selectedDocuments,
        useRag,
      })

      const decoder = new TextDecoder()
      let buffer = ''
      let receivedAnyEvent = false

      // Add a 90-second timeout for the entire response
      // Resolves to true if timeout fires, false otherwise
      const TIMEOUT_MS = 90000
      const TIMEOUT = Symbol('timeout')
      const timeoutPromise = new Promise((resolve) =>
        setTimeout(() => resolve(TIMEOUT), TIMEOUT_MS)
      )

      const readLoop = (async () => {
        while (true) {
          const { value, done } = await reader.read()
          if (done) break
          receivedAnyEvent = true
          buffer += decoder.decode(value, { stream: true })
          const parts = buffer.split('\n\n')
          buffer = parts.pop() || ''

          for (const part of parts) {
            if (!part.trim()) continue
            const { event, data } = parseSsePayload(part)
            let payload = {}
            try {
              payload = JSON.parse(data)
            } catch {
              payload = { text: data }
            }

            if (event === 'status') {
              setStatusText(payload.state || 'Thinking...')
            }

            if (event === 'tool') {
              setStatusText(`Using tool: ${payload.tool || 'tool'}`)
            }

            if (event === 'chunk') {
              setMessages((prev) => {
                const lastIndex = prev.length - 1
                return prev.map((m, i) =>
                  i === lastIndex && m.role === 'assistant'
                    ? { ...m, content: `${m.content}${payload.text || ''}` }
                    : m,
                )
              })
            }

            if (event === 'done') {
              setIsThinking(false)
              setStatusText('')
              refreshConversations()
            }
          }
        }
      })()

      const winner = await Promise.race([readLoop, timeoutPromise])

      // If timeout won (resolved with TIMEOUT symbol), throw an error
      if (winner === TIMEOUT) {
        // If we received at least some data, the response is just slow — show a friendlier message
        const msg = receivedAnyEvent
          ? 'Response is taking longer than expected. The answer may still arrive — check back shortly.'
          : 'The server did not respond. Please try again.'
        throw new Error(msg)
      }
    } catch (error) {
      setMessages((prev) =>
        prev.map((m) =>
          m.role === 'assistant' && m.content === ''
            ? { ...m, content: `Error: ${error.message}` }
            : m,
        ),
      )
      setIsThinking(false)
      setStatusText('')
    }
  }, [activeId, messages, refreshConversations])

  return {
    messages,
    setMessages,
    isThinking,
    setIsThinking,
    statusText,
    setStatusText,
    bottomRef,
    sendMessage,
  }
}
