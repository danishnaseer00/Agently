import { useEffect } from 'react'

/**
 * Calls handler when a click/touch occurs outside the given ref element.
 */
export function useClickOutside(ref, handler, excludeRefs = []) {
  useEffect(() => {
    const handleClickOutside = (event) => {
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

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [ref, handler, excludeRefs])
}
