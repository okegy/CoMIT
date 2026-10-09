import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Navigation2, TriangleAlert, Volume2, MapPin, Compass, AlertOctagon, ShieldAlert, Sparkles, Radio, Gauge, Zap } from 'lucide-react'

export default function NavMode({ ego, emergency, spat, hazard, lanes }) {
  const e = ego || {}
  const [speed, setSpeed] = useState(e.speed_kmh || 38)
  const [distanceToJunction, setDistanceToJunction] = useState(e.distance_to_stop || 220)
  const [navProgress, setNavProgress] = useState(0)
  const [activePopup, setActivePopup] = useState('signal') // 'signal', 'obstacle', 'emergency', null
  const [voiceAudioAlert, setVoiceAudioAlert] = useState(null)

  // Extract signal state from SPaT
  const activeGreen = spat?.states?.find(s => s.event_state === 6)
  const isRed = spat?.states?.some(s => s.event_state === 3)
  const signalCountdown = activeGreen?.min_end_time ?? spat?.states?.[0]?.min_end_time ?? 11
  const glosaSpeed = e.advisory_kmh || (activeGreen ? 42 : 32)
  const isEmergency = spat?.mode === 'EMERGENCY' || !!emergency
  const isHazard = !!hazard || (distanceToJunction < 180 && distanceToJunction > 80)

  // Realistic vehicle telemetry and distance loop
  useEffect(() => {
    const timer = setInterval(() => {
      setNavProgress(prev => (prev + 1.2) % 100)
      setDistanceToJunction(prev => {
        if (prev <= 15) return 300 // loop back
        return Math.max(10, prev - 4)
      })
      if (!ego?.speed_kmh) {
        setSpeed(prev => Math.min(55, Math.max(25, prev + (Math.random() * 4 - 2))))
      } else {
        setSpeed(ego.speed_kmh)
      }
    }, 200)
    return () => clearInterval(timer)
  }, [ego?.speed_kmh])

  // Context-aware Google Maps style pop-up priority
  useEffect(() => {
    if (isEmergency) {
      setActivePopup('emergency')
      setVoiceAudioAlert('Emergency Vehicle Detected behind you. Merge Left.')
    } else if (isHazard) {
      setActivePopup('hazard')
      setVoiceAudioAlert('Warning: Pothole detected 120m ahead. Reduce Speed.')
    } else if (distanceToJunction < 260) {
      setActivePopup('signal')
      setVoiceAudioAlert(`Traffic signal in ${Math.round(distanceToJunction)}m. Recommended speed: ${glosaSpeed} km/h`)
    } else {
      setActivePopup(null)
    }
  }, [isEmergency, isHazard, distanceToJunction, glosaSpeed])

  return (
    <div className="relative w-full h-[620px] bg-[#0c1322] rounded-3xl overflow-hidden border border-slate-700/60 shadow-2xl flex flex-col font-sans select-none">
      {/* Google Maps Style Top Navigation Bar */}
      <div className="absolute top-4 left-4 right-4 z-30 flex flex-wrap gap-3">
        {/* Next Maneuver Green Banner */}
        <div className="bg-[#0f9d58] shadow-2xl shadow-amber-950/60 rounded-2xl px-5 py-3.5 flex-1 flex items-center justify-between text-white border border-amber-400/30">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-white/15 flex items-center justify-center border border-white/20">
              <Navigation2 size={28} className="-rotate-45 text-white" />
            </div>
            <div>
              <div className="text-2xl font-black tracking-tight digits">
                {Math.round(distanceToJunction)} m
              </div>
              <div className="text-amber-100 text-xs font-semibold">
                Proceed straight through <span className="font-bold text-white">Anna Salai · JN-1</span>
              </div>
            </div>
          </div>
          <div className="hidden sm:flex items-center gap-2 bg-amber-900/50 px-3 py-1.5 rounded-xl border border-amber-400/20 text-xs">
            <Radio size={14} className="text-amber-300 animate-pulse" />
            <span className="font-bold text-amber-200">V2X LIVE</span>
          </div>
        </div>

        {/* GLOSA Smart Speed Banner */}
        <div className="bg-slate-900/90 backdrop-blur-md border border-slate-700/80 shadow-2xl rounded-2xl px-4 py-3 min-w-[170px] text-center text-white flex flex-col justify-center">
          <div className="text-slate-400 text-[10px] font-bold uppercase tracking-wider flex items-center justify-center gap-1">
            <Zap size={12} className="text-orange-400" /> GLOSA Advisory
          </div>
          <div className="text-2xl font-black digits text-orange-400 mt-0.5">
            {glosaSpeed} <span className="text-xs font-semibold text-slate-400 font-sans">km/h</span>
          </div>
          <div className="text-[9.5px] text-amber-400 font-semibold mt-0.5">
            Catch Green Wave
          </div>
        </div>
      </div>

      {/* Floating Compass and Re-Center Tools */}
      <div className="absolute top-24 right-4 z-20 flex flex-col gap-2">
        <div className="w-10 h-10 rounded-xl bg-slate-900/80 backdrop-blur border border-slate-700/60 shadow-lg flex items-center justify-center text-slate-300 hover:text-white transition-colors cursor-pointer">
          <Compass size={20} className="text-red-400" />
        </div>
        <div className="px-2.5 py-1 rounded-lg bg-slate-900/80 backdrop-blur border border-slate-700/60 text-[10px] font-bold text-slate-300 text-center font-mono">
          3D POV
        </div>
      </div>

      {/* Simulated 3D Google Maps Perspective View */}
      <div className="flex-1 relative overflow-hidden bg-[#0e1726]" style={{ perspective: '900px' }}>
        <motion.div
          className="absolute inset-0 flex items-center justify-center"
          style={{ rotateX: '58deg', scale: 2.3, transformOrigin: 'center 75%' }}
        >
          <svg width="450" height="850" viewBox="0 0 450 850" className="opacity-90">
            {/* Dark Map Grid & City Blocks */}
            <defs>
              <pattern id="nav-grid" width="50" height="50" patternUnits="userSpaceOnUse">
                <path d="M 50 0 L 0 0 0 50" fill="none" stroke="rgba(56, 189, 248, 0.05)" strokeWidth="1" />
              </pattern>
              <linearGradient id="route-gradient" x1="0%" y1="100%" x2="0%" y2="0%">
                <stop offset="0%" stopColor="#0284c7" />
                <stop offset="60%" stopColor="#38bdf8" />
                <stop offset="100%" stopColor="#4ade80" />
              </linearGradient>
            </defs>
            <rect width="450" height="850" fill="url(#nav-grid)" />

            {/* City Building Footprints */}
            <rect x="20" y="80" width="120" height="200" rx="6" fill="#131e33" stroke="#1e293b" strokeWidth="2" />
            <rect x="310" y="80" width="120" height="200" rx="6" fill="#131e33" stroke="#1e293b" strokeWidth="2" />
            <rect x="20" y="340" width="120" height="240" rx="6" fill="#131e33" stroke="#1e293b" strokeWidth="2" />
            <rect x="310" y="340" width="120" height="240" rx="6" fill="#131e33" stroke="#1e293b" strokeWidth="2" />

            {/* Main Road Surface */}
            <rect x="160" y="0" width="130" height="850" fill="#1e293b" />
            {/* Road Markings */}
            <line x1="225" y1="0" x2="225" y2="850" stroke="#f8fafc" strokeWidth="3" strokeDasharray="24 18" />
            <line x1="162" y1="0" x2="162" y2="850" stroke="#facc15" strokeWidth="3" />
            <line x1="288" y1="0" x2="288" y2="850" stroke="#facc15" strokeWidth="3" />

            {/* Upcoming Intersection Stop Line */}
            <line x1="160" y1="200" x2="290" y2="200" stroke="#ef4444" strokeWidth="6" />
            <text x="225" y="190" textAnchor="middle" fill="#f87171" fontSize="12" fontWeight="bold" fontFamily="sans-serif">
              STOP LINE · JN-1 (200m)
            </text>

            {/* Active Navigation Route Ribbon (Cyan/Green Glow) */}
            <motion.path
              d="M 225 850 L 225 200 L 225 0"
              fill="none"
              stroke="url(#route-gradient)"
              strokeWidth="16"
              strokeLinecap="round"
              strokeLinejoin="round"
              opacity="0.85"
            />

            {/* Hazard / Pothole Indicator on Road */}
            <g transform="translate(245, 340)">
              <circle cx="0" cy="0" r="14" fill="#ea580c" opacity="0.3" className="animate-ping" />
              <polygon points="0,-10 10,8 -10,8" fill="#f97316" stroke="#fff" strokeWidth="1.5" />
            </g>

            {/* Ego Connected Vehicle (Google Navigation orange Puck + Heading Arrow) */}
            <motion.g transform={`translate(225, ${640 - (navProgress % 100) * 4.2})`} className="drop-shadow-2xl">
              {/* Outer Accuracy Circle */}
              <circle cx="0" cy="0" r="28" fill="rgba(56, 189, 248, 0.2)" stroke="#38bdf8" strokeWidth="1.5" />
              {/* Vehicle Body */}
              <polygon points="-16,22 0,-26 16,22 0,10" fill="#0284c7" stroke="#38bdf8" strokeWidth="2.5" />
              {/* Center Core */}
              <circle cx="0" cy="2" r="5" fill="#ffffff" />
              {/* Headlights Beam */}
              <polygon points="-10,-24 -30,-90 30,-90 10,-24" fill="rgba(254, 240, 138, 0.15)" />
            </motion.g>

            {/* Ambulance Approaching from Behind in Emergency Mode */}
            <AnimatePresence>
              {isEmergency && (
                <motion.g
                  initial={{ y: 850, opacity: 0 }}
                  animate={{ y: 640 - (navProgress % 100) * 4.2 + 90, opacity: 1 }}
                  exit={{ y: 850, opacity: 0 }}
                  transition={{ duration: 1.5, ease: 'easeOut' }}
                  transform="translate(225, 0)"
                >
                  <rect x="-14" y="-18" width="28" height="46" rx="5" fill="#ef4444" stroke="#ffffff" strokeWidth="2" />
                  <circle cx="-6" cy="-10" r="3.5" fill="#38bdf8" className="animate-pulse" />
                  <circle cx="6" cy="-10" r="3.5" fill="#ef4444" className="animate-pulse" />
                  <text x="0" y="16" textAnchor="middle" fill="#fff" fontSize="8" fontWeight="bold">AMB</text>
                </motion.g>
              )}
            </AnimatePresence>
          </svg>
        </motion.div>

        {/* ========================================================================= */}
        {/* DYNAMIC GOOGLE MAPS POP-UPS (SIGNAL / OBSTACLE / EMERGENCY) */}
        {/* ========================================================================= */}
        <div className="absolute bottom-20 left-4 right-4 z-30 flex justify-center pointer-events-none">
          <AnimatePresence mode="wait">
            {/* POP-UP 1: Next 200m Traffic Signal Ahead */}
            {activePopup === 'signal' && (
              <motion.div
                key="signal-popup"
                initial={{ y: 40, opacity: 0, scale: 0.92 }}
                animate={{ y: 0, opacity: 1, scale: 1 }}
                exit={{ y: 30, opacity: 0, scale: 0.92 }}
                className="w-full max-w-md bg-slate-900/95 backdrop-blur-xl border border-orange-500/40 shadow-2xl rounded-2xl p-4 pointer-events-auto"
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <div className={`w-3.5 h-3.5 rounded-full ${isRed ? 'bg-red-500 animate-pulse' : 'bg-amber-400'}`} />
                    <span className="text-xs font-bold text-white uppercase tracking-wider">
                      Next Signal in {Math.round(distanceToJunction)}m · JN-1 Anna Nagar
                    </span>
                  </div>
                  <span className="text-xs font-mono font-bold px-2 py-0.5 rounded-full bg-slate-800 text-orange-300 border border-slate-700">
                    SPaT Live
                  </span>
                </div>
                <div className="flex items-center justify-between bg-slate-950/80 p-3 rounded-xl border border-slate-800">
                  <div>
                    <div className="text-sm font-black text-white">
                      {isRed ? "Signal is RED — Approaching Stop" : "Signal is GREEN — Maintain Pace"}
                    </div>
                    <div className="text-xs text-slate-400 mt-0.5">
                      Recommended GLOSA Speed: <span className="text-orange-400 font-bold">{glosaSpeed} km/h</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-black text-amber-400 font-mono digits">
                      {signalCountdown}s
                    </div>
                    <div className="text-[10px] text-slate-400 uppercase font-semibold">Change In</div>
                  </div>
                </div>
              </motion.div>
            )}

            {/* POP-UP 2: Road Obstacle / Pothole Warning */}
            {activePopup === 'hazard' && (
              <motion.div
                key="hazard-popup"
                initial={{ y: 40, opacity: 0, scale: 0.92 }}
                animate={{ y: 0, opacity: 1, scale: 1 }}
                exit={{ y: 30, opacity: 0, scale: 0.92 }}
                className="w-full max-w-md bg-amber-950/95 backdrop-blur-xl border-2 border-amber-500 shadow-2xl shadow-amber-950/60 rounded-2xl p-4 pointer-events-auto"
              >
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-amber-500/20 border border-amber-400 flex items-center justify-center shrink-0">
                    <TriangleAlert className="text-amber-400" size={24} />
                  </div>
                  <div className="flex-1">
                    <div className="text-xs font-bold text-amber-300 uppercase tracking-wide">
                      ⚠️ Road Hazard Ahead (In 120m)
                    </div>
                    <div className="text-sm font-black text-white">
                      Pothole / Road Deterioration Detected
                    </div>
                    <div className="text-xs text-amber-200/80 mt-0.5">
                      Reduce speed to <span className="font-bold text-white">25 km/h</span> and stay in middle lane.
                    </div>
                  </div>
                </div>
              </motion.div>
            )}

            {/* POP-UP 3: Critical Emergency Vehicle Preemption */}
            {activePopup === 'emergency' && (
              <motion.div
                key="emergency-popup"
                initial={{ y: 40, opacity: 0, scale: 0.92 }}
                animate={{ y: 0, opacity: 1, scale: 1 }}
                exit={{ y: 30, opacity: 0, scale: 0.92 }}
                className="w-full max-w-md bg-red-600/95 backdrop-blur-xl border-2 border-red-300 shadow-2xl shadow-red-950/80 rounded-2xl p-4 pointer-events-auto animate-pulse"
              >
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-white/20 border border-white flex items-center justify-center shrink-0">
                    <ShieldAlert className="text-white" size={24} />
                  </div>
                  <div className="flex-1 text-white">
                    <div className="text-xs font-extrabold uppercase tracking-wide text-red-100">
                      🚨 Emergency Vehicle Behind You (In 150m)
                    </div>
                    <div className="text-sm font-black text-white">
                      Please Merge Left Immediately
                    </div>
                    <div className="text-xs text-red-100/90 mt-0.5">
                      Green corridor active · Signal preemption in progress.
                    </div>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Google Maps Bottom ETA & Telemetry Bar */}
      <div className="bg-slate-900/95 backdrop-blur border-t border-slate-700/60 p-4 flex items-center justify-between z-30">
        <div className="flex items-center gap-6 text-slate-300">
          <div>
            <div className="text-2xl font-black text-white digits">
              {Math.max(1, Math.round(distanceToJunction / 25))}<span className="text-xs font-normal text-slate-400 ml-1">min</span>
            </div>
            <div className="text-[11px] text-slate-500 font-semibold">{Math.round(distanceToJunction)} m remaining</div>
          </div>
          <div className="h-8 w-[1px] bg-slate-800" />
          <div>
            <div className="text-2xl font-black text-white digits">
              {Math.round(speed)}<span className="text-xs font-normal text-slate-400 ml-1 font-sans">km/h</span>
            </div>
            <div className="text-[11px] text-slate-500 font-semibold">Speedometer</div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="px-3.5 py-2 bg-slate-800/80 rounded-xl border border-slate-700 text-xs font-bold flex items-center gap-2 text-slate-300">
            <MapPin size={15} className="text-red-400" /> JN-1 Corridor
          </div>
          <div className="px-4 py-2 bg-amber-500/20 text-amber-300 border border-amber-500/30 rounded-xl text-xs font-bold flex items-center gap-1.5">
            <Sparkles size={14} /> AI Nav Synced
          </div>
        </div>
      </div>
    </div>
  )
}

