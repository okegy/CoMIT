import { useEffect, useRef } from 'react'

/** Glassmorphic cursor: glowing dot + frosted ring; ring expands over
 *  interactive elements (a, button, [data-cursor]). Desktop pointers only. */
export default function GlassCursor() {
  const ref = useRef(null)

  useEffect(() => {
    if (!window.matchMedia('(pointer: fine)').matches) return
    document.documentElement.classList.add('cursor-none-desktop')
    const el = ref.current
    let rx = window.innerWidth / 2, ry = window.innerHeight / 2
    let tx = rx, ty = ry
    let raf
    const onMove = (e) => {
      tx = e.clientX; ty = e.clientY
      el.style.setProperty('--dx', `${tx}px`)
      const t = e.target
      const interactive = t.closest?.('a, button, [role="button"], input, [data-cursor]')
      el.classList.toggle('hovering', !!interactive)
    }
    const loop = () => {
      rx += (tx - rx) * 0.22
      ry += (ty - ry) * 0.22
      el.style.transform = `translate(${rx}px, ${ry}px)`
      raf = requestAnimationFrame(loop)
    }
    window.addEventListener('mousemove', onMove)
    raf = requestAnimationFrame(loop)
    return () => {
      window.removeEventListener('mousemove', onMove)
      cancelAnimationFrame(raf)
      document.documentElement.classList.remove('cursor-none-desktop')
    }
  }, [])

  return (
    <div ref={ref} className="glass-cursor" aria-hidden="true">
      <div className="ring" />
      <div className="dot" style={{ position: 'absolute', left: 0, top: 0 }} />
    </div>
  )
}

