import { get, post, patch, del } from './client.js'

export function createConversation() {
  return {
    id: `conv-${Date.now()}`,
    title: 'New chat',
    createdAt: Date.now(),
    messages: [],
  }
}

export async function loadConversationsFromApi() {
  try {
    const data = await get('/api/conversations')
    if (!Array.isArray(data) || data.length === 0) return [createConversation()]
    return data.map((c) => ({
      id: c.id,
      title: c.title,
      createdAt: new Date(c.created_at).getTime(),
      messages: [],
    }))
  } catch {
    return [createConversation()]
  }
}

export async function loadMessagesFromApi(convId) {
  try {
    const data = await get(`/api/conversations/${convId}/messages`)
    return data.map((m) => ({
      id: m.id,
      role: m.role,
      content: m.content,
    }))
  } catch {
    return []
  }
}

export async function deleteConversationApi(convId) {
  try {
    await del(`/api/conversations/${convId}`)
  } catch { /* ignore */ }
}

export async function updateTitleApi(convId, title) {
  try {
    await patch(`/api/conversations/${convId}`, { title })
  } catch { /* ignore */ }
}
