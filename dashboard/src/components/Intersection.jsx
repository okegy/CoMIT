import { motion } from 'framer-motion'

const GROUP_NAMES = { 1: 'NS through', 2: 'NS left', 3: 'EW through', 4: 'EW left' }

function Signal({ x, y, state, label, countdown }) {
  const on = { red: state === 3, green: state === 6, amber: state === 8 }
  return (
    <g transform={`translate(${x},${y})`}>
      <rect x={-15} y={-36} width={30} height={22} rx={6} fill="#060d1a" stroke="#1e3a5f" />
      <circle cx={-7} cy={-25} r={4.2}
        fill={on.red ? '#ff7f50' : '#2d0a14'}
        style={on.red ? { filter: 'drop-shadow(0 0 6px #ff7f50)' } : {}}
        className={on.red ? 'glow-coral' : ''} />
      <circle cx={0} cy={-25} r={4.2}
        fill={on.amber ? '#ffb800' : '#2d1f00'}
        style={on.amber ? { filter: 'drop-shadow(0 0 6px #ffb800)' } : {}}
        className={on.amber ? 'glow-amber' : ''} />
      <circle cx={7} cy={-25} r={4.2}
        fill={on.green ? '#22c55e' : '#001a0e'}
        style={on.green ? { filter: 'drop-shadow(0 0 6px #22c55e)' } : {}}
        className={on.green ? 'glow-green' : ''} />
      <text x={0} y={-2} textAnchor="middle" fontSize={11} fill="#e2e8f0" fontFamily="Rajdhani" fontWeight={700}>{label}</text>
      {on.green && countdown != null &&
        <text x={0} y={12} textAnchor="middle" fontSize={10} fill="#22c55e" fontFamily="Orbitron"
          style={{ filter: 'drop-shadow(0 0 4px #22c55e)' }}>{countdown}s</text>}
    </g>
  )
}

function QueueBar({ x, y, n, dir }) {
  const cells = Math.min(n, 8)
  return (
    <g>
      {Array.from({ length: cells }).map((_, i) => (
        <motion.rect key={i}
          initial={{ opacity: 0, scale: 0.4 }}
          animate={{ opacity: 0.95, scale: 1 }}
          transition={{ delay: i * 0.04 }}
          x={dir === 'h' ? x + i * 12 : x} y={dir === 'h' ? y : y - i * 12}
          width={8} height={8} rx={2}
          fill={i < 5 ? '#ffb800' : '#ff7f50'} />
      ))}
    </g>
  )
}

export default function Intersection({ spat, lanes, kpi, emergency, vehicles }) {
  const st = {}
  ;(spat?.states || []).forEach(s => { st[s.signal_group] = s })
  const green = (spat?.states || []).find(s => s.event_state === 6)
  const fallback = spat?.mode === 'FALLBACK_FIXED'
  const ped = kpi?.ped_window
  const q = (a) => lanes?.approaches?.[a]?.queue ?? 0
  const blips = vehicles?.vehicles || []
  const BLIP_COLOR = { car: '#38bdf8', moto: '#ffb800', bus: '#ffb800', truck: '#a3a3a3', amb: '#ff7f50' }

  return (
    <div className="card h-full flex flex-col border-2 border-orange-500/20">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-black text-white tracking-wide uppercase">Junction JN-1 · Pondicherry</h2>
        <span className={`text-xs px-2 py-1 rounded-full font-mono font-bold ${
          fallback
            ? 'bg-amber-500/20 text-amber-300 border border-amber-500/60 shadow-[0_0_8px_rgba(255,184,0,0.3)]'
            : spat?.mode === 'EMERGENCY'
              ? 'bg-red-500/20 text-red-300 border border-red-500/60 shadow-[0_0_8px_rgba(255,127,80,0.4)]'
              : 'bg-amber-500/20 text-amber-300 border border-amber-500/60 shadow-[0_0_8px_rgba(255,184,0,0.3)]'}`}>
          {spat?.mode || '—'}
        </span>
      </div>
      <svg viewBox="0 0 340 340" className="w-full flex-1">
        {/* roads */}
        <rect x={20} y={130} width={300} height={80} fill="#0d1a30" />
        <rect x={130} y={20} width={80} height={300} fill="#0d1a30" />
        <rect x={130} y={130} width={80} height={80} fill="#162035" />
        {/* lane markings */}
        <line x1={20} y1={170} x2={130} y2={170} stroke="#1e3a5f" strokeWidth={2} strokeDasharray="10 8" />
        <line x1={210} y1={170} x2={320} y2={170} stroke="#1e3a5f" strokeWidth={2} strokeDasharray="10 8" />
        <line x1={170} y1={20} x2={170} y2={130} stroke="#1e3a5f" strokeWidth={2} strokeDasharray="10 8" />
        <line x1={170} y1={210} x2={170} y2={320} stroke="#1e3a5f" strokeWidth={2} strokeDasharray="10 8" />
        {/* green corridor */}
        {spat?.mode === 'EMERGENCY' && emergency?.approach && (
          <>
            <motion.line
              initial={{ opacity: 0, scaleY: 0 }}
              animate={{ opacity: 1, scaleY: 1 }}
              x1={['E', 'W'].includes(emergency.approach) ? 20 : 170}
              y1={['N', 'S'].includes(emergency.approach) ? 20 : 170}
              x2={['E', 'W'].includes(emergency.approach) ? 320 : 170}
              y2={['N', 'S'].includes(emergency.approach) ? 320 : 170}
              stroke="#ffb800" strokeWidth={12} opacity={0.4} className="glow-amber"
            />
            <motion.circle cx={170} cy={170} r={40} fill="none" stroke="#38bdf8" strokeWidth={2}
              initial={{ r: 40, opacity: 0.8 }} animate={{ r: 150, opacity: 0 }} transition={{ repeat: Infinity, duration: 1.5 }} />
            <motion.circle cx={170} cy={170} r={40} fill="none" stroke="#38bdf8" strokeWidth={2}
              initial={{ r: 40, opacity: 0.8 }} animate={{ r: 150, opacity: 0 }} transition={{ repeat: Infinity, duration: 1.5, delay: 0.75 }} />
            <motion.g initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
              <rect x={30} y={30} width={90} height={22} rx={4} fill="#0ea5e9" opacity={0.2} stroke="#38bdf8" />
              <text x={75} y={45} textAnchor="middle" fontSize={9} fill="#bae6fd" fontFamily="Orbitron">► V2V REROUTING</text>
            </motion.g>
          </>
        )}
        {/* crossing zebra */}
        {[0, 1, 2, 3, 4].map(i => (
          <g key={i}>
            <line x1={134 + i * 14} y1={132} x2={134 + i * 14} y2={146} stroke="#253a56" strokeWidth={4} />
            <line x1={134 + i * 14} y1={194} x2={134 + i * 14} y2={208} stroke="#253a56" strokeWidth={4} />
            <line x1={132} y1={134 + i * 14} x2={146} y2={134 + i * 14} stroke="#253a56" strokeWidth={4} />
            <line x1={194} y1={134 + i * 14} x2={208} y2={134 + i * 14} stroke="#253a56" strokeWidth={4} />
          </g>
        ))}
        {/* pedestrian badge */}
        {ped && (
          <motion.g initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <rect x={139} y={161} width={62} height={18} rx={9} fill="rgba(255,184,0,0.15)" stroke="#ffb800" strokeWidth={1} />
            <text x={170} y={173.5} textAnchor="middle" fontSize={9.5} fill="#ffb800" fontFamily="Rajdhani" fontWeight={700}>PED CROSS ✓</text>
          </motion.g>
        )}
        {/* queues */}
        <QueueBar x={60} y={218} n={q('N')} dir="v" />
        <QueueBar x={272} y={114} n={q('S')} dir="v" />
        <QueueBar x={104} y={70} n={q('E')} dir="h" />
        <QueueBar x={228} y={262} n={q('W')} dir="h" />
        {/* signals */}
        <Signal x={170} y={112} state={st[1]?.event_state ?? 3} label="N" countdown={st[1]?.min_end_time} />
        <Signal x={170} y={244} state={st[1]?.event_state ?? 3} label="S" />
        <Signal x={248} y={176} state={st[3]?.event_state ?? 3} label="E" countdown={st[3]?.min_end_time} />
        <Signal x={92} y={176} state={st[3]?.event_state ?? 3} label="W" />
        {/* live vehicle blips */}
        {blips.map((v) => (
          <motion.circle key={v.id}
            initial={{ opacity: 0 }} animate={{ opacity: 1 }}
            cx={Math.max(24, Math.min(316, v.x))} cy={Math.max(24, Math.min(316, v.y))}
            r={v.em ? 5.5 : v.cv ? 4.5 : 3.2}
            fill={BLIP_COLOR[v.t] || '#38bdf8'}
            stroke={v.cv ? '#ffffff' : v.em ? '#fecaca' : 'none'}
            strokeWidth={v.em || v.cv ? 1.5 : 0}
            className={v.em ? 'glow-coral' : ''}>
            <animate attributeName="opacity" values="1;1" dur="1s" />
          </motion.circle>
        ))}
        {blips.length === 0 && (
          <text x={170} y={310} textAnchor="middle" fontSize={9} fill="#334155" fontFamily="Rajdhani">
            {vehicles ? 'no vehicles in view' : 'digital twin: waiting for v2x/vehicles feed…'}
          </text>
        )}
        {/* center countdown */}
        <text x={170} y={169} textAnchor="middle" fontSize={15} fill="#ffffff" fontWeight="bold" fontFamily="Orbitron"
          style={{ filter: green ? 'drop-shadow(0 0 8px #ffb800)' : 'none' }}>
          {green ? `${green.min_end_time}s` : '—'}
        </text>
        <text x={170} y={187} textAnchor="middle" fontSize={10} fill="#94a3b8" fontFamily="Rajdhani" fontWeight={600}>
          {green ? GROUP_NAMES[green.signal_group] + ' GREEN' : (ped ? 'pedestrian phase' : 'all red')}
        </text>
      </svg>
    </div>
  )
}


