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
  const [uploadError, setUploadError] = useState('')

  useEffect(() => {
    if (activeId) {
      loadDocumentsFromApi(activeId).then(setDocuments)
      setSelectedDocuments([])
    }
  }, [activeId])

  useEffect(() => {
    if (uploadSuccess || uploadError) {
      const timer = setTimeout(() => {
        setUploadSuccess('')
        setUploadError('')
      }, 4000)
      return () => clearTimeout(timer)
    }
  }, [uploadSuccess, uploadError])

  const uploadDocument = useCallback(async (file) => {
    if (!file || !activeId) return
    setUploading(true)
    setUploadError('')
    setUploadSuccess('')
    try {
      const result = await uploadDocumentToApi(file, activeId)
      if (result && result.status !== 'failed') {
        setUploadSuccess(`Uploaded: ${file.name}`)
        const docs = await loadDocumentsFromApi(activeId)
        setDocuments(docs)
        if (result.document_id) {
          setSelectedDocuments((prev) => [...prev, result.document_id])
        }
        return result
      } else {
        const errMsg = result?.error || 'Upload failed. Please try again.'
        setUploadError(errMsg)
        return null
      }
    } catch (err) {
      setUploadError(err.message || 'Upload failed. Please try again.')
      return null
    } finally {
      setUploading(false)
    }
  }, [activeId])

  const deleteDocument = useCallback(async (docId) => {
    // Optimistically remove from UI immediately
    const prevDocs = documents
    const prevSelected = selectedDocuments
    setDocuments((prev) => prev.filter((d) => d.id !== docId))
    setSelectedDocuments((prev) => prev.filter((id) => id !== docId))
    try {
      await deleteDocumentFromApi(docId, activeId)
    } catch {
      // Revert on failure
      setDocuments(prevDocs)
      setSelectedDocuments(prevSelected)
    }
  }, [activeId, documents, selectedDocuments])

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
    uploadError,
    uploadDocument,
    deleteDocument,
    toggleDocument,
    clearSelection,
  }
}
