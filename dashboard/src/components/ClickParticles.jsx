import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

export default function ClickParticles() {
  const [particles, setParticles] = useState([])

  useEffect(() => {
    const handleClick = (e) => {
      // Create 5-8 particles at the click location
      const newParticles = Array.from({ length: 6 }).map((_, i) => ({
        id: Date.now() + i,
        x: e.clientX,
        y: e.clientY,
        angle: Math.random() * Math.PI * 2,
        velocity: 30 + Math.random() * 50,
        size: 4 + Math.random() * 8,
        color: Math.random() > 0.5 ? '#ff7f50' : '#ffb800', // Coral or Amber
        shape: Math.random() > 0.5 ? 'circle' : 'square'
      }))
      setParticles(prev => [...prev, ...newParticles])
      
      // Clean up particles after animation
      setTimeout(() => {
        setParticles(prev => prev.filter(p => !newParticles.find(np => np.id === p.id)))
      }, 1000)
    }

    window.addEventListener('click', handleClick)
    return () => window.removeEventListener('click', handleClick)
  }, [])

  return (
    <div className="fixed inset-0 pointer-events-none z-[99999]">
      <AnimatePresence>
        {particles.map(p => (
          <motion.div
            key={p.id}
            initial={{ 
              opacity: 1, 
              x: p.x, 
              y: p.y, 
              scale: 0.5 
            }}
            animate={{ 
              opacity: 0,
              x: p.x + Math.cos(p.angle) * p.velocity,
              y: p.y + Math.sin(p.angle) * p.velocity - 60, // Float up heavily
              scale: 1.5,
              rotate: p.shape === 'square' ? 180 : 0
            }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.8, ease: "easeOut" }}
            style={{
              position: 'absolute',
              width: p.size,
              height: p.size,
              borderRadius: p.shape === 'circle' ? '50%' : '20%',
              backgroundColor: p.color,
              boxShadow: `0 0 12px ${p.color}`,
            }}
          />
        ))}
      </AnimatePresence>
    </div>
  )
}

