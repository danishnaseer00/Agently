import { API_BASE } from '../utils/constants.js'

/**
 * Send a chat message and return the SSE response stream reader.
 */
export async function sendChatMessage({
  message,
  history,
  conversationId,
  title,
  toolNames,
  documentIds,
  useRag,
}) {
  const response = await fetch(`${API_BASE}/api/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      history,
      conversation_id: conversationId,
      title,
      tool_names: toolNames.length > 0 ? toolNames : null,
      document_ids: documentIds.length > 0 ? documentIds : null,
      use_rag: useRag && documentIds.length > 0,
    }),
  })

  if (!response.body) {
    throw new Error('No response body')
  }

  return response.body.getReader()
}
