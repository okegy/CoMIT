import { useEffect, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Battery, Signal as SignalIcon, Bluetooth, Thermometer, Volume2,
         Radio, TriangleAlert, Coins } from 'lucide-react'

const polar = (cx, cy, r, deg) => {
  const rad = (deg * Math.PI) / 180
  return [cx + r * Math.cos(rad), cy + r * Math.sin(rad)]
}
const arcPath = (cx, cy, r, a0, a1) => {
  const [x0, y0] = polar(cx, cy, r, a0)
  const [x1, y1] = polar(cx, cy, r, a1)
  const large = Math.abs(a1 - a0) > 180 ? 1 : 0
  return `M ${x0} ${y0} A ${r} ${r} 0 ${large} 1 ${x1} ${y1}`
}

const START = -210, END = 30   // 240° sweep, like a real cluster

function Gauge({ value, max, major, redFrom, centerTop, centerMain, centerSub,
                 size = 250, accent = '#7dd3fc' }) {
  const cx = 100, cy = 100, r = 78
  const angle = START + (Math.min(value, max) / max) * (END - START)
  const ticks = []
  for (let v = 0; v <= max; v += major) {
    const a = START + (v / max) * (END - START)
    const [x1, y1] = polar(cx, cy, r - 2, a)
    const [x2, y2] = polar(cx, cy, r - 12, a)
    const [tx, ty] = polar(cx, cy, r - 24, a)
    const red = redFrom != null && v >= redFrom
    ticks.push(
      <g key={v}>
        <line x1={x1} y1={y1} x2={x2} y2={y2}
          stroke={red ? '#ff7f50' : '#94a3b8'} strokeWidth={2} />
        <text x={tx} y={ty} textAnchor="middle" dominantBaseline="middle"
          fontSize={10} fill={red ? '#ff7f50' : '#cbd5e1'} fontFamily="Rajdhani" fontWeight={600}>
          {v}
        </text>
      </g>
    )
  }
  return (
    <svg viewBox="0 0 200 200" width={size} height={size}>
      <defs>
        <radialGradient id={`face-${accent.slice(1)}`} cx="50%" cy="42%">
          <stop offset="0%" stopColor="#0f172a" />
          <stop offset="100%" stopColor="#020617" />
        </radialGradient>
      </defs>
      <circle cx={cx} cy={cy} r={94} fill={`url(#face-${accent.slice(1)})`}
        stroke="rgba(148,163,184,0.25)" strokeWidth={1.5} />
      <circle cx={cx} cy={cy} r={94} fill="none" stroke={accent} strokeOpacity={0.15} strokeWidth={6} />
      {/* red zone */}
      {redFrom != null && (
        <path d={arcPath(cx, cy, r - 5, START + (redFrom / max) * (END - START), END)}
          stroke="#ff7f50" strokeWidth={5} fill="none" strokeLinecap="round" opacity={0.85} style={{filter: 'drop-shadow(0 0 4px #ff7f50)'}} />
      )}
      {/* progress arc */}
      <path d={arcPath(cx, cy, r - 5, START, angle)}
        stroke={accent} strokeWidth={5} fill="none" strokeLinecap="round" opacity={0.9} style={{filter: `drop-shadow(0 0 6px ${accent})`}} />
      {ticks}
      {/* needle */}
      <motion.g animate={{ rotate: angle }} transition={{ type: 'spring', stiffness: 60, damping: 12 }}
        style={{ originX: '100px', originY: '100px' }}>
        <line x1={cx} y1={cy + 10} x2={cx} y2={cy - r + 16}
          stroke={accent} strokeWidth={3} strokeLinecap="round" style={{filter: `drop-shadow(0 0 4px ${accent})`}} />
        <line x1={cx} y1={cy + 10} x2={cx} y2={cy + 2}
          stroke="#ff7f50" strokeWidth={3} strokeLinecap="round" />
      </motion.g>
      <circle cx={cx} cy={cy} r={7} fill="#1e293b" stroke={accent} strokeWidth={1.5} />
      {centerTop}
      {centerMain}
      {centerSub}
    </svg>
  )
}

function TrafficLamp({ color, on }) {
  return (
    <div className={`w-6 h-6 rounded-full border ${on ? 'glow-amber' : ''}`}
      style={{
        background: on ? color : 'rgba(30,41,59,0.9)',
        borderColor: on ? color : 'rgba(100,116,139,0.4)',
        boxShadow: on ? `0 0 14px ${color}` : 'none',
      }} />
  )
}

const STATE_TEXT = {
  red: { text: "Please wait — It's Red", color: '#ff7f50', lamp: '#ff7f50' },
  yellow: { text: 'Signal changing — hold', color: '#ffb800', lamp: '#ffb800' },
  green: { text: 'Go — Green now', color: '#ffb800', lamp: '#ffb800' },
}

export default function Cluster({ ego }) {
  const [tokens, setTokens] = useState(1450)
  const [rewarded, setRewarded] = useState(false)
  const e = ego || {}
  const speed = e.speed_kmh ?? 0

  useEffect(() => {
    // Gamification Logic: Reward driver for yielding to ambulance
    if (e.emergency && speed < 5 && !rewarded) {
      setTimeout(() => {
        setTokens(t => t + 15)
        setRewarded(true)
      }, 2000)
    } else if (!e.emergency) {
      setRewarded(false)
    }
  }, [e.emergency, speed, rewarded])

  const st = STATE_TEXT[e.group_state || 'red']
  const counting = e.group_state !== 'green' && e.time_to_green != null
  const clock = (() => {
    const t = 16 * 3600 + Math.floor(e.sim_time ?? 0)
    return `${String(Math.floor(t / 3600)).padStart(2, '0')}:${String(Math.floor((t % 3600) / 60)).padStart(2, '0')}`
  })()
  const passed = e.dist_m != null && e.dist_m <= 0.5

  return (
    <div className="relative rounded-3xl overflow-hidden border border-slate-700/50"
      style={{ background: 'linear-gradient(160deg, #0b1220 0%, #05080f 70%)', minHeight: 560 }}>
      <div className="scanline" />
      {/* top status bar */}
      <div className="flex items-center justify-between px-5 py-2.5 text-xs text-slate-400 border-b border-slate-800/80">
        <div className="flex items-center gap-3">
          <Battery size={14} className="text-[#ffb800]" />
          <span className="digits">410 km</span>
          <Bluetooth size={14} className="text-orange-400" />
          <span>CoMIT CV-01 | Connected</span>
        </div>
        <div className="flex items-center gap-3">
          <SignalIcon size={14} className="text-orange-400" />
          <span className="digits">{clock}</span>
          <Thermometer size={14} /> <span className="digits">+30.5°C</span>
        </div>
      </div>

      {/* emergency overlay */}
      <AnimatePresence>
        {e.emergency && (
          <motion.div initial={{ y: -40, opacity: 0 }} animate={{ y: 0, opacity: 1 }}
            exit={{ y: -40, opacity: 0 }}
            className="absolute top-12 left-1/2 -translate-x-1/2 z-20">
            <div className="pulse-ring flex items-center gap-2 px-5 py-2.5 rounded-xl
              bg-red-950/90 border border-[#ff7f50] text-[#ff7f50] font-bold text-sm shadow-[0_0_15px_rgba(255,127,80,0.4)]">
              <TriangleAlert size={16} className="glow-coral" />
              AMBULANCE APPROACHING — CLEAR LEFT LANE
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* gamification wallet */}
      <div className="absolute top-16 left-6 z-20 flex flex-col gap-2">
        <div className="bg-slate-900/60 backdrop-blur-md border border-slate-700/50 rounded-xl p-3 shadow-lg">
          <div className="flex items-center gap-2 text-xs font-bold uppercase text-slate-400 mb-1">
            <Coins size={14} className="text-[#ffb800]" />
            Driver Wallet
          </div>
          <div className="text-2xl font-black digits text-[#ffb800]" style={{ filter: 'drop-shadow(0 0 4px rgba(255,184,0,0.6))' }}>
            {tokens.toLocaleString()} <span className="text-[10px] text-amber-500/80">CMT</span>
          </div>
        </div>
        <AnimatePresence>
          {rewarded && (
            <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0 }}
              className="bg-amber-950/80 border border-[#ffb800] rounded-lg p-2 text-[10px] font-bold text-[#ffb800] shadow-[0_0_10px_rgba(255,184,0,0.3)]">
              +15 CMT: Yielded to Emergency
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* gauges row */}
      <div className="flex items-center justify-center gap-2 py-6 px-4">
        {/* tachometer */}
        <Gauge value={Math.min(speed / 15, 8)} max={8} major={1} redFrom={6.5} accent="#7dd3fc"
          centerTop={
            <text x={100} y={78} textAnchor="middle" fontSize={9} fill="#64748b"
              fontFamily="Rajdhani" fontWeight={600}>RPM ×1000</text>
          }
          centerMain={
            <text x={100} y={118} textAnchor="middle" fontSize={26} fill="#e2e8f0"
              fontFamily="Orbitron" fontWeight={700}>P</text>
          }
          centerSub={
            <text x={100} y={140} textAnchor="middle" fontSize={9} fill="#ffb800"
              fontFamily="Rajdhani" fontWeight={700}>READY</text>
          } />

        {/* center SPaT card */}
        <motion.div layout
          className="glass-strong glass-sheen relative mx-2 px-8 py-6 text-center min-w-[250px]">
          <div className="text-sm font-semibold text-slate-200 tracking-wide">
            {(e.signal || 'JN-1 · Anna Nagar Junction').split('·')[1] || ' Anna Nagar Junction'}
          </div>
          <div className="flex items-center justify-center gap-3 my-3">
            <div className="flex flex-col gap-1.5 p-1.5 rounded-lg bg-slate-950/70 border border-slate-700/60">
              <TrafficLamp color="#ff7f50" on={e.group_state !== 'green'} />
              <TrafficLamp color="#ffb800" on={e.group_state === 'yellow'} />
              <TrafficLamp color="#22c55e" on={e.group_state === 'green'} />
            </div>
            <div className="text-left">
              <div className="font-bold text-base leading-tight" style={{ color: st.color, filter: `drop-shadow(0 0 6px ${st.color})` }}>
                {passed ? 'Cleared — nice timing' : st.text}
              </div>
              <div className="text-xs text-slate-400 mt-0.5">
                {e.dist_m != null ? `${Math.max(e.dist_m, 0).toFixed(0)} m to stop line` : 'approaching JN-1'}
              </div>
            </div>
          </div>
          <AnimatePresence mode="popLayout">
            {counting ? (
              <motion.div key={Math.ceil(e.time_to_green / 5)}
                initial={{ scale: 1.15, opacity: 0.4 }} animate={{ scale: 1, opacity: 1 }}
                className="text-center">
                <div className="text-xs text-slate-400">Green in</div>
                <div className="digits text-5xl font-black text-orange-300 leading-none my-1" style={{ filter: 'drop-shadow(0 0 6px rgba(56,189,248,0.6))' }}>
                  {Math.ceil(e.time_to_green)}
                </div>
                <div className="text-xs text-slate-500">sec</div>
              </motion.div>
            ) : (
              <motion.div key="go" initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
                className={`digits text-4xl font-black my-2 text-slate-300`} style={e.group_state === 'green' ? { color: '#22c55e', filter: 'drop-shadow(0 0 8px #22c55e)' } : {}}>
                {passed ? '✓' : 'GO'}
              </motion.div>
            )}
          </AnimatePresence>
          <div className="mt-3 flex items-center justify-center gap-2 text-xs">
            <span className="px-2.5 py-1 rounded-lg bg-orange-500/15 text-orange-300 border border-orange-500/30 font-semibold shadow-[0_0_8px_rgba(56,189,248,0.3)]">
              GLOSA {e.advisory_kmh != null ? `${e.advisory_kmh} km/h` : '—'}
            </span>
            <span className="text-slate-400">{e.advice || 'connecting to SPaT…'}</span>
          </div>
        </motion.div>

        {/* speedometer */}
        <Gauge value={speed} max={120} major={20} redFrom={100} accent="#93c5fd"
          centerTop={
            <text x={100} y={80} textAnchor="middle" fontSize={9} fill="#64748b"
              fontFamily="Rajdhani" fontWeight={600}>km/h</text>
          }
          centerMain={
            <text x={100} y={122} textAnchor="middle" fontSize={34} fill="#f8fafc"
              fontFamily="Orbitron" fontWeight={900}>
              {Math.round(speed)}
            </text>
          }
          centerSub={
            <text x={100} y={142} textAnchor="middle" fontSize={9} fill="#64748b"
              fontFamily="Rajdhani" fontWeight={600}>
              {(e.dist_m != null && e.dist_m > 0.5) ? `ADVISORY ${e.advisory_kmh ?? '--'}` : 'CRUISE'}
            </text>
          } />
      </div>

      {/* bottom bar */}
      <div className="flex items-center justify-between px-5 py-3 text-xs text-slate-400 border-t border-slate-800/80">
        <div className="flex items-center gap-4">
          <span><span className="text-slate-500">odo</span> <span className="digits text-slate-200">4263 km</span></span>
          <span><span className="text-slate-500">trip</span> <span className="digits text-slate-200">105.4 km</span></span>
          <span className="flex items-center gap-1"><Volume2 size={13} className="text-[#ffb800]" /> voice module armed (EN · தமிழ்)</span>
        </div>
        <div className="flex items-center gap-2">
          <Radio size={13} className={e.emergency ? 'text-[#ff7f50] glow-coral' : 'text-[#ffb800]'} />
          <span style={e.emergency ? {color: '#ff7f50', fontWeight: 'bold'} : {}}>{e.emergency ? 'PREEMPTION ACTIVE' : 'SPaT link live'}</span>
        </div>
      </div>
    </div>
  )
}



