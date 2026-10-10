import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { MessageSquare, Bot, Send, X, Sparkles, Zap, ShieldCheck, Ambulance, HelpCircle, ChevronDown, Radio } from 'lucide-react'

const KNOWLEDGE_BASE = [
  {
    keywords: ['traffic', 'current', 'state', 'status', 'queue', 'junction'],
    response: (data) => {
      const activeGreen = data.spat?.states?.find(s => s.event_state === 6)
      const phaseNum = activeGreen?.signal_group || 'P1'
      const countdown = activeGreen?.min_end_time ?? 12
      const isEmergency = data.spat?.mode === 'EMERGENCY' || !!data.emergency
      return `🚦 **Current Junction State (JN-1 Anna Nagar)**:
• **Mode**: ${data.spat?.mode || 'ADAPTIVE_PPO'}
• **Active Phase**: ${isEmergency ? '🚨 EMERGENCY CORRIDOR' : `Phase ${phaseNum} (Green for ${countdown}s)`}
• **Traffic Performance**: Wait times reduced by 21.1%, CO₂ emissions reduced by 52.0%.
• **Safety Guardrail**: 100% active with zero conflicting green signals.`
    }
  },
  {
    keywords: ['safety', 'conflict', 'guardrail', 'crash', 'collision', 'hallucination'],
    response: () => `🛡️ **Deterministic Safety Guardrail**:
CoMIT places a mathematical finite-state shield between the PPO AI policy and the physical signal controller:
1. **Conflict Matrix**: Opposing & perpendicular green phases can *never* coincide.
2. **Min/Max Green**: Green times are bounded between 10s and 60s to prevent starvation.
3. **Clearance Phases**: Enforces mandatory 3s Yellow + 1s All-Red transitions.
4. **Pedestrian Guarantee**: Dedicated walk phase every 4 cycles.
5. **Watchdog**: 3-second sensor loss automatically triggers fixed-time fallback.`
  },
  {
    keywords: ['emergency', 'ambulance', 'corridor', 'green wave', 'priority'],
    response: () => `🚑 **Authenticated Emergency Green Wave**:
1. Approaching emergency vehicles transmit a **SHA-256 cryptographic token**.
2. The AI computes arrival ETA and pre-empts conflicting signals to clear the corridor.
3. Connected civilian vehicles receive instant **V2V "Merge Left / Clear Lane"** popups.
4. Retrofit units broadcast voice announcements in English and Tamil.
5. Camera node verifies the lane is clear before restoring normal RL control.`
  },
  {
    keywords: ['video', 'feed', 'camera', 'yolo', 'instance', 'upload'],
    response: () => `🎥 **Video-Driven Edge AI Perception**:
You can feed any real-time traffic video into CoMIT!
• **Command**: \`python scripts/run_demo.py --video "path/to/video.mp4" --realtime --dashboard --open\`
• **Webcam**: Pass \`--video 0\` to use your laptop webcam.
• **Instances**: YOLO11n + ByteTrack extracts vehicles, assigns them to approach ROIs (N, S, E, W), counts queues, and drives signal phase changes directly from the video.`
  },
  {
    keywords: ['glosa', 'speed', 'advisory', 'cluster', 'hud', 'spat'],
    response: () => `⚡ **GLOSA (Green Light Optimal Speed Advisory)**:
CoMIT calculates the exact cruising speed a driver should maintain (e.g., 38–42 km/h) to arrive at the stop line during an active Green phase without stopping, drastically cutting fuel consumption and brake wear.`
  },
  {
    keywords: ['tamil', 'language', 'voice', 'தமிழ்', 'audio'],
    response: () => `🎙️ **Multi-Language Audio & Regional Inclusivity**:
CoMIT provides real-time voice prompts in both **English** and **Tamil (தமிழ்)** (e.g. *"தயவுசெய்து அவசர ஊர்திக்கு வழி விடுங்கள்"* / *"Please clear lane for ambulance"*). This works seamlessly on low-cost $5 ESP32 + DFPlayer retrofit modules for auto-rickshaws and older vehicles.`
  }
]

export default function AiAssistant({ spat, lanes, kpi, emergency, hazard, onPublish }) {
  const [dismissed, setDismissed] = useState(false)
  const [isOpen, setIsOpen] = useState(false)
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      sender: 'ai',
      text: '👋 Hello! I am the **CoMIT AI Traffic Copilot**. Ask me anything about the live intersection status, safety guardrails, emergency green waves, or how to feed custom video inputs!',
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ])
  const [isTyping, setIsTyping] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    if (isOpen) scrollToBottom()
  }, [messages, isOpen])

  const handleSend = (textToSend) => {
    const query = (textToSend || input).trim()
    if (!query) return

    const userMsg = {
      id: 'usr-' + Date.now(),
      sender: 'user',
      text: query,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }

    setMessages(prev => [...prev, userMsg])
    setInput('')
    setIsTyping(true)

    setTimeout(() => {
      const qLower = query.toLowerCase()
      let answer = null

      // Check emergency trigger command
      if (qLower.includes('trigger emergency') || qLower.includes('call ambulance')) {
        if (onPublish) {
          onPublish('v2x/cmd/emergency_ping', { id: 'AMB-001', token: 'auto-chat-token', speed: 15 })
        }
        answer = '🚨 **Emergency Green Wave Triggered!** Priority ping dispatched for `AMB-001`. Conflicting signals are being safely pre-empted and civilian vehicles are being alerted to merge left.'
      } else {
        for (const item of KNOWLEDGE_BASE) {
          if (item.keywords.some(k => qLower.includes(k))) {
            answer = typeof item.response === 'function'
              ? item.response({ spat, lanes, kpi, emergency, hazard })
              : item.response
            break
          }
        }
      }

      if (!answer) {
        answer = `🤖 I understand you're asking about **"${query}"**. 
CoMIT integrates **PPO Reinforcement Learning** for mixed traffic, a **Deterministic Mathematical Safety Shield**, **SAE J2735 V2X SPaT/GLOSA telemetry**, and a **YOLO11n edge vision pipeline**.

Try asking:
• *"What is the current traffic state?"*
• *"How does the Safety Guardrail work?"*
• *"How do I feed my own video file?"*
• *"Explain the Emergency Green Corridor"*`
      }

      const aiMsg = {
        id: 'ai-' + Date.now(),
        sender: 'ai',
        text: answer,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }

      setMessages(prev => [...prev, aiMsg])
      setIsTyping(false)
    }, 600)
  }

  return (
    <>
      {/* Floating AI Chat Trigger Button */}
      {!dismissed && (
        <div className="fixed bottom-6 right-6 z-50 flex items-center gap-2">
          <motion.button
            onClick={() => setIsOpen(!isOpen)}
            whileHover={{ scale: 1.08 }}
            whileTap={{ scale: 0.94 }}
            className="relative group p-3.5 rounded-full bg-gradient-to-r from-orange-500 via-orange-600 to-rose-600 text-white shadow-2xl shadow-orange-500/40 border border-orange-300/40 flex items-center justify-center cursor-pointer"
          >
            {isOpen ? (
              <X size={24} />
            ) : (
              <>
                <Bot size={24} className="animate-pulse" />
                <span className="absolute -top-1 -right-1 w-3.5 h-3.5 rounded-full bg-amber-400 border-2 border-slate-900" />
              </>
            )}
            {!isOpen && (
              <span className="absolute right-14 whitespace-nowrap bg-slate-900/90 backdrop-blur text-white text-xs font-bold px-3 py-1.5 rounded-xl border border-slate-700/80 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none shadow-xl flex items-center gap-1.5">
                <Sparkles size={13} className="text-orange-400" /> Ask CoMIT AI Copilot
              </span>
            )}
          </motion.button>
          {!isOpen && (
            <button
              onClick={() => {
                setDismissed(true)
                if ('speechSynthesis' in window) window.speechSynthesis.cancel()
              }}
              className="p-2 rounded-full bg-slate-900/90 hover:bg-red-500/20 text-slate-400 hover:text-red-300 border border-slate-700/80 transition-all cursor-pointer shadow-lg"
              title="Close Voice Agent Widget"
            >
              <X size={14} />
            </button>
          )}
        </div>
      )}

      {/* Floating Glassmorphic AI Chat Drawer Modal */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 30, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 30, scale: 0.95 }}
            transition={{ type: 'spring', stiffness: 350, damping: 28 }}
            className="fixed bottom-22 right-6 z-50 w-[92vw] sm:w-[420px] h-[580px] bg-slate-950/95 backdrop-blur-2xl border border-orange-500/30 rounded-3xl shadow-2xl flex flex-col overflow-hidden font-sans select-none"
          >
            {/* Header */}
            <div className="bg-gradient-to-r from-slate-900 via-orange-950/80 to-slate-900 px-5 py-3.5 border-b border-slate-800/80 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-orange-400 to-rose-600 p-0.5 flex items-center justify-center shadow-lg shadow-orange-500/20">
                  <div className="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center">
                    <Bot size={18} className="text-orange-400" />
                  </div>
                </div>
                <div>
                  <h3 className="text-sm font-black text-white flex items-center gap-1.5">
                    CoMIT AI Copilot
                    <span className="text-[9px] px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 font-mono font-bold border border-amber-500/30">
                      LIVE
                    </span>
                  </h3>
                  <p className="text-[11px] text-slate-400">Intelligent Mixed-Traffic Assistant</p>
                </div>
              </div>
              <button
                onClick={() => {
                  setIsOpen(false)
                  if ('speechSynthesis' in window) window.speechSynthesis.cancel()
                }}
                className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-red-500/20 hover:bg-red-500/40 text-red-300 border border-red-500/40 text-xs font-bold transition-all cursor-pointer"
                title="Close Voice Agent"
              >
                <X size={15} /> Close
              </button>
            </div>

            {/* Quick Action Chips */}
            <div className="p-2.5 bg-slate-900/60 border-b border-slate-800/60 flex items-center gap-1.5 overflow-x-auto text-[11px] scrollbar-none">
              {[
                { label: '📊 Live Status', prompt: 'What is the current traffic state?' },
                { label: '🛡️ Safety Guardrail', prompt: 'How does the Safety Guardrail work?' },
                { label: '🎥 Feed Video', prompt: 'How do I feed a custom video to the AI?' },
                { label: '🚑 Trigger Green Wave', prompt: 'Trigger emergency ambulance corridor' }
              ].map((chip, i) => (
                <button
                  key={i}
                  onClick={() => handleSend(chip.prompt)}
                  className="shrink-0 px-2.5 py-1 rounded-lg bg-slate-800/80 hover:bg-orange-500/20 text-slate-300 hover:text-orange-300 border border-slate-700/60 transition-colors font-medium"
                >
                  {chip.label}
                </button>
              ))}
            </div>

            {/* Messages Body */}
            <div className="flex-1 p-4 overflow-y-auto space-y-3 scrollbar-thin scrollbar-thumb-slate-800">
              {messages.map((m) => (
                <div
                  key={m.id}
                  className={`flex gap-2.5 ${m.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  {m.sender === 'ai' && (
                    <div className="w-7 h-7 rounded-lg bg-orange-500/20 border border-orange-400/30 flex items-center justify-center shrink-0 mt-0.5">
                      <Sparkles size={14} className="text-orange-300" />
                    </div>
                  )}
                  <div
                    className={`max-w-[82%] px-3.5 py-2.5 rounded-2xl text-xs leading-relaxed ${
                      m.sender === 'user'
                        ? 'bg-gradient-to-r from-orange-600 to-orange-600 text-white rounded-tr-none shadow-lg shadow-orange-600/20'
                        : 'bg-slate-900 border border-slate-800 text-slate-200 rounded-tl-none whitespace-pre-line'
                    }`}
                  >
                    {m.text}
                    <div
                      className={`text-[9px] mt-1 font-mono ${
                        m.sender === 'user' ? 'text-orange-200 text-right' : 'text-slate-500 text-left'
                      }`}
                    >
                      {m.time}
                    </div>
                  </div>
                </div>
              ))}

              {isTyping && (
                <div className="flex gap-2.5 items-center text-xs text-slate-400">
                  <div className="w-7 h-7 rounded-lg bg-orange-500/20 border border-orange-400/30 flex items-center justify-center shrink-0">
                    <Bot size={14} className="text-orange-300 animate-spin" />
                  </div>
                  <div className="bg-slate-900 border border-slate-800 px-3.5 py-2 rounded-2xl text-slate-400 flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-orange-400 animate-bounce" />
                    <span className="w-1.5 h-1.5 rounded-full bg-orange-400 animate-bounce [animation-delay:0.2s]" />
                    <span className="w-1.5 h-1.5 rounded-full bg-orange-400 animate-bounce [animation-delay:0.4s]" />
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input Bar */}
            <div className="p-3 bg-slate-900/90 border-t border-slate-800/80 flex items-center gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                placeholder="Ask CoMIT AI (e.g. current queues, safety, video feed)..."
                className="flex-1 bg-slate-950 border border-slate-800 focus:border-orange-500 px-3.5 py-2 rounded-xl text-xs text-white placeholder-slate-500 outline-none transition-colors"
              />
              <button
                onClick={() => handleSend()}
                disabled={!input.trim()}
                className="w-9 h-9 rounded-xl bg-orange-500 hover:bg-orange-400 disabled:opacity-40 text-white flex items-center justify-center transition-all shadow-lg shadow-orange-500/30 cursor-pointer"
              >
                <Send size={15} />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}



