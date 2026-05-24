import { API_BASE } from '../utils/constants.js'
import { getAuthHeaders, refreshAuthToken } from './client.js'

/**
 * Build the request body for a chat message.
 */
function buildBody({ message, history, conversationId, title, toolNames, documentIds, useRag }) {
  return JSON.stringify({
    message,
    history,
    conversation_id: conversationId,
    title,
    tool_names: toolNames.length > 0 ? toolNames : null,
    document_ids: documentIds.length > 0 ? documentIds : null,
    use_rag: useRag && documentIds.length > 0,
  })
}

/**
 * Send a chat message and return the SSE response stream reader.
 */
export async function sendChatMessage(params) {
  const doFetch = async () => {
    const headers = {
      'Content-Type': 'application/json',
      ...getAuthHeaders(),
    }
    return fetch(`${API_BASE}/api/chat/stream`, {
      method: 'POST',
      headers,
      body: buildBody(params),
    })
  }

  let response = await doFetch()

  // On 401, try refreshing the token and retry once
  if (response.status === 401) {
    const refreshed = await refreshAuthToken()
    if (refreshed) {
      response = await doFetch()
    }
  }

  if (!response.ok) {
    const errorBody = await response.text().catch(() => '')
    throw new Error(`We're having trouble processing your request right now. Please try again.`)
  }

  if (!response.body) {
    throw new Error('No response body')
  }

  return response.body.getReader()
}

/**
 * Execute a slash command (e.g. /summarize, /deepThink) and return the result.
 * Includes a 50-second timeout to prevent the UI from freezing forever.
 */
export async function sendSlashCommand(command, conversationId, topic = '') {
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), 50000)

  const headers = {
    'Content-Type': 'application/json',
    ...getAuthHeaders(),
  }

  try {
    const response = await fetch(`${API_BASE}/api/chat/slash`, {
      method: 'POST',
      headers,
      signal: controller.signal,
      body: JSON.stringify({
        command,
        conversation_id: conversationId,
        topic: topic || null,
      }),
    })

    clearTimeout(timeoutId)

    if (!response.ok) {
      const errorBody = await response.text().catch(() => '')
      throw new Error(`We're having trouble processing your request right now. Please try again.`)
    }

    return response.json()
  } catch (err) {
    clearTimeout(timeoutId)
    if (err.name === 'AbortError') {
      throw new Error('Request timed out. Please try again.')
    }
    throw err
  }
}
