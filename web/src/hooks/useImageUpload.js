import { useState, useCallback } from 'react'
import { analyzeImageApi } from '../api/images.js'

export function useImageUpload() {
  const [uploadedImage, setUploadedImage] = useState(null)
  const [imageAnalysis, setImageAnalysis] = useState(null)
  const [analyzingImage, setAnalyzingImage] = useState(false)

  const processImage = useCallback(async (file) => {
    if (!file.type.startsWith('image/')) {
      alert('Please upload an image file')
      return
    }

    const reader = new FileReader()
    reader.onload = (e) => {
      setUploadedImage(e.target.result)
    }
    reader.onerror = () => {
      alert('Failed to read image file')
    }
    reader.readAsDataURL(file)

    setAnalyzingImage(true)
    const result = await analyzeImageApi(file)
    setAnalyzingImage(false)

    if (result && !result.error) {
      setImageAnalysis(result.extracted_text || 'Image ready for analysis')
    } else {
      setImageAnalysis(result?.error || 'Failed to analyze image')
    }
  }, [])

  const clearImage = useCallback(() => {
    setUploadedImage(null)
    setImageAnalysis(null)
  }, [])

  const handleImageUpload = useCallback(async (event) => {
    const file = event.target.files?.[0]
    if (file) {
      await processImage(file)
      event.target.value = ''
    }
  }, [processImage])

  const handlePaste = useCallback(async (event) => {
    const items = event.clipboardData?.items
    if (!items) return

    for (const item of items) {
      if (item.type.startsWith('image/')) {
        event.preventDefault()
        const file = item.getAsFile()
        if (file) {
          await processImage(file)
        }
        break
      }
    }
  }, [processImage])

  return {
    uploadedImage,
    setUploadedImage,
    imageAnalysis,
    setImageAnalysis,
    analyzingImage,
    processImage,
    clearImage,
    handleImageUpload,
    handlePaste,
  }
}
