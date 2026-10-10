import { useEffect, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Gauge as GaugeIcon, LayoutDashboard, Ambulance, Unplug, Activity, Smartphone, ShieldAlert, Navigation2, Square, Camera } from 'lucide-react'
import { useMqtt } from './lib/mqtt'
import Intersection from './components/Intersection.jsx'
import Cluster from './components/Cluster.jsx'
import PriorityApp from './components/PriorityApp.jsx'
import AdminPortal from './components/AdminPortal.jsx'
import NavMode from './components/NavMode.jsx'
import CityGrid from './components/CityGrid.jsx'
import MultiCamStudio from './components/MultiCamStudio.jsx'
import AiAssistant from './components/AiAssistant.jsx'
import ClickParticles from './components/ClickParticles.jsx'
import GlassCursor from './components/GlassCursor.jsx'
import { KpiCards, QueueChart, EmergencyBanner, VoiceConsole, SafetyPanel, GlosaCard, FleetInspector } from './components/Panels.jsx'

const TOPICS = ['v2x/spat/jn1', 'v2x/lane_state', 'v2x/alert/emergency',
                'v2x/alert/voice', 'v2x/kpi', 'v2x/vehicle/ego', 'v2x/alert/hazard',
                'v2x/vehicles', 'v2x/perception/multi_cam']

/** Real SHA-256 token — must match core/emergency.py verify_token(). */
async function emergencyToken(id, secret) {
  const data = new TextEncoder().encode(`${id}:${secret}`)
  const digest = await crypto.subtle.digest('SHA-256', data)
  return [...new Uint8Array(digest)].map(b => b.toString(16).padStart(2, '0')).join('').slice(0, 16)
}

const fadeUp = {
  hidden: { opacity: 0, y: 18 },
  show: (i = 0) => ({ opacity: 1, y: 0, transition: { delay: i * 0.06, duration: 0.45, ease: 'easeOut' } }),
}

export default function App() {
  const { status, setHandler, publish } = useMqtt(TOPICS)
  const [tab, setTab] = useState('command')
  const [lang, setLang] = useState('en')
  const [spat, setSpat] = useState(null)
  const [lanes, setLanes] = useState(null)
  const [kpi, setKpi] = useState(null)
  const [emergency, setEmergency] = useState(null)
  const [voice, setVoice] = useState(null)
  const [decision, setDecision] = useState(null)
  const [ego, setEgo] = useState(null)
  const [vehicles, setVehicles] = useState(null)
  const [hazard, setHazard] = useState(null)
  const [events, setEvents] = useState([])
  const [token, setToken] = useState('')
  const push = (msg, color) => setEvents(ev => [{ t: new Date().toLocaleTimeString(), msg, color }, ...ev].slice(0, 60))

  useEffect(() => { emergencyToken('AMB-001', 'comit-zephyr-2026').then(setToken) }, [])

  useEffect(() => {
    setHandler('v2x/spat/jn1', (_, m) => setSpat(m))
    setHandler('v2x/lane_state', (_, m) => setLanes(m))
    setHandler('v2x/kpi', (_, m) => setKpi(m))
    setHandler('v2x/vehicle/ego', (_, m) => setEgo(m))
    setHandler('v2x/vehicles', (_, m) => setVehicles(m))
    setHandler('v2x/alert/emergency', (_, m) => {
      if (m.kind === 'decision') { setDecision(m); return }
      setEmergency(m)
      push(`EMERGENCY ${m.event || m.kind} ${m.approach || ''} ${m.eta ? 'ETA ' + m.eta + 's' : ''}`, 'text-red-300')
    })
    setHandler('v2x/alert/hazard', (_, m) => {
      setHazard(m)
      push(`HAZARD DETECTED: ${m.type} on ${m.approach} approach`, 'text-orange-400')
    })
    setHandler('v2x/alert/voice', (_, m) => { setVoice(m); push(`voice → ${m.ta}`, 'text-amber-300') })
  }, [setHandler])

  const sendPing = () => {
    publish('v2x/cmd/emergency_ping', { id: 'AMB-001', token, speed: 15 })
    push('priority ping sent (AMB-001)', 'text-red-300')
  }
  const killSensors = () => {
    publish('v2x/cmd/sensor_fail', { seconds: 25 })
    push('sensor feed cut — watchdog should trip in 3s', 'text-amber-300')
  }
  const stopSim = () => {
    if (!window.confirm('Stop the simulation? The backend will shut down gracefully.')) return
    publish('v2x/cmd/stop', { by: 'dashboard', ts: Date.now() })
    push('STOP command sent — simulation shutting down', 'text-red-300')
  }

  const statusColor = status === 'connected' ? 'bg-amber-400' : 'bg-red-400'

  return (
    <div className="cursor-none-desktop">
      <GlassCursor />
      <div className="aurora" />
      <div className="grid-overlay" />

      <div className="max-w-7xl mx-auto p-4 space-y-4">
        <motion.header initial="hidden" animate="show" variants={fadeUp}
          className="glass-strong glass-sheen flex flex-wrap items-center justify-between gap-4 px-6 py-3.5 border-2 border-orange-400/30 shadow-2xl">
          {/* Brand Logo & Title */}
          <div className="flex items-center gap-3.5 shrink-0">
            <div className="w-11 h-11 rounded-2xl bg-gradient-to-br from-amber-400 via-orange-500 to-orange-600 p-0.5 flex items-center justify-center shadow-lg shadow-orange-500/30">
              <div className="w-full h-full bg-slate-950 rounded-[14px] flex items-center justify-center">
                <Activity className="text-amber-400 animate-pulse" size={22} />
              </div>
            </div>
            <div className="flex flex-col justify-center">
              <div className="flex items-center gap-2">
                <h1 className="text-2xl font-black tracking-tight text-white digits drop-shadow">
                  CoMIT
                </h1>
                <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-400/40">
                  AI V2X CORE
                </span>
              </div>
              <p className="text-[11px] text-slate-300 font-semibold truncate max-w-[280px]">
                {lang === 'fr' ? 'Contrôle adaptatif du trafic' : lang === 'ta' ? 'அடாப்டிவ் போக்குவரத்து கட்டுப்பாடு' : 'Adaptive Traffic Decision Framework'} · PS-1
              </p>
            </div>
          </div>

          {/* Centered Navigation Tabs */}
          <div className="flex items-center gap-3 flex-wrap">
            <nav className="flex gap-1 p-1.5 rounded-2xl bg-slate-950/80 border-2 border-slate-700/60 shadow-inner">
              {[
                { id: 'command', label: lang === 'fr' ? 'Centre de cde' : lang === 'ta' ? 'கட்டளை மையம்' : 'Command Center', icon: LayoutDashboard },
                { id: 'multicam', label: lang === 'fr' ? 'Studio Multi-Cam' : lang === 'ta' ? 'கேமரா பார்வை' : 'AI Multi-Vision', icon: Camera },
                { id: 'city', label: lang === 'fr' ? 'Réseau Urbain' : lang === 'ta' ? 'நகர வலையமைப்பு' : 'City Network', icon: Activity },
                { id: 'cluster', label: lang === 'fr' ? 'Tableau de bord' : lang === 'ta' ? 'வாகனத்தில்' : 'In-Vehicle', icon: GaugeIcon },
                { id: 'nav', label: lang === 'fr' ? 'Carte Nav' : lang === 'ta' ? 'வழிசெலுத்தல்' : 'Navigation Map', icon: Navigation2 },
                { id: 'priority', label: lang === 'fr' ? 'Priorité' : lang === 'ta' ? 'முன்னுரிமை' : 'Priority App', icon: Smartphone },
                { id: 'admin', label: lang === 'fr' ? 'Administration' : lang === 'ta' ? 'நிர்வாகம்' : 'Admin Portal', icon: ShieldAlert },
              ].map(t => (
                <button key={t.id} onClick={() => setTab(t.id)}
                  className={`relative flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                    tab === t.id ? 'text-white' : 'text-slate-300 hover:text-white hover:bg-slate-800/60'}`}>
                  {tab === t.id && (
                    <motion.div layoutId="nav-pill" className="absolute inset-0 rounded-xl bg-gradient-to-r from-orange-500 to-orange-600 border border-orange-300 shadow-lg shadow-orange-500/40"
                      transition={{ type: 'spring', stiffness: 400, damping: 30 }} />
                  )}
                  <t.icon size={14} className="relative z-10" />
                  <span className="relative z-10">{t.label}</span>
                </button>
              ))}
            </nav>

            {/* Status & Language Selectors */}
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-2 text-xs font-bold text-slate-200 bg-slate-950/80 px-3 py-1.5 rounded-xl border border-slate-700/60 shadow">
                <span className={`w-2.5 h-2.5 rounded-full ${status === 'connected' ? 'bg-amber-400 shadow-[0_0_8px_#ffb800]' : 'bg-red-500 shadow-[0_0_8px_#ff7f50]'} animate-pulse`} />
                <span className="font-mono">{status === 'connected' ? 'LIVE MQTT' : 'OFFLINE'}</span>
              </div>
              <div className="flex items-center gap-1 bg-slate-950/80 p-1 rounded-xl border border-slate-700/60">
                {['en', 'fr', 'ta'].map(l => (
                  <button key={l} onClick={() => setLang(l)}
                    className={`px-2.5 py-1 text-[10.5px] font-black uppercase rounded-lg transition-all cursor-pointer ${lang === l ? 'bg-gradient-to-r from-amber-500 to-orange-500 text-slate-950 font-black shadow-md shadow-amber-500/30' : 'text-slate-400 hover:text-white'}`}>
                    {l}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </motion.header>

        <AnimatePresence mode="wait">
          {tab === 'command' ? (
            <motion.div key="command" initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }} transition={{ duration: 0.3 }} className="space-y-4">
              <EmergencyBanner emergency={emergency} hazard={hazard} />
              <motion.div variants={fadeUp} initial="hidden" animate="show" custom={1}>
                <KpiCards kpi={kpi} />
              </motion.div>
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                <motion.div variants={fadeUp} initial="hidden" animate="show" custom={2}>
                  <Intersection spat={spat} lanes={lanes} kpi={kpi} emergency={emergency} vehicles={vehicles} />
                </motion.div>
                <motion.div className="space-y-4" variants={fadeUp} initial="hidden" animate="show" custom={3}>
                  <QueueChart lanes={lanes} />
                  <SafetyPanel lastDecision={decision} />
                  <FleetInspector vehicles={vehicles} />
                </motion.div>
                <motion.div className="space-y-4" variants={fadeUp} initial="hidden" animate="show" custom={4}>
                  <GlosaCard spat={spat} />
                  <VoiceConsole voice={voice} events={events} spat={spat} lang={lang} />
                </motion.div>
              </div>
            </motion.div>
          ) : tab === 'multicam' ? (
            <motion.div key="multicam" initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }} transition={{ duration: 0.3 }} className="space-y-4">
              <MultiCamStudio spat={spat} lanes={lanes} emergency={emergency} hazard={hazard} onPublish={publish} />
            </motion.div>
          ) : tab === 'city' ? (
            <motion.div key="city" initial={{ opacity: 0, scale: 0.985 }} animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.99 }} transition={{ duration: 0.35 }} className="space-y-4">
              <CityGrid emergency={emergency} onFeedAmbulance={sendPing} spat={spat} publish={publish} />
            </motion.div>
          ) : tab === 'cluster' ? (
            <motion.div key="cluster" initial={{ opacity: 0, scale: 0.985 }} animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.99 }} transition={{ duration: 0.35 }} className="space-y-4">
              <Cluster ego={ego} />
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                <motion.div className="lg:col-span-2" variants={fadeUp} initial="hidden" animate="show" custom={1}>
                  <QueueChart lanes={lanes} />
                </motion.div>
                <motion.div variants={fadeUp} initial="hidden" animate="show" custom={2}>
                  <VoiceConsole voice={voice} events={events} spat={spat} lang={lang} />
                </motion.div>
              </div>
              <p className="text-xs text-slate-500 text-center">
                The in-vehicle cluster subscribes to the same SPaT feed — distance, time-to-green and
                GLOSA advisory speed are computed live from the simulated ego vehicle (W→E corridor).
              </p>
            </motion.div>
          ) : null}
          {tab === 'nav' && (
            <motion.div key="nav" initial={{ opacity: 0, scale: 0.985 }} animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.99 }} transition={{ duration: 0.35 }} className="space-y-4">
              <NavMode ego={ego} emergency={emergency} spat={spat} hazard={hazard} lanes={lanes} />
              <p className="text-xs text-slate-500 text-center">
                Real-Time Google Maps Style 3D Navigation with Live Turn-by-Turn, 200m Signal Status Pop-ups, GLOSA Speed Advisories, and Obstacle / Emergency Preemption Alerts.
              </p>
            </motion.div>
          )}
          {tab === 'priority' && (
            <motion.div key="priority" initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }} transition={{ duration: 0.3 }} className="space-y-4">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <PriorityApp emergency={emergency} spat={spat} ego={ego}
                  onPing={sendPing} tokenReady={!!token} />
                <div className="space-y-4">
                  <QueueChart lanes={lanes} />
                  <VoiceConsole voice={voice} events={events} spat={spat} lang={lang} />
                </div>
              </div>
              <p className="text-xs text-slate-500 text-center">
                Software replacement for the Android priority app — open this tab on a phone on the same
                Wi-Fi (http://&lt;laptop-ip&gt;:5173) and the corridor request flows through the same
                authenticated MQTT path the native app would use.
              </p>
            </motion.div>
          )}
          {tab === 'admin' && (
            <motion.div key="admin" initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }} transition={{ duration: 0.3 }} className="space-y-4">
              <AdminPortal />
            </motion.div>
          )}
        </AnimatePresence>

        <motion.div className="glass flex flex-wrap items-center gap-3 px-4 py-3" variants={fadeUp} initial="hidden" animate="show" custom={5}>
          <span className="text-xs text-slate-400 uppercase tracking-wider mr-1">Demo controls</span>
          <button onClick={sendPing}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-red-600/80 hover:bg-red-600 text-white text-sm font-semibold shadow transition-colors">
            <Ambulance size={16} /> Trigger emergency ping
          </button>
          <button onClick={killSensors}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-amber-600/80 hover:bg-amber-600 text-white text-sm font-semibold shadow transition-colors">
            <Unplug size={16} /> {lang === 'fr' ? 'Couper les capteurs' : lang === 'ta' ? 'சென்சார் துண்டி' : 'Cut sensor feed (fallback demo)'}
          </button>
          <button onClick={stopSim}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-700 text-white text-sm font-bold shadow-lg shadow-rose-900/40 transition-all border border-rose-400/50 hover:scale-105 active:scale-95">
            <Square size={15} className="fill-white" /> Stop Simulation (Off System)
          </button>
          <span className="ml-auto flex items-center gap-1.5 text-xs text-slate-500">
            <Activity size={13} /> mode: {spat?.mode || '—'} · sim {kpi?.sim_time != null ? Math.floor(kpi.sim_time) : '—'}s
          </span>
        </motion.div>

        {/* Floating AI Chat Assistant Toggle */}
        <ClickParticles />
        <AiAssistant spat={spat} lanes={lanes} kpi={kpi} emergency={emergency} hazard={hazard} onPublish={publish} />
      </div>
    </div>
  )
}





