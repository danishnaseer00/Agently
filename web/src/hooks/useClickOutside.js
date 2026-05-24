import { useEffect } from 'react'

/**
 * Calls handler when a click/touch occurs outside the given ref element.
 *
 * Handles mobile edge case: when a native file picker dialog opens and closes,
 * the browser sometimes fires a phantom mousedown on <body>/<html> as it
 * restores focus. This would incorrectly close the tools menu mid-upload.
 * We ignore those document-level phantom events.
 */
export function useClickOutside(ref, handler, excludeRefs = []) {
  useEffect(() => {
    const handleClickOutside = (event) => {
      // Ignore phantom events on document-level elements — these often fire
      // after native dialogs (file picker, camera, etc.) return focus to the page
      if (
        event.target === document.body ||
        event.target === document.documentElement ||
        event.target === document
      ) {
        return
      }

      // Don't close if clicking on an excluded element
      for (const excludeRef of excludeRefs) {
        if (excludeRef.current && event.target === excludeRef.current) {
          return
        }
      }
      if (ref.current && !ref.current.contains(event.target)) {
        handler()
      }
    }

    // Use both mouse and touch events for cross-platform support
    document.addEventListener('mousedown', handleClickOutside)
    document.addEventListener('touchstart', handleClickOutside)

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
      document.removeEventListener('touchstart', handleClickOutside)
    }
  }, [ref, handler, excludeRefs])
}
