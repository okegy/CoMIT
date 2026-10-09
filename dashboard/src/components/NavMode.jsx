import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Navigation2, TriangleAlert, Volume2, MapPin } from 'lucide-react'

export default function NavMode({ ego, emergency, spat }) {
  const e = ego || {}
  const speed = e.speed_kmh ?? 0
  const [navPath, setNavPath] = useState(0)

  // Simulate vehicle moving along the route
  useEffect(() => {
    if (speed > 0) {
      const interval = setInterval(() => {
        setNavPath(p => (p + (speed / 50)) % 100)
      }, 100)
      return () => clearInterval(interval)
    }
  }, [speed])

  const ttg = e.time_to_green ?? 15
  
  return (
    <div className="relative w-full h-[600px] bg-[#1e293b] rounded-3xl overflow-hidden border border-slate-700/50 shadow-2xl flex flex-col">
      {/* Top Bar - Next Turn */}
      <div className="absolute top-4 left-4 right-4 z-20 flex gap-4">
        <div className="bg-emerald-600 shadow-lg rounded-2xl p-4 flex-1 flex items-center gap-4 text-white">
          <Navigation2 size={32} className="-rotate-45" />
          <div>
            <div className="text-3xl font-black digits">400 m</div>
            <div className="text-emerald-100 font-semibold">Turn right onto Anna Salai</div>
          </div>
        </div>
        <div className="bg-slate-900/80 backdrop-blur border border-slate-700/50 shadow-lg rounded-2xl p-4 w-48 text-center text-white flex flex-col justify-center">
          <div className="text-slate-400 text-xs font-bold uppercase mb-1">GLOSA Advisory</div>
          <div className="text-2xl font-black digits text-sky-400">{e.advisory_kmh || 40} km/h</div>
        </div>
      </div>

      {/* Simulated 3D Map View */}
      <div className="flex-1 relative overflow-hidden" style={{ perspective: '800px' }}>
        <motion.div 
          className="absolute inset-0 flex items-center justify-center"
          style={{ rotateX: '60deg', scale: 2.5, transformOrigin: 'center 70%' }}
        >
          <svg width="400" height="800" viewBox="0 0 400 800" className="opacity-80">
            {/* Background Grid */}
            <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="1"/>
            </pattern>
            <rect width="400" height="800" fill="url(#grid)" />
            
            {/* Road */}
            <rect x="150" y="0" width="100" height="800" fill="#334155" />
            <line x1="200" y1="0" x2="200" y2="800" stroke="#cbd5e1" strokeWidth="4" strokeDasharray="20 20" />
            <line x1="152" y1="0" x2="152" y2="800" stroke="#fef08a" strokeWidth="2" />
            <line x1="298" y1="0" x2="298" y2="800" stroke="#fef08a" strokeWidth="2" />
            
            {/* Route Line */}
            <motion.path 
              d="M 225 800 L 225 300 C 225 200, 350 200, 400 200"
              fill="none" stroke="#0ea5e9" strokeWidth="12" strokeLinecap="round" strokeLinejoin="round" opacity="0.8"
            />
            
            {/* Ego Vehicle (Blue Arrow) */}
            <motion.g transform={`translate(225, ${600 - navPath * 4})`} className="drop-shadow-2xl">
              <polygon points="-15,20 0,-25 15,20 0,10" fill="#38bdf8" stroke="#0284c7" strokeWidth="2" />
              {/* Headlights */}
              <circle cx="-10" cy="-20" r="3" fill="#fef08a" className="glow-amber" />
              <circle cx="10" cy="-20" r="3" fill="#fef08a" className="glow-amber" />
            </motion.g>

            {/* Emergency Vehicle Simulation (Red/White) approaching from behind */}
            <AnimatePresence>
              {emergency && (
                <motion.g 
                  initial={{ y: 800, opacity: 0 }} 
                  animate={{ y: 600 - navPath * 4 + 100, opacity: 1 }} 
                  exit={{ y: 800, opacity: 0 }}
                  transition={{ duration: 2, ease: "easeOut" }}
                  transform={`translate(225, 0)`}
                >
                  <rect x="-12" y="-15" width="24" height="40" rx="4" fill="#ef4444" stroke="#b91c1c" strokeWidth="2" />
                  <rect x="-10" y="-10" width="20" height="30" fill="#ffffff" />
                  <circle cx="0" cy="-5" r="4" fill="#38bdf8" className="glow-amber" />
                  <circle cx="0" cy="15" r="4" fill="#ef4444" className="glow-red" />
                </motion.g>
              )}
            </AnimatePresence>

          </svg>
        </motion.div>

        {/* Emergency V2X Pop-Up */}
        <AnimatePresence>
          {emergency && (
            <motion.div 
              initial={{ y: 50, opacity: 0, scale: 0.9 }} 
              animate={{ y: 0, opacity: 1, scale: 1 }} 
              exit={{ y: 50, opacity: 0, scale: 0.9 }}
              className="absolute bottom-24 left-1/2 -translate-x-1/2 w-[90%] max-w-lg"
            >
              <div className="bg-red-600 shadow-2xl shadow-red-900/50 rounded-2xl p-6 border-2 border-red-400 text-center animate-pulse-fast">
                <TriangleAlert size={48} className="mx-auto text-white mb-2" />
                <h2 className="text-2xl font-black text-white uppercase tracking-wider mb-1">
                  Ambulance Approaching
                </h2>
                <p className="text-red-100 font-bold text-lg">
                  Please merge left immediately to allow emergency vehicle to pass.
                </p>
                <div className="mt-4 flex items-center justify-center gap-2 bg-red-950/40 rounded-lg py-2">
                  <Volume2 size={18} className="text-red-300" />
                  <span className="text-red-200 text-sm font-semibold">Broadcasting voice instruction...</span>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Bottom Bar - ETA & Speed */}
      <div className="bg-slate-900 border-t border-slate-700/50 p-4 flex items-center justify-between z-20">
        <div className="flex gap-8 text-slate-300 font-semibold">
          <div>
            <div className="text-2xl font-black text-white">12<span className="text-sm font-normal text-slate-400 ml-1">min</span></div>
            <div className="text-xs text-slate-500">14 km</div>
          </div>
          <div>
            <div className="text-2xl font-black text-white digits">{Math.round(speed)}<span className="text-sm font-normal text-slate-400 ml-1 font-sans">km/h</span></div>
            <div className="text-xs text-slate-500">Current Speed</div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="px-4 py-2 bg-slate-800 rounded-xl border border-slate-700 text-sm font-bold flex items-center gap-2 text-slate-300">
            <MapPin size={16} className="text-red-400" /> JN-1 Junction
          </div>
          <button className="px-6 py-3 bg-red-500 hover:bg-red-600 text-white font-bold rounded-xl transition-colors shadow-lg">
            Exit
          </button>
        </div>
      </div>
    </div>
  )
}
