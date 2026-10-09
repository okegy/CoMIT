import { useEffect, useRef, useState } from 'react'
import { motion } from 'framer-motion'
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip, Cell } from 'recharts'
import { Ambulance, Volume2, VolumeX, ShieldAlert, Car, Clock, Leaf, Radio } from 'lucide-react'

export function KpiCards({ kpi }) {
  // real values from the backend (run_demo.py impact metrics vs fixed-time baseline)
  const items = [
    { icon: Clock, label: 'Avg Wait Reduction', value: kpi?.wait_reduction_pct != null ? `${kpi.wait_reduction_pct.toFixed(1)}%` : '—', color: 'text-sky-300' },
    { icon: Car, label: 'Traffic Density', value: kpi?.queue_total != null ? `${kpi.queue_total} queued` : '—', color: 'text-emerald-300' },
    { icon: Leaf, label: 'CO2 Saved', value: kpi?.co2_saved_kg != null ? `${kpi.co2_saved_kg.toFixed(2)} kg` : '—', color: 'text-lime-300' },
    { icon: Radio, label: 'RL Confidence', value: kpi?.rl_confidence != null ? `${(kpi.rl_confidence * 100).toFixed(1)}%` : (kpi?.controller ? 'rule-based' : '—'), color: 'text-violet-300' },
  ]
  return (
    <div className="grid grid-cols-4 gap-3">
      {items.map(it => (
        <div key={it.label} className="card !p-3 flex flex-col gap-1">
          <div className="flex items-center gap-1.5 text-xs text-slate-400"><it.icon size={13} />{it.label}</div>
          <div className={`digits text-lg font-bold ${it.color}`}>{it.value}</div>
        </div>
      ))}
    </div>
  )
}

export function QueueChart({ lanes }) {
  const data = ['N', 'S', 'E', 'W'].map(a => ({
    approach: a,
    queue: lanes?.approaches?.[a]?.queue ?? 0,
    wait: lanes?.approaches?.[a]?.wait ?? 0,
  }))
  return (
    <div className="card">
      <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wide mb-2">Live queue lengths</h3>
      <ResponsiveContainer width="100%" height={150}>
        <BarChart data={data}>
          <XAxis dataKey="approach" stroke="#64748b" fontSize={12} />
          <YAxis stroke="#64748b" width={24} fontSize={11} />
          <Tooltip contentStyle={{ background: 'rgba(15,23,42,0.95)', border: '1px solid #334155', borderRadius: 10, fontSize: 12 }} />
          <Bar dataKey="queue" radius={[6, 6, 0, 0]} minPointSize={3}>
            {data.map((d, i) => <Cell key={i} fill={d.queue > 10 ? '#dc2626' : d.queue > 5 ? '#f97316' : '#22c55e'} />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <div className="text-xs text-slate-500 text-right">queue = halted vehicles at stop line</div>
    </div>
  )
}

export function EmergencyBanner({ emergency, hazard }) {
  if (hazard && !emergency?.event) {
    return (
      <motion.div initial={{ opacity: 0, y: -14 }} animate={{ opacity: 1, y: 0 }}
        className="rounded-2xl border border-orange-500/60 bg-orange-950/70 p-4 flex items-center gap-3">
        <ShieldAlert className="text-orange-400 glow-amber" size={26} />
        <div>
          <div className="font-bold text-orange-200 flex items-center gap-2 uppercase tracking-wide">
            INFRASTRUCTURE HAZARD DETECTED — {hazard.type}
          </div>
          <div className="text-sm text-orange-300/90 font-mono">
            ▲ Approach: {hazard.approach} · Severity: {hazard.severity} · Broadcasting V2X Warning
          </div>
        </div>
      </motion.div>
    )
  }

  if (!emergency || !emergency.event) return null
  const ev = emergency
  const style = ev.event === 'PREEMPT' ? 'border-red-500/60 bg-red-950/70'
    : ev.event === 'CLEARED' ? 'border-emerald-500/60 bg-emerald-950/70'
    : 'border-slate-600 bg-slate-900/70'
  return (
    <motion.div initial={{ opacity: 0, y: -14 }} animate={{ opacity: 1, y: 0 }}
      className={`rounded-2xl border ${style} p-4 flex items-center gap-3`}>
      <Ambulance className={ev.event === 'PREEMPT' ? 'text-red-300 glow-red' : 'text-red-300'} size={26} />
      <div>
        <div className="font-bold text-red-200 flex items-center gap-2">
          {ev.event === 'PREEMPT' && <>EMERGENCY PREEMPTION — {ev.approach} approach · ETA {ev.eta}s</>}
          {ev.event === 'CLEARED' && <>CORRIDOR CLEARED — lane verified empty, restoring RL</>}
          {ev.event === 'RL_RESTORED' && <>RL CONTROL RESTORED</>}
          {ev.event === 'ping_accepted' && <>Emergency vehicle authenticated: {ev.id}</>}
          {!['PREEMPT', 'CLEARED', 'RL_RESTORED', 'ping_accepted'].includes(ev.event) && (ev.event || 'emergency')}
        </div>
        {ev.lane_clear && <div className="text-sm text-red-300/90 font-mono">▲ {ev.lane_clear} broadcast to connected vehicles</div>}
      </div>
    </motion.div>
  )
}

export function VoiceConsole({ voice, events, spat }) {
  const [enabled, setEnabled] = useState(true)
  const [playing, setPlaying] = useState(false)
  const audioRef = useRef(null)

  useEffect(() => {
    if (voice && enabled) {
      setPlaying(true)
      audioRef.current = new Audio(voice.ta)
      audioRef.current.onended = () => setPlaying(false)
      audioRef.current.play().catch(() => setPlaying(false))
    }
  }, [voice])

  const speakNav = () => {
    if (!('speechSynthesis' in window)) return
    const red = (spat?.states || []).find(s => s.event_state === 3)
    const ttg = red?.min_end_time ?? 15
    const speed = Math.min(13.9, 60 / Math.max(ttg, 0.5)) * 3.6
    
    let text = `Approaching smart intersection. Turn right ahead. `
    if (ttg < 6) text += `Maintain ${speed.toFixed(0)} kilometers per hour to catch the green light.`
    else text += `Slow down, green light in ${ttg} seconds.`
    
    const utterance = new SpeechSynthesisUtterance(text)
    utterance.rate = 0.95
    utterance.pitch = 1.1
    setPlaying(true)
    utterance.onend = () => setPlaying(false)
    window.speechSynthesis.speak(utterance)
  }

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wide">Retrofit voice module</h3>
        <div className="flex items-center gap-2">
          {playing && (
            <div className="flex items-end gap-0.5 h-3.5">
              {[0, 1, 2].map(i => (
                <motion.span key={i} className="w-1 rounded bg-amber-300"
                  animate={{ height: [4, 13, 6, 11, 4] }}
                  transition={{ duration: 0.9, repeat: Infinity, delay: i * 0.12 }} />
              ))}
            </div>
          )}
          <button onClick={() => setEnabled(e => !e)}
            className="flex items-center gap-1 text-xs px-2 py-1 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 border border-slate-700">
            {enabled ? <Volume2 size={13} /> : <VolumeX size={13} />} {enabled ? 'ON' : 'OFF'}
          </button>
        </div>
      </div>
      {voice && (
        <div className="mb-2 p-2 rounded-xl bg-slate-800/60 border border-slate-700/70">
          <div className="text-xs text-slate-400 mb-1">Static Alerts</div>
          <div className="flex gap-2">
            <button onClick={() => new Audio(voice.ta).play().catch(() => {})}
              className="flex-1 text-sm py-1.5 rounded-lg bg-amber-500/20 text-amber-200 hover:bg-amber-500/30 border border-amber-500/30 transition-colors">தமிழ் ▶</button>
            <button onClick={() => new Audio(voice.en).play().catch(() => {})}
              className="flex-1 text-sm py-1.5 rounded-lg bg-sky-500/20 text-sky-200 hover:bg-sky-500/30 border border-sky-500/30 transition-colors">English ▶</button>
          </div>
        </div>
      )}
      
      <div className="mb-2">
        <button onClick={speakNav}
          className="w-full flex items-center justify-center gap-2 text-xs py-2 rounded-lg bg-violet-500/20 text-violet-300 hover:bg-violet-500/30 border border-violet-500/40 transition-colors font-bold uppercase tracking-wide">
           Generate Sync Nav Audio
        </button>
      </div>
      <div className="space-y-1 max-h-36 overflow-y-auto font-mono text-xs">
        {events.slice(0, 12).map((e, i) => (
          <div key={i} className="text-slate-400 flex gap-2">
            <span className="text-slate-600">{e.t}</span>
            <span className={e.color || 'text-slate-300'}>{e.msg}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

const TYPE_STYLE = {
  car: { c: '#38bdf8', label: 'car' }, moto: { c: '#facc15', label: 'moto' },
  bus: { c: '#34d399', label: 'bus' }, truck: { c: '#a3a3a3', label: 'truck' },
  amb: { c: '#ef4444', label: 'ambulance' },
}

/** Fleet Inspector — live vehicle instances from v2x/vehicles.
 *  An "instance" is one actor in the simulation: id, class, position,
 *  connected-vehicle flag. This is what the RL agent and corridor see. */
export function FleetInspector({ vehicles }) {
  const list = vehicles?.vehicles || []
  const counts = {}
  list.forEach(v => { counts[v.t] = (counts[v.t] || 0) + 1 })
  return (
    <div className="card">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wide">Fleet inspector</h3>
        <span className="text-[10px] font-mono text-slate-500">{list.length} instances</span>
      </div>
      <div className="flex flex-wrap gap-1.5 mb-2">
        {Object.entries(counts).map(([t, n]) => (
          <span key={t} className="text-[10px] px-2 py-0.5 rounded-full border font-semibold"
            style={{ color: TYPE_STYLE[t]?.c || '#94a3b8', borderColor: (TYPE_STYLE[t]?.c || '#94a3b8') + '55', background: (TYPE_STYLE[t]?.c || '#94a3b8') + '18' }}>
            {n}× {TYPE_STYLE[t]?.label || t}
          </span>
        ))}
        {list.length === 0 && <span className="text-xs text-slate-500">waiting for v2x/vehicles…</span>}
      </div>
      <div className="space-y-1 max-h-32 overflow-y-auto font-mono text-[11px]">
        {list.slice(0, 10).map(v => (
          <div key={v.id} className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full shrink-0" style={{ background: TYPE_STYLE[v.t]?.c || '#38bdf8' }} />
            <span className="text-slate-300 w-20 truncate">{v.id}</span>
            <span className="text-slate-500">({v.x}, {v.y})</span>
            {v.cv && <span className="text-[9px] px-1 rounded bg-sky-500/20 text-sky-300 border border-sky-500/40">CV</span>}
            {v.em && <span className="text-[9px] px-1 rounded bg-red-500/20 text-red-300 border border-red-500/40 animate-pulse">EMERGENCY</span>}
          </div>
        ))}
      </div>
      <div className="text-[10px] text-slate-500 mt-1">every row = one actor instance in the SUMO world; CV = connected vehicle (receives SPaT/GLOSA)</div>
    </div>
  )
}

export function SafetyPanel({ lastDecision }) {
  const d = lastDecision
  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-2">
        <ShieldAlert size={15} className="text-amber-300" />
        <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wide">Safety layer</h3>
      </div>
      {d ? (
        <div className="text-xs space-y-1 font-mono">
          <div className="flex justify-between"><span className="text-slate-500">RL action</span><span className="text-slate-200">{String(d.rl_action)}</span></div>
          <div className="flex justify-between"><span className="text-slate-500">executed</span><span className={d.overridden ? 'text-amber-300' : 'text-emerald-300'}>{String(d.executed)}</span></div>
          <div className="text-slate-500">{d.reason || 'action approved as-is'}</div>
        </div>
      ) : <div className="text-xs text-slate-500">waiting for decisions…</div>}
    </div>
  )
}

export function GlosaCard({ spat }) {
  const green = (spat?.states || []).find(s => s.event_state === 6)
  const red = (spat?.states || []).find(s => s.event_state === 3)
  const ttg = red?.min_end_time ?? null
  let advice = '—', v = null
  if (ttg != null) {
    v = Math.min(13.9, 60 / Math.max(ttg, 0.5))
    advice = ttg < 6 ? `Maintain ${(Math.min(v, 13.9) * 3.6).toFixed(0)} km/h to make the green`
      : `Slow down — green in ${ttg}s`
  }
  return (
    <div className="card">
      <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wide mb-2">GLOSA · connected vehicle</h3>
      <div className="flex items-end gap-3">
        <div className="digits text-3xl font-black text-emerald-300">{v ? (v * 3.6).toFixed(0) : '--'}<span className="text-sm text-slate-500 font-normal"> km/h</span></div>
        <div className="text-xs text-slate-400 pb-1">{advice}</div>
      </div>
      <div className="text-xs text-slate-500 mt-2">advised speed for 60 m approach · green in {ttg ?? '—'}s · full cluster view → “In-Vehicle” tab</div>
    </div>
  )
}
