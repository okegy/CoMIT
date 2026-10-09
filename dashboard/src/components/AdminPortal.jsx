import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { AlertTriangle, Car, Clock, ShieldAlert, CheckCircle, Video, Camera } from 'lucide-react'

// Mock data generator for demo purposes
const generateViolation = (id) => {
  const types = ['SPEEDING', 'RED_LIGHT', 'WRONG_WAY']
  const type = types[Math.floor(Math.random() * types.length)]
  let speed = 40 + Math.random() * 40
  if (type === 'SPEEDING') speed = 75 + Math.random() * 30
  
  return {
    id: `V-${1000 + id}`,
    timestamp: new Date().toLocaleTimeString(),
    type,
    plate: `PY-01-${Math.floor(1000 + Math.random() * 9000)}`,
    speed: speed.toFixed(1),
    status: 'PENDING_REVIEW',
    confidence: (85 + Math.random() * 14).toFixed(1)
  }
}

export default function AdminPortal() {
  const [violations, setViolations] = useState([])
  const [selected, setSelected] = useState(null)

  // Simulate incoming violations from the vision node
  useEffect(() => {
    // Initial load
    setViolations(Array.from({ length: 4 }).map((_, i) => generateViolation(i)))
    
    // Add new violation every 8 seconds
    const interval = setInterval(() => {
      setViolations(prev => [generateViolation(prev.length), ...prev].slice(0, 15))
    }, 8000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
      {/* Violation Feed */}
      <div className="lg:col-span-2 space-y-4">
        <div className="card h-full flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wide flex items-center gap-2">
              <ShieldAlert size={16} className="text-sky-400" /> Live Enforcement Feed
            </h3>
            <span className="text-xs bg-red-500/20 text-red-300 px-2 py-1 rounded-full border border-red-500/30 flex items-center gap-1 animate-pulse">
              <div className="w-1.5 h-1.5 rounded-full bg-red-400" /> LIVE CAPTURE
            </span>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="text-slate-500 border-b border-slate-700/50">
                  <th className="pb-2 font-medium">Time</th>
                  <th className="pb-2 font-medium">Plate</th>
                  <th className="pb-2 font-medium">Infraction</th>
                  <th className="pb-2 font-medium">Speed</th>
                  <th className="pb-2 font-medium">Action</th>
                </tr>
              </thead>
              <tbody>
                <AnimatePresence>
                  {violations.map((v, idx) => (
                    <motion.tr 
                      key={v.id}
                      initial={{ opacity: 0, x: -10, backgroundColor: 'rgba(56, 189, 248, 0.1)' }}
                      animate={{ opacity: 1, x: 0, backgroundColor: 'transparent' }}
                      transition={{ duration: 0.5 }}
                      className={`border-b border-slate-800/50 hover:bg-slate-800/30 cursor-pointer transition-colors ${selected?.id === v.id ? 'bg-slate-800/50' : ''}`}
                      onClick={() => setSelected(v)}
                    >
                      <td className="py-3 text-slate-400 font-mono text-xs">{v.timestamp}</td>
                      <td className="py-3 font-mono font-bold text-slate-200">{v.plate}</td>
                      <td className="py-3">
                        <span className={`text-[10px] px-2 py-1 rounded font-bold uppercase tracking-wide ${
                          v.type === 'SPEEDING' ? 'bg-amber-500/20 text-amber-300' : 
                          v.type === 'RED_LIGHT' ? 'bg-red-500/20 text-red-300' : 
                          'bg-violet-500/20 text-violet-300'
                        }`}>
                          {v.type.replace('_', ' ')}
                        </span>
                      </td>
                      <td className="py-3 text-slate-300 digits">{v.speed} km/h</td>
                      <td className="py-3">
                        <button className="text-xs bg-sky-500/20 text-sky-300 hover:bg-sky-500/40 px-3 py-1 rounded transition-colors">
                          Review
                        </button>
                      </td>
                    </motion.tr>
                  ))}
                </AnimatePresence>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Review Panel */}
      <div className="space-y-4">
        <div className="card h-[400px] flex flex-col relative overflow-hidden">
          <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wide mb-3">Evidentiary Review</h3>
          
          {selected ? (
            <motion.div 
              key={selected.id}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="flex-1 flex flex-col"
            >
              <div className="w-full h-32 bg-slate-900 rounded-lg border border-slate-700 flex items-center justify-center relative overflow-hidden mb-4 group">
                <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1549317661-bd32c8ce0db2?auto=format&fit=crop&q=80&w=600')] bg-cover bg-center opacity-40 mix-blend-luminosity grayscale group-hover:grayscale-0 transition-all duration-500" />
                <div className="absolute inset-0 bg-sky-900/20" />
                
                {/* AI Bounding Box Overlay */}
                <div className="absolute w-24 h-16 border-2 border-red-500/70 rounded bg-red-500/10 flex items-end justify-center pb-1">
                  <span className="text-[9px] font-mono font-bold bg-red-500 text-white px-1 rounded-sm shadow">
                    {selected.confidence}% {selected.type}
                  </span>
                </div>
                
                <div className="absolute bottom-2 left-2 text-[10px] font-mono text-white/70 bg-black/50 px-1 rounded">
                  CAM_JN1_NORTH
                </div>
              </div>
              
              <div className="space-y-2 text-sm">
                <div className="flex justify-between border-b border-slate-700/50 pb-1">
                  <span className="text-slate-500">Incident ID</span>
                  <span className="font-mono text-slate-300">{selected.id}</span>
                </div>
                <div className="flex justify-between border-b border-slate-700/50 pb-1">
                  <span className="text-slate-500">Time</span>
                  <span className="font-mono text-slate-300">{selected.timestamp}</span>
                </div>
                <div className="flex justify-between border-b border-slate-700/50 pb-1">
                  <span className="text-slate-500">Plate (ANPR)</span>
                  <span className="font-mono font-bold text-emerald-400">{selected.plate}</span>
                </div>
                <div className="flex justify-between border-b border-slate-700/50 pb-1">
                  <span className="text-slate-500">Recorded Speed</span>
                  <span className={`font-mono font-bold ${selected.speed > 60 ? 'text-red-400' : 'text-slate-300'}`}>
                    {selected.speed} km/h
                  </span>
                </div>
              </div>
              
              <div className="mt-auto grid grid-cols-2 gap-2 pt-4">
                <button className="flex items-center justify-center gap-2 bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/30 py-2 rounded-lg text-xs font-bold uppercase transition-colors">
                  <CheckCircle size={14} /> Issue Ticket
                </button>
                <button className="flex items-center justify-center gap-2 bg-slate-700/50 hover:bg-slate-700/80 text-slate-300 border border-slate-600 py-2 rounded-lg text-xs font-bold uppercase transition-colors">
                  Dismiss
                </button>
              </div>
            </motion.div>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-slate-500">
              <Camera size={32} className="mb-2 opacity-50" />
              <p className="text-xs text-center px-4">Select an infraction from the feed to review evidence and issue citations.</p>
            </div>
          )}
        </div>
        
        <div className="card text-xs text-slate-400">
          <p className="flex items-start gap-2">
            <AlertTriangle size={14} className="text-amber-400 shrink-0 mt-0.5" />
            This portal receives velocity and trajectory data directly from the ByteTrack AI vision node. Red-light violations are cross-referenced with the SPaT phase data.
          </p>
        </div>
      </div>
    </div>
  )
}
