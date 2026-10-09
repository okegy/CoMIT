import { useEffect, useRef, useState } from 'react'
import { motion } from 'framer-motion'
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip, Cell } from 'recharts'
import { Ambulance, Volume2, VolumeX, ShieldAlert, Car, Clock, Leaf, Radio, Zap, ShieldCheck, CheckCircle2 } from 'lucide-react'

export function KpiCards({ kpi }) {
  const items = [
    { 
      icon: Clock, 
      label: 'Avg Wait Reduction', 
      value: kpi?.wait_reduction_pct != null ? `${kpi.wait_reduction_pct.toFixed(1)}%` : '—', 
      color: 'text-orange-300 drop-shadow-[0_0_8px_rgba(56,189,248,0.5)]', 
      borderColor: 'border-orange-500/30',
      bgColor: 'bg-orange-950/30'
    },
    { 
      icon: Car, 
      label: 'Traffic Density', 
      value: kpi?.queue_total != null ? `${kpi.queue_total} queued` : '—', 
      color: 'text-amber-400 drop-shadow-[0_0_8px_rgba(251,191,36,0.5)]', 
      borderColor: 'border-amber-500/30',
      bgColor: 'bg-amber-950/30'
    },
    { 
      icon: Leaf, 
      label: 'CO2 Saved', 
      value: kpi?.co2_saved_kg != null ? `${kpi.co2_saved_kg.toFixed(2)} kg` : '—', 
      color: 'text-[#ffb800] drop-shadow-[0_0_8px_rgba(255,184,0,0.6)]', 
      borderColor: 'border-amber-500/30',
      bgColor: 'bg-amber-950/30'
    },
    { 
      icon: Radio, 
      label: 'RL Confidence', 
      value: kpi?.rl_confidence != null ? `${(kpi.rl_confidence * 100).toFixed(1)}%` : (kpi?.controller ? 'rule-based' : '—'), 
      color: 'text-rose-300 drop-shadow-[0_0_8px_rgba(216,180,254,0.5)]', 
      borderColor: 'border-rose-500/30',
      bgColor: 'bg-rose-950/30'
    },
  ]
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3.5">
      {items.map(it => (
        <div key={it.label} className={`card !p-3.5 flex flex-col justify-between border-2 ${it.borderColor} ${it.bgColor} shadow-lg shadow-black/40`}>
          <div className="flex items-center gap-2 text-xs font-bold text-slate-300">
            <it.icon size={15} className="text-white" />
            <span className="truncate">{it.label}</span>
          </div>
          <div className={`digits text-2xl font-black mt-1 ${it.color}`}>{it.value}</div>
        </div>
      ))}
    </div>
  )
}

export function QueueChart({ lanes }) {
  const data = ['N', 'S', 'E', 'W'].map(a => ({
    approach: `App ${a}`,
    queue: lanes?.approaches?.[a]?.queue ?? 0,
    wait: lanes?.approaches?.[a]?.wait ?? 0,
  }))
  return (
    <div className="card border-2 border-slate-700/60 shadow-xl">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-xs font-black text-white uppercase tracking-wider flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-amber-400 animate-pulse" />
          Live Queue Lengths (Vehicles Halted)
        </h3>
        <span className="text-[10px] font-mono font-bold text-slate-400">Stopline ROIs</span>
      </div>
      <ResponsiveContainer width="100%" height={150}>
        <BarChart data={data}>
          <XAxis dataKey="approach" stroke="#94a3b8" fontSize={11} fontWeight={700} />
          <YAxis stroke="#94a3b8" width={24} fontSize={11} />
          <Tooltip contentStyle={{ background: 'rgba(15,23,42,0.95)', border: '1px solid #38bdf8', borderRadius: 10, fontSize: 12, fontWeight: 'bold' }} />
          <Bar dataKey="queue" radius={[6, 6, 0, 0]} minPointSize={4}>
            {data.map((d, i) => (
              <Cell key={i} fill={d.queue > 8 ? '#ff7f50' : d.queue > 3 ? '#ffb800' : '#ffb800'} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <div className="flex items-center justify-between text-[10px] font-semibold text-slate-400 mt-1 pt-1 border-t border-slate-800">
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded bg-[#ffb800]" /> Normal (0-3)</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded bg-[#ffb800]" /> Moderate (4-8)</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded bg-[#ff7f50]" /> Congested (9+)</span>
      </div>
    </div>
  )
}

export function EmergencyBanner({ emergency, hazard }) {
  if (hazard && !emergency?.event) {
    return (
      <motion.div initial={{ opacity: 0, y: -14 }} animate={{ opacity: 1, y: 0 }}
        className="rounded-2xl border-2 border-amber-400 bg-gradient-to-r from-amber-950/90 via-orange-950/80 to-slate-950 p-4 flex items-center gap-3.5 shadow-2xl shadow-amber-950/60">
        <div className="w-11 h-11 rounded-xl bg-amber-500/20 border border-amber-400 flex items-center justify-center shrink-0">
          <ShieldAlert className="text-amber-400 animate-bounce" size={24} />
        </div>
        <div className="flex-1">
          <div className="font-black text-amber-200 text-sm flex items-center gap-2 uppercase tracking-wide">
            ⚠️ INFRASTRUCTURE HAZARD DETECTED — {hazard.type}
          </div>
          <div className="text-xs text-amber-100/90 font-mono mt-0.5">
            Approach: <span className="font-bold text-white">{hazard.approach}</span> · Severity: <span className="font-bold text-amber-300">{hazard.severity}</span> · Broadcasting V2X Warning to Connected Vehicles
          </div>
        </div>
      </motion.div>
    )
  }

  if (!emergency || !emergency.event) return null
  const ev = emergency
  const isPreempt = ev.event === 'PREEMPT'
  
  return (
    <motion.div initial={{ opacity: 0, y: -14 }} animate={{ opacity: 1, y: 0 }}
      className={`rounded-2xl border-2 ${isPreempt ? 'border-red-400 bg-gradient-to-r from-red-950/90 via-rose-950/80 to-slate-950 shadow-2xl shadow-red-950/80 animate-pulse' : 'border-amber-400 bg-amber-950/80'} p-4 flex items-center gap-3.5`}>
      <div className={`w-11 h-11 rounded-xl ${isPreempt ? 'bg-red-500/20 border border-red-400' : 'bg-amber-500/20 border border-amber-400'} flex items-center justify-center shrink-0`}>
        <Ambulance className={isPreempt ? 'text-red-400' : 'text-amber-400'} size={26} />
      </div>
      <div className="flex-1">
        <div className="font-black text-white text-sm flex items-center gap-2 uppercase tracking-wide">
          {ev.event === 'PREEMPT' && <>🚨 EMERGENCY CORRIDOR PREEMPTION — {ev.approach} Approach · ETA {ev.eta}s</>}
          {ev.event === 'CLEARED' && <>✅ CORRIDOR CLEARED — Lane verified empty, restoring adaptive RL control</>}
          {ev.event === 'RL_RESTORED' && <>RL CONTROL RESTORED SMOOTHLY</>}
          {ev.event === 'ping_accepted' && <>Emergency vehicle authenticated: {ev.id}</>}
        </div>
        {ev.lane_clear && <div className="text-xs text-red-200 font-mono mt-0.5 font-bold">▲ {ev.lane_clear} broadcast over V2X</div>}
      </div>
    </motion.div>
  )
}

export function VoiceConsole({ voice, events, spat }) {
  const [enabled, setEnabled] = useState(true)
  const [playing, setPlaying] = useState(false)
  const audioRef = useRef(null)

  const speakNav = () => {
    if (!('speechSynthesis' in window)) return
    const text = 'Turn right onto Anna Salai in 400 meters. Maintain 40 km/h for Green Light Optimal Speed Advisory.'
    const utterance = new SpeechSynthesisUtterance(text)
    utterance.rate = 1.0
    window.speechSynthesis.speak(utterance)
  }

  return (
    <div className="card border-2 border-slate-700/60 shadow-xl">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-xs font-black text-white uppercase tracking-wider flex items-center gap-1.5">
          <Volume2 className="text-amber-400" size={15} />
          Retrofit Voice Module (EN + தமிழ்)
        </h3>
        <div className="flex items-center gap-2">
          <button onClick={() => setEnabled(e => !e)}
            className={`flex items-center gap-1 text-[11px] font-bold px-2.5 py-1 rounded-lg border transition-all ${enabled ? 'bg-amber-500/20 text-amber-300 border-amber-500/40' : 'bg-slate-800 text-slate-400 border-slate-700'}`}>
            {enabled ? <Volume2 size={12} /> : <VolumeX size={12} />} {enabled ? 'AUDIO ON' : 'MUTED'}
          </button>
        </div>
      </div>

      {voice && (
        <div className="mb-2 p-2.5 rounded-xl bg-slate-900/90 border border-slate-700">
          <div className="text-[10px] uppercase font-bold text-slate-400 mb-1.5">Manual Trigger Alerts</div>
          <div className="flex gap-2">
            <button onClick={() => new Audio(voice.ta).play().catch(() => {})}
              className="flex-1 text-xs py-1.5 rounded-lg bg-amber-500/20 text-amber-200 hover:bg-amber-500/30 border border-amber-500/40 font-bold transition-all cursor-pointer">
              தமிழ் ▶
            </button>
            <button onClick={() => new Audio(voice.en).play().catch(() => {})}
              className="flex-1 text-xs py-1.5 rounded-lg bg-orange-500/20 text-orange-200 hover:bg-orange-500/30 border border-orange-500/40 font-bold transition-all cursor-pointer">
              English ▶
            </button>
          </div>
        </div>
      )}
      
      <div className="mb-2">
        <button onClick={speakNav}
          className="w-full flex items-center justify-center gap-2 text-xs py-2 rounded-xl bg-gradient-to-r from-rose-600 to-rose-600 hover:from-rose-500 hover:to-rose-500 text-white border border-rose-400 shadow-lg shadow-rose-900/30 font-black uppercase tracking-wider transition-all cursor-pointer">
          <Zap size={14} /> Synthesize Sync Nav Audio
        </button>
      </div>

      <div className="space-y-1 max-h-32 overflow-y-auto font-mono text-[11px] bg-slate-950/80 p-2 rounded-xl border border-slate-800">
        {events.slice(0, 8).map((e, i) => (
          <div key={i} className="text-slate-300 flex gap-2">
            <span className="text-slate-500 shrink-0">{e.t}</span>
            <span className={e.color || 'text-slate-300'}>{e.msg}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

export function FleetInspector({ vehicles }) {
  const list = vehicles?.vehicles || []
  const counts = {}
  list.forEach(v => { counts[v.t] = (counts[v.t] || 0) + 1 })
  const TYPE_STYLE = {
    car: { c: '#38bdf8', label: 'car' }, moto: { c: '#facc15', label: 'moto' },
    bus: { c: '#34d399', label: 'bus' }, truck: { c: '#cbd5e1', label: 'truck' },
    amb: { c: '#ff7f50', label: 'ambulance' },
  }

  return (
    <div className="card border-2 border-slate-700/60 shadow-xl">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-xs font-black text-white uppercase tracking-wider">Fleet Instance Inspector</h3>
        <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-orange-500/20 text-orange-300 border border-orange-500/30">
          {list.length} Tracked Instances
        </span>
      </div>
      <div className="flex flex-wrap gap-1.5 mb-2">
        {Object.entries(counts).map(([t, n]) => (
          <span key={t} className="text-[10px] px-2 py-0.5 rounded-md border font-black"
            style={{ color: TYPE_STYLE[t]?.c || '#94a3b8', borderColor: (TYPE_STYLE[t]?.c || '#94a3b8') + '88', background: (TYPE_STYLE[t]?.c || '#94a3b8') + '20' }}>
            {n}× {TYPE_STYLE[t]?.label || t}
          </span>
        ))}
      </div>
      <div className="space-y-1 max-h-28 overflow-y-auto font-mono text-[11px] bg-slate-950/80 p-2 rounded-xl border border-slate-800">
        {list.slice(0, 8).map(v => (
          <div key={v.id} className="flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full shrink-0" style={{ background: TYPE_STYLE[v.t]?.c || '#38bdf8' }} />
              <span className="text-white font-bold">{v.id}</span>
            </div>
            <span className="text-slate-400">({Math.round(v.x)}, {Math.round(v.y)})</span>
            {v.em && <span className="text-[9px] px-1.5 rounded bg-red-500/30 text-red-200 border border-red-500 animate-pulse font-bold">AMBULANCE</span>}
          </div>
        ))}
      </div>
    </div>
  )
}

export function SafetyPanel({ lastDecision }) {
  const d = lastDecision
  return (
    <div className="card border-2 border-amber-500/40 bg-gradient-to-br from-amber-950/40 via-slate-900 to-slate-950 shadow-xl">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-xs font-black text-white uppercase tracking-wider flex items-center gap-1.5">
          <ShieldCheck className="text-[#ffb800]" size={16} />
          Deterministic Safety Shield
        </h3>
        <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-500/20 text-[#ffb800] border border-amber-400/40">
          ZERO CONFLICTS
        </span>
      </div>
      <div className="space-y-1 text-xs font-mono">
        <div className="flex justify-between text-slate-300">
          <span>RL Proposed Action:</span>
          <span className="text-white font-bold">{d?.rl_action ?? 'Keep Phase'}</span>
        </div>
        <div className="flex justify-between text-slate-300">
          <span>Safety Vetted Action:</span>
          <span className="text-[#ffb800] font-black">{d?.executed ?? '1 (NS Green)'}</span>
        </div>
        <div className="text-[11px] text-slate-400 mt-1 flex items-center gap-1">
          <CheckCircle2 size={12} className="text-[#ffb800]" />
          <span>{d?.reason || 'Conflict matrix & min-green verified safely'}</span>
        </div>
      </div>
    </div>
  )
}

export function GlosaCard({ spat }) {
  const activeGreen = spat?.states?.find(s => s.event_state === 6)
  const isEmergency = spat?.mode === 'EMERGENCY'
  
  return (
    <div className="card border-2 border-orange-500/40 shadow-xl">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-xs font-black text-white uppercase tracking-wider flex items-center gap-1.5">
          <Zap className="text-orange-400" size={15} />
          GLOSA · Connected Vehicle Feed
        </h3>
        <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-orange-500/20 text-orange-300 border border-orange-500/30 font-mono">
          J2735 SPaT
        </span>
      </div>
      <div className="flex items-center justify-between bg-slate-950 p-3 rounded-xl border border-slate-800">
        <div>
          <div className="digits text-3xl font-black text-orange-400">
            {isEmergency ? '0' : (activeGreen ? '40' : '32')} <span className="text-xs font-semibold text-slate-400 font-sans">km/h</span>
          </div>
          <div className="text-xs font-bold text-slate-300 mt-0.5">
            {isEmergency ? '🚨 Emergency Stop' : activeGreen ? 'Green Wave Pace' : 'Decelerate Safely'}
          </div>
        </div>
        <div className="text-right">
          <div className="digits text-2xl font-black text-white">
            {activeGreen?.min_end_time != null ? `${activeGreen.min_end_time}s` : '—'}
          </div>
          <div className="text-[10px] uppercase font-bold text-slate-400">Green Window</div>
        </div>
      </div>
    </div>
  )
}

