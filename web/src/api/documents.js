import { get, del, uploadFile } from './client.js'

export async function loadDocumentsFromApi(convId) {
  try {
    return await get(`/api/documents?conversation_id=${convId}`)
  } catch {
    return []
  }
}

export async function uploadDocumentToApi(file, convId) {
  try {
    return await uploadFile('/api/documents/upload', file, { conversation_id: convId })
  } catch {
    return null
  }
}

export async function deleteDocumentFromApi(docId, convId) {
  try {
    await del(`/api/documents/${docId}?conversation_id=${convId}`)
  } catch { /* ignore */ }
}
