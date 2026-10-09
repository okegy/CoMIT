import { motion, AnimatePresence } from 'framer-motion'
import { Siren, MapPin, Gauge, ShieldCheck, Radio, Navigation } from 'lucide-react'

/** Mobile GPS Priority App — software replacement for the Android app in the
 *  workflow: an ambulance driver requests a green corridor with one tap;
 *  the request carries the same authenticated token the backend expects. */
export default function PriorityApp({ emergency, spat, ego, onPing, tokenReady }) {
  const st = spat?.states?.find(s => s.event_state === 6)
  const active = ['ping_accepted', 'PREEMPT'].includes(emergency?.event)
  const cleared = ['CLEARED', 'RL_RESTORED'].includes(emergency?.event)

  return (
    <div className="flex justify-center">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
        className="w-[380px] rounded-[2rem] border-[6px] border-slate-800 bg-slate-950 overflow-hidden shadow-2xl"
        style={{ minHeight: 640 }}>
        {/* notch */}
        <div className="flex justify-center pt-2 pb-1 bg-slate-950">
          <div className="w-24 h-5 rounded-full bg-slate-800" />
        </div>
        {/* status bar */}
        <div className="flex items-center justify-between px-6 py-2 text-[10px] text-slate-400 bg-slate-950">
          <span className="digits">16:24</span>
          <div className="flex items-center gap-1.5"><Radio size={11} className="text-emerald-400" /> CoMIT-Link</div>
          <span className="digits">5G ▮▮▮</span>
        </div>

        <div className="px-5 pb-6 pt-2 space-y-4 bg-gradient-to-b from-slate-950 via-slate-900/60 to-slate-950">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 rounded-2xl bg-red-500/15 border border-red-500/40 flex items-center justify-center">
              <Siren size={20} className="text-red-300" />
            </div>
            <div>
              <div className="text-white font-bold leading-tight">CoMIT Priority</div>
              <div className="text-[11px] text-slate-400">Emergency Green Corridor · AMB-001</div>
            </div>
            <ShieldCheck size={18} className={tokenReady ? 'text-emerald-400 ml-auto' : 'text-slate-600 ml-auto'} />
          </div>

          {/* corridor status */}
          <div className="glass px-4 py-3">
            <div className="text-[10px] uppercase tracking-wider text-slate-500 mb-1">Corridor status</div>
            <AnimatePresence mode="wait">
              <motion.div key={emergency?.event || 'idle'}
                initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                className={`text-sm font-bold ${
                  active ? 'text-red-300' : cleared ? 'text-emerald-300' : 'text-slate-300'}`}>
                {active && (emergency.event === 'PREEMPT'
                  ? `Green corridor ACTIVE · approach ${emergency.approach} · ETA ${emergency.eta}s`
                  : 'Priority ping accepted — corridor arming…')}
                {cleared && (emergency.event === 'CLEARED'
                  ? 'Corridor cleared — lane verified empty'
                  : 'Delivered. RL control restored — thank you!')}
                {!active && !cleared && 'Idle — no active request'}
              </motion.div>
            </AnimatePresence>
            {active && emergency.lane_clear && (
              <div className="text-[11px] text-amber-300 mt-1 font-mono">▲ {emergency.lane_clear}</div>
            )}
          </div>

          {/* signal ahead */}
          <div className="glass px-4 py-3 flex items-center justify-between">
            <div>
              <div className="text-[10px] uppercase tracking-wider text-slate-500 mb-1">Signal ahead</div>
              <div className="text-sm text-slate-200 font-semibold">
                {st ? `${st.movement_name} · ${st.event_state === 6 ? 'GREEN' : 'RED'}` : 'acquiring SPaT…'}
              </div>
              {ego?.dist_m != null && (
                <div className="text-[11px] text-slate-400 flex items-center gap-1 mt-0.5">
                  <MapPin size={11} /> {Math.max(ego.dist_m, 0).toFixed(0)} m to stop line
                </div>
              )}
            </div>
            <div className="text-right">
              <div className="digits text-3xl font-black text-sky-300">
                {st?.event_state === 6 ? Math.ceil(st.min_end_time) : ego?.time_to_green != null ? Math.ceil(ego.time_to_green) : '--'}
              </div>
              <div className="text-[10px] text-slate-500">sec</div>
            </div>
          </div>

          {/* speed */}
          <div className="glass px-4 py-3 flex items-center justify-between">
            <div className="flex items-center gap-2 text-slate-300">
              <Gauge size={15} className="text-sky-300" /> Current speed
            </div>
            <div className="digits text-2xl font-bold text-white">
              {ego?.speed_kmh != null ? ego.speed_kmh.toFixed(0) : '--'} <span className="text-xs text-slate-500">km/h</span>
            </div>
          </div>

          {/* THE button */}
          <motion.button
            whileTap={{ scale: 0.96 }}
            onClick={onPing}
            disabled={!tokenReady}
            className={`w-full py-5 rounded-2xl font-black text-lg tracking-wide transition-all ${
              active
                ? 'bg-red-950/70 text-red-300 border border-red-500/50'
                : 'bg-gradient-to-br from-red-500 to-red-700 text-white shadow-lg shadow-red-900/50 hover:brightness-110'}`}>
            <div className="flex items-center justify-center gap-3">
              <Navigation size={20} className={active ? 'animate-spin' : ''} />
              {active ? 'CORRIDOR ACTIVE — EN ROUTE' : 'REQUEST GREEN CORRIDOR'}
            </div>
          </motion.button>
          <div className="text-center text-[10px] text-slate-500">
            request signed with vehicle token · {tokenReady ? 'authenticated ✓' : 'authenticating…'}
          </div>
        </div>
      </motion.div>
    </div>
  )
}
