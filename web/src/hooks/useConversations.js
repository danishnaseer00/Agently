import { useState, useCallback, useEffect } from 'react'
import {
  loadConversationsFromApi,
  createConversation,
  deleteConversationApi,
  updateTitleApi,
} from '../api/conversations.js'

export function useConversations() {
  const [conversations, setConversations] = useState([])
  const [activeId, setActiveId] = useState(null)
  const [loaded, setLoaded] = useState(false)

  // Initial load
  useEffect(() => {
    if (!loaded) {
      loadConversationsFromApi().then((data) => {
        setConversations(data)
        setLoaded(true)
        if (data && data.length > 0 && !activeId) {
          setActiveId(data[0].id)
        }
      })
    }
  }, [loaded, activeId])

  const refreshConversations = useCallback(() => {
    loadConversationsFromApi().then(setConversations)
  }, [])

  const createNewChat = useCallback(() => {
    const fresh = createConversation()
    setConversations((prev) => [fresh, ...prev])
    setActiveId(fresh.id)
    return fresh
  }, [])

  const deleteChat = useCallback(async (convId) => {
    await deleteConversationApi(convId)
    setConversations((prev) => prev.filter((c) => c.id !== convId))
  }, [])

  const updateTitle = useCallback(async (convId, title) => {
    // Optimistically update local state immediately
    setConversations((prev) =>
      prev.map((c) => (c.id === convId ? { ...c, title } : c)),
    )
    try {
      await updateTitleApi(convId, title)
    } catch {
      // Revert on failure — re-fetch from server
      refreshConversations()
    }
  }, [refreshConversations])

  return {
    conversations,
    setConversations,
    activeId,
    setActiveId,
    loaded,
    refreshConversations,
    createNewChat,
    deleteChat,
    updateTitle,
  }
}
