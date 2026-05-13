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
    throw new Error(`Request failed: ${response.status}${errorBody ? ` — ${errorBody}` : ''}`)
  }

  if (!response.body) {
    throw new Error('No response body')
  }

  return response.body.getReader()
}
