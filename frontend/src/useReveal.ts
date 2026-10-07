import { useEffect, useRef } from 'react'

/**
 * Reveal an element when it scrolls into view.
 *
 * Content is visible by default in the stylesheet and only hidden once this hook
 * confirms the browser supports the observer, so a failure can never leave the
 * page blank. Honours `prefers-reduced-motion` by skipping the animation.
 */
export function useReveal<T extends HTMLElement>() {
  const ref = useRef<T>(null)

  useEffect(() => {
    const node = ref.current
    if (!node) return
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
    if (!('IntersectionObserver' in window)) return

    node.classList.add('reveal')
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-revealed')
            observer.unobserve(entry.target)
          }
        }
      },
      { rootMargin: '0px 0px -60px 0px', threshold: 0.05 },
    )
    observer.observe(node)
    return () => observer.disconnect()
  }, [])

  return ref
}
