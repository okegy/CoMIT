import { useEffect, useMemo, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Video, TriangleAlert, HardHat, ShieldAlert, Radio, Hospital, Siren, Cpu, Eye, ScanLine, Wifi } from 'lucide-react'

/* ---------------------------------------------------------------------------
 * City Network map — a real road-network view of the CoMIT corridor.
 *
 * Feeding a scenario here drives the REAL backend when it is running:
 *   Feed: Ambulance  -> publishes an authenticated v2x/cmd/emergency_ping,
 *                       the trained PPO policy + SafetyChecker preempt the
 *                       junction, and the emergency prop reflects live events
 *                       (ping_accepted -> PREEMPT -> CLEARED).
 * The map animates the same chain: ambulance drives W -> J3 -> J2 -> J1 ->
 * Hospital; junctions flip green ahead of it (green corridor), V2V ripples
 * broadcast to surrounding vehicles, warned cars pull over and flash.
 * ------------------------------------------------------------------------- */

const W = 960, H = 540
const J = [ // junctions: id, x, y
  { id: 'J1', x: 200, y: 170 }, { id: 'J2', x: 480, y: 170 }, { id: 'J3', x: 760, y: 170 },
  { id: 'J4', x: 200, y: 370 }, { id: 'J5', x: 480, y: 370 }, { id: 'J6', x: 760, y: 370 },
]
const HOSPITAL = { x: 875, y: 80 }
// ambulance corridor: west edge -> J5 -> J2 -> J1... route passes J5(480,370), J2(480,170), J1? no.
// Path: enter west on y=370 -> J5 -> north to J2 -> east to J3(x760,170) -> north to hospital
const ROUTE = `M -40 370 L 480 370 L 480 170 L 760 170 L 760 80 L 860 80`
const ROUTE_LEN = 520 + 200 + 280 + 90 + 100 // ≈ 1190
// progress fraction of each corridor junction along the route
const CORRIDOR_JUNCTIONS = [
  { id: 'J5', at: 520 / ROUTE_LEN },
  { id: 'J2', at: 720 / ROUTE_LEN },
  { id: 'J3', at: 1000 / ROUTE_LEN },
]

const CARS = [
  // corridor traffic (westbound + eastbound on the ambulance road) — these get warned
  { id: 'c1', path: 'M 1000 350 L -40 350', dur: 26, t: 'car', warned: true },
  { id: 'c2', path: 'M 1000 390 L -40 390', dur: 32, t: 'bus', warned: true },
  { id: 'c3', path: 'M -40 345 L 1000 345', dur: 24, t: 'car', warned: true },
  { id: 'c4', path: 'M 700 388 L -40 388', dur: 30, t: 'moto', warned: true },
  { id: 'c5', path: 'M 1000 352 L -40 352', dur: 22, t: 'truck', warned: true },
  // cross traffic
  { id: 'c6', path: 'M -40 155 L 1000 155', dur: 28, t: 'car', warned: false },
  { id: 'c7', path: 'M 1000 185 L -40 185', dur: 33, t: 'car', warned: false },
  { id: 'c8', path: 'M 185 -40 L 185 580', dur: 25, t: 'car', warned: false },
  { id: 'c9', path: 'M 215 580 L 215 -40', dur: 29, t: 'moto', warned: false },
  { id: 'c10', path: 'M 465 -40 L 465 580', dur: 27, t: 'bus', warned: false },
  { id: 'c11', path: 'M 495 580 L 495 -40', dur: 31, t: 'car', warned: false },
  { id: 'c12', path: 'M 745 -40 L 745 580', dur: 26, t: 'car', warned: false },
  { id: 'c13', path: 'M 775 580 L 775 -40', dur: 34, t: 'truck', warned: false },
  { id: 'c14', path: 'M -40 362 L 1000 362', dur: 35, t: 'auto', warned: true },
]
const CAR_COLOR = { car: '#38bdf8', moto: '#ffb800', bus: '#ffb800', truck: '#a3a3a3', auto: '#ffb800' }

const STAGES = [
  { id: 'FEED', icon: Video, label: 'Scenario feed' },
  { id: 'DETECT', icon: Eye, label: 'YOLO detect' },
  { id: 'DECIDE', icon: Cpu, label: 'PPO + Safety' },
  { id: 'BROADCAST', icon: Wifi, label: 'SPaT / V2X' },
]

export default function CityGrid({ emergency, onFeedAmbulance, spat, publish }) {
  const [amb, setAmb] = useState(null)          // {start: ts}
  const [progress, setProgress] = useState(0)
  const [hazard, setHazard] = useState(null)    // {type, x, y, label}
  const [stage, setStage] = useState('FEED')
  const rafRef = useRef()
  const animRef = useRef({ t0: 0, dur: 12000 })
  const liveMode = emergency?.event === 'PREEMPT' || emergency?.event === 'ping_accepted'

    // ---------------- ambulance run loop (12s across the corridor) ------------
  useEffect(() => {
    if (liveMode && !amb) {
      setAmb({ start: Date.now() })
    }
  }, [liveMode, amb])

  useEffect(() => {
    if (!amb) { setProgress(0); return }
    const tick = (ts) => {
      const p = Math.min((ts - animRef.current.t0) / animRef.current.dur, 1)
      setProgress(p)
      // pipeline stages follow the run
      setStage(p < 0.04 ? 'FEED' : p < 0.12 ? 'DETECT' : p < 0.22 ? 'DECIDE' : 'BROADCAST')
      if (p < 1) rafRef.current = requestAnimationFrame(tick)
      else setTimeout(() => { setAmb(null); setStage('FEED') }, 1500)
    }
    animRef.current.t0 = performance.now()
    rafRef.current = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(rafRef.current)
  }, [amb])

  const feedAmbulance = () => {
    if (amb || liveMode) return
    setAmb({ start: Date.now() })
    // drive the REAL pipeline too (trained model + safety checker)
    onFeedAmbulance?.()
  }
    const feedHazard = (type) => {
    const spots = {
      construction: { x: 620, y: 370, label: 'ROAD WORKS � RIGHT LANE CLOSED' },
      pothole: { x: 330, y: 170, label: 'SEVERE POTHOLE � CENTER LANE' },
    }
    setHazard({ type, ...spots[type] })
    if (publish) publish('v2x/alert/hazard', JSON.stringify({ type, approach: 'W_E' }))
    setTimeout(() => setHazard(null), 9000)
  }

  // junction signal state: green if ambulance within 18% progress ahead of it
  const greenFor = (jid) => {
    if (!amb && !liveMode) return 'red'
    const cj = CORRIDOR_JUNCTIONS.find(c => c.id === jid)
    if (!cj) return 'red'
    return progress >= cj.at - 0.16 && progress <= cj.at + 0.10 ? 'green' : 'red'
  }
  const corridorOn = !!amb || liveMode
  const warnedActive = amb ? progress > 0.08 : liveMode

  const ambPos = useMemo(() => {
    // piecewise-linear point along ROUTE by progress
    const pts = [[-40, 370], [480, 370], [480, 170], [760, 170], [760, 80], [860, 80]]
    const segs = [520, 200, 280, 90, 100]
    let d = progress * ROUTE_LEN
    for (let i = 0; i < segs.length; i++) {
      if (d <= segs[i]) {
        const f = d / segs[i]
        return [pts[i][0] + (pts[i + 1][0] - pts[i][0]) * f,
                pts[i][1] + (pts[i + 1][1] - pts[i][1]) * f]
      }
      d -= segs[i]
    }
    return pts.at(-1)
  }, [progress])

  return (
    <div className="flex flex-col gap-4">
      {/* scenario feed controls + pipeline */}
      <div className="card p-4">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
          <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wide flex items-center gap-2">
            <Video size={18} className="text-orange-400" /> City Network — Scenario Feed
          </h2>
          {/* live pipeline strip */}
          <div className="flex items-center gap-1.5">
            {STAGES.map((s, i) => {
              const active = stage === s.id
              const done = STAGES.findIndex(x => x.id === stage) > i
              return (
                <div key={s.id} className="flex items-center gap-1.5">
                  <div className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border text-[10px] font-bold uppercase tracking-wide transition-all duration-300 ${
                    active ? 'bg-orange-500/25 border-orange-400/60 text-orange-200 shadow-[0_0_12px_rgba(56,189,248,0.4)]'
                    : done ? 'bg-amber-500/15 border-amber-500/40 text-amber-300'
                    : 'bg-slate-900/60 border-slate-700/50 text-slate-500'}`}>
                    <s.icon size={12} className={active ? 'animate-pulse' : ''} /> {s.label}
                  </div>
                  {i < STAGES.length - 1 && <span className="text-slate-600 text-xs">▸</span>}
                </div>
              )
            })}
          </div>
        </div>
        <div className="flex flex-wrap gap-3">
          <button onClick={feedAmbulance} disabled={corridorOn}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-red-600/20 hover:bg-red-600/40 disabled:opacity-40 border border-red-500/50 text-red-300 rounded-xl transition-colors text-sm font-bold">
            <Siren size={16} className={corridorOn ? 'animate-pulse' : ''} /> Feed: Ambulance → Hospital corridor
          </button>
          <button onClick={() => feedHazard('construction')}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-amber-600/20 hover:bg-amber-600/40 border border-amber-500/50 text-amber-300 rounded-xl transition-colors text-sm font-bold">
            <HardHat size={16} /> Feed: Construction
          </button>
          <button onClick={() => feedHazard('pothole')}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-orange-600/20 hover:bg-orange-600/40 border border-orange-500/50 text-orange-300 rounded-xl transition-colors text-sm font-bold">
            <ShieldAlert size={16} /> Feed: Pothole
          </button>
        </div>
        {liveMode && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
            className="mt-3 text-xs text-amber-300 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
            Live pipeline engaged — trained PPO policy pre-empting junction JN-1 (SPaT mode: {spat?.mode || '…'})
          </motion.div>
        )}
      </div>

      {/* THE MAP */}
      <div className="card !p-0 overflow-hidden relative">
        <svg viewBox={`0 0 ${W} ${H}`} className="w-full" style={{ background: 'linear-gradient(160deg, #060b18, #0a1322)' }}>
          <defs>
            <pattern id="citygrid" width="48" height="48" patternUnits="userSpaceOnUse">
              <path d="M 48 0 L 0 0 0 48" fill="none" stroke="rgba(148,163,184,0.05)" strokeWidth="1" />
            </pattern>
            <filter id="glow"><feGaussianBlur stdDeviation="3" result="b" />
              <feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge></filter>
          </defs>
          <rect width={W} height={H} fill="url(#citygrid)" />

          {/* city blocks (subtle buildings) */}
          {[[60, 60, 110, 80], [260, 60, 160, 80], [540, 60, 120, 80],
            [60, 230, 110, 110], [260, 230, 160, 110], [540, 230, 120, 110],
            [60, 430, 110, 70], [260, 430, 160, 70], [540, 430, 120, 70],
            [820, 230, 100, 110], [820, 430, 100, 70]].map(([x, y, w2, h2], i) => (
            <g key={i}>
              <rect x={x} y={y} width={w2} height={h2} rx={6} fill="rgba(30,41,59,0.55)" stroke="rgba(148,163,184,0.12)" />
              {i % 3 === 0 && <rect x={x + 8} y={y + 8} width={w2 - 16} height={h2 - 16} rx={3} fill="rgba(56,189,248,0.04)" />}
            </g>
          ))}

          {/* roads */}
          {[170, 370].map(y => (
            <g key={y}>
              <rect x={0} y={y - 26} width={W} height={52} fill="#101b2e" />
              <line x1={0} y1={y} x2={W} y2={y} stroke="#24334d" strokeWidth={2} strokeDasharray="18 14" />
            </g>
          ))}
          {[200, 480, 760].map(x => (
            <g key={x}>
              <rect x={x - 26} y={0} width={52} height={H} fill="#101b2e" />
              <line x1={x} y1={0} x2={x} y2={H} stroke="#24334d" strokeWidth={2} strokeDasharray="18 14" />
            </g>
          ))}

          {/* green corridor overlay */}
          <AnimatePresence>
            {corridorOn && (
              <motion.path d={ROUTE} fill="none" stroke="#22c55e" strokeWidth={18}
                strokeLinecap="round" opacity={0.28}
                initial={{ pathLength: 0 }} animate={{ pathLength: progress || 0.001 }}
                transition={{ duration: 0.2 }} />
            )}
          </AnimatePresence>

          {/* junctions + signals */}
          {J.map(j => {
            const g = greenFor(j.id)
            return (
              <g key={j.id}>
                <rect x={j.x - 30} y={j.y - 30} width={60} height={60} rx={8} fill="#1c2b45" stroke="#2b3d5c" />
                <circle cx={j.x} cy={j.y} r={7} fill={g === 'green' ? '#22c55e' : '#ef4444'}
                  filter="url(#glow)" className={g === 'green' ? 'glow-green' : 'glow-red'} />
                <text x={j.x} y={j.y + 46} textAnchor="middle" fontSize={10} fill="#64748b" fontFamily="Rajdhani" fontWeight={700}>
                  {j.id}
                </text>
                {/* V2V broadcast ripple when ambulance passes */}
                {corridorOn && greenFor(j.id) === 'green' && (
                  <>
                    <motion.circle cx={j.x} cy={j.y} r={12} fill="none" stroke="#38bdf8" strokeWidth={2}
                      initial={{ r: 12, opacity: 0.9 }} animate={{ r: 120, opacity: 0 }}
                      transition={{ repeat: Infinity, duration: 1.8 }} />
                    <motion.circle cx={j.x} cy={j.y} r={12} fill="none" stroke="#38bdf8" strokeWidth={1.5}
                      initial={{ r: 12, opacity: 0.7 }} animate={{ r: 120, opacity: 0 }}
                      transition={{ repeat: Infinity, duration: 1.8, delay: 0.6 }} />
                  </>
                )}
              </g>
            )
          })}

          {/* hospital */}
          <g transform={`translate(${HOSPITAL.x - 34}, ${HOSPITAL.y - 22})`}>
            <rect width={68} height={44} rx={8} fill="#0f2a1e" stroke="#ffb800" strokeWidth={1.5} />
            <path d="M 26 12 h 16 v 8 h 8 v 16 h -8 v 8 ... " display="none" />
            <text x={34} y={27} textAnchor="middle" fill="#ffb800" fontSize={18} fontWeight="bold">✚</text>
            <text x={34} y={39} textAnchor="middle" fill="#ffb800" fontSize={8} fontFamily="Rajdhani" fontWeight={700}>HOSPITAL</text>
          </g>

          {/* civilian vehicles */}
          {CARS.map(c => (
            <g key={c.id}>
              <path id={`p-${c.id}`} d={c.path} fill="none" stroke="none" />
              <g>
                <animateMotion dur={`${c.dur}s`} repeatCount="indefinite" begin={`${-(c.dur * 0.37).toFixed(1)}s`}>
                  <mpath href={`#p-${c.id}`} />
                </animateMotion>
                {/* warned halo */}
                {c.warned && warnedActive && (
                  <motion.circle r={9} fill="none" stroke="#f59e0b" strokeWidth={1.5}
                    animate={{ r: [7, 10, 7], opacity: [0.9, 0.4, 0.9] }}
                    transition={{ repeat: Infinity, duration: 1.1 }} />
                )}
                <rect x={-5} y={-8} width={10} height={16} rx={2.5}
                  fill={CAR_COLOR[c.t]} opacity={c.warned && warnedActive ? 0.75 : 0.95} />
                {c.warned && warnedActive && (
                  <g transform="translate(7, -10)">
                    <circle r={6} fill="#78350f" stroke="#f59e0b" strokeWidth={1} />
                    <text y={2.5} textAnchor="middle" fontSize={8} fill="#ffb800">⚠</text>
                  </g>
                )}
              </g>
            </g>
          ))}

          {/* hazard marker */}
          <AnimatePresence>
            {hazard && (
              <motion.g initial={{ opacity: 0, scale: 0.6 }} animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0 }} style={{ originX: `${hazard.x}px`, originY: `${hazard.y}px` }}>
                <motion.circle cx={hazard.x} cy={hazard.y} r={26} fill="rgba(249,115,22,0.15)" stroke="#f97316" strokeWidth={2}
                  animate={{ r: [22, 30, 22] }} transition={{ repeat: Infinity, duration: 1.4 }} />
                <text x={hazard.x} y={hazard.y + 4} textAnchor="middle" fontSize={18}>⚠️</text>
                <text x={hazard.x} y={hazard.y + 44} textAnchor="middle" fontSize={10} fill="#fdba74"
                  fontFamily="Rajdhani" fontWeight={700}>{hazard.label}</text>
                {/* warning ripple upstream */}
                <motion.circle cx={hazard.x} cy={hazard.y} r={30} fill="none" stroke="#f97316" strokeWidth={1.5}
                  initial={{ r: 30, opacity: 0.8 }} animate={{ r: 150, opacity: 0 }}
                  transition={{ repeat: Infinity, duration: 2 }} />
              </motion.g>
            )}
          </AnimatePresence>

          {/* THE AMBULANCE */}
          <AnimatePresence>
            {(amb || liveMode) && (
              <motion.g
                animate={{ x: ambPos[0], y: ambPos[1] }}
                transition={{ type: 'tween', duration: 0.12, ease: 'linear' }}
                exit={{ opacity: 0 }}>
                <motion.circle r={16} fill="rgba(255,127,80,0.25)" stroke="#ff7f50" strokeWidth={1.5}
                  animate={{ r: [12, 20, 12] }} transition={{ repeat: Infinity, duration: 0.8 }} />
                <rect x={-7} y={-12} width={14} height={24} rx={3} fill="#ff7f50" stroke="#fecaca" strokeWidth={1} />
                <rect x={-5} y={-7} width={10} height={14} rx={1.5} fill="white" />
                <motion.circle cy={-10} r={2.5} fill="#38bdf8"
                  animate={{ opacity: [1, 0.2, 1] }} transition={{ repeat: Infinity, duration: 0.35 }} />
                <text y={-18} textAnchor="middle" fontSize={9} fill="#fca5a5" fontFamily="Orbitron" fontWeight={700}>
                  AMB {Math.round(progress * 100)}%
                </text>
              </motion.g>
            )}
          </AnimatePresence>

          {/* legend */}
          <g transform="translate(16, 500)" fontFamily="Rajdhani" fontSize={10}>
            {Object.entries(CAR_COLOR).map(([t, c], i) => (
              <g key={t} transform={`translate(${i * 74}, 0)`}>
                <rect x={0} y={-7} width={9} height={14} rx={2} fill={c} />
                <text x={14} y={4} fill="#94a3b8" fontWeight={600}>{t}</text>
              </g>
            ))}
            <g transform="translate(380, 0)">
              <rect x={0} y={-7} width={9} height={14} rx={2} fill="#ff7f50" />
              <text x={14} y={4} fill="#94a3b8" fontWeight={600}>ambulance</text>
            </g>
            <g transform="translate(490, 0)">
              <line x1={0} y1={-5} x2={22} y2={-5} stroke="#ffb800" strokeWidth={5} strokeLinecap="round" opacity={0.5} />
              <text x={28} y={0} fill="#94a3b8" fontWeight={600}>green corridor</text>
            </g>
          </g>
        </svg>

        {/* map HUD */}
        <div className="absolute top-3 right-3 flex flex-col gap-2 items-end">
          <div className="glass-strong px-3 py-1.5 rounded-lg text-[10px] font-mono text-slate-300 flex items-center gap-2">
            <Radio size={11} className="text-amber-400" />
            {corridorOn ? 'V2V BROADCASTING' : 'NETWORK IDLE'}
            <span className={`w-1.5 h-1.5 rounded-full ${corridorOn ? 'bg-red-400 animate-pulse' : 'bg-slate-500'}`} />
          </div>
          {corridorOn && (
            <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }}
              className="glass-strong px-3 py-2 rounded-lg text-[10px] text-red-200 max-w-[240px]">
              <b className="text-red-300">⚠ AMBULANCE IN CORRIDOR</b><br />
              J5→J2→J3 signals green · corridor vehicles merging left
            </motion.div>
          )}
        </div>
      </div>

      <p className="text-xs text-slate-500 text-center">
        Feeding the ambulance scenario publishes an authenticated priority ping on the real MQTT fabric —
        the trained PPO policy pre-empts junction JN-1 through the SafetyChecker while this map visualises the
        V2V cascade to every vehicle on the corridor. Hazards (construction / pothole) demonstrate edge-camera
        detection broadcasts.
      </p>
    </div>
  )
}







