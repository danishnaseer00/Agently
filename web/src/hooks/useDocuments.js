import { useState, useEffect, useCallback } from 'react'
import {
  loadDocumentsFromApi,
  uploadDocumentToApi,
  deleteDocumentFromApi,
} from '../api/documents.js'

export function useDocuments(activeId) {
  const [documents, setDocuments] = useState([])
  const [selectedDocuments, setSelectedDocuments] = useState([])
  const [useRag, setUseRag] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadSuccess, setUploadSuccess] = useState('')

  useEffect(() => {
    if (activeId) {
      loadDocumentsFromApi(activeId).then(setDocuments)
      setSelectedDocuments([])
    }
  }, [activeId])

  useEffect(() => {
    if (uploadSuccess) {
      const timer = setTimeout(() => setUploadSuccess(''), 3000)
      return () => clearTimeout(timer)
    }
  }, [uploadSuccess])

  const uploadDocument = useCallback(async (file) => {
    if (!file || !activeId) return
    setUploading(true)
    const result = await uploadDocumentToApi(file, activeId)
    setUploading(false)
    if (result) {
      setUploadSuccess(`Uploaded: ${file.name}`)
      const docs = await loadDocumentsFromApi(activeId)
      setDocuments(docs)
      if (result.document_id) {
        setSelectedDocuments((prev) => [...prev, result.document_id])
      }
    }
    return result
  }, [activeId])

  const deleteDocument = useCallback(async (docId) => {
    await deleteDocumentFromApi(docId, activeId)
    setDocuments((prev) => prev.filter((d) => d.id !== docId))
    setSelectedDocuments((prev) => prev.filter((id) => id !== docId))
  }, [activeId])

  const toggleDocument = useCallback((docId) => {
    setSelectedDocuments((prev) =>
      prev.includes(docId)
        ? prev.filter((id) => id !== docId)
        : [...prev, docId],
    )
  }, [])

  const clearSelection = useCallback(() => {
    setSelectedDocuments([])
  }, [])

  return {
    documents,
    selectedDocuments,
    useRag,
    setUseRag,
    uploading,
    uploadSuccess,
    uploadDocument,
    deleteDocument,
    toggleDocument,
    clearSelection,
  }
}
