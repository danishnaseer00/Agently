import { useState, useCallback } from 'react'

export function useFullscreenImage() {
  const [fullscreenImage, setFullscreenImage] = useState(null)

  const openFullscreen = useCallback((src) => {
    setFullscreenImage(src)
  }, [])

  const closeFullscreen = useCallback(() => {
    setFullscreenImage(null)
  }, [])

  return {
    fullscreenImage,
    openFullscreen,
    closeFullscreen,
  }
}
