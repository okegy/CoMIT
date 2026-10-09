# CoMIT — 3-Minute Judge Demo Script

## Before the demo (1 min setup)
```bash
.venv\Scripts\python scripts\run_demo.py --mode ppo --scenario emergency --realtime --camera --dashboard --open
```
That single command starts: MQTT broker → PPO policy + SUMO junction (1× pace) →
camera edge node on the bundled traffic clip → dashboard at http://localhost:5173.
Keep `scripts/test_safety.py` output ready to paste (12/12 PASS) and
`reports/benchmark.png` open in a second window.

## Minute 0–1 — The world & the brain (Command Center tab)
- Point at sumo-gui: mixed Indian traffic — bikes, autos, buses, trucks, cars.
- Dashboard: SPaT countdowns, live queues, pedestrian badge during clearance,
  safety-layer panel showing every RL decision and any override.
- Say: "A PPO policy reads queues + waits every 5 s and picks the phase; a
  deterministic SafetyChecker vets every decision — conflict matrix, min/max
  green, yellow + all-red, pedestrian interval."

## Minute 1–2 — Emergency corridor (switch to Priority App tab)
- Show the mobile Priority App; tap **REQUEST GREEN CORRIDOR** (or the ambulance
  auto-spawns at t=40 s in the emergency scenario).
- Watch the full chain: SHA-256-authenticated ping → ETA model → pre-emption
  granted *through* the safety layer (min-green overridden, conflict rules never)
  → `STOP_AND_CLEAR_LANE` on MQTT → Tamil + English voice (ESP32 simulator prints
  DFPlayer serial logs) → lane verified empty → RL restored.
- Switch to **In-Vehicle** tab: the cluster shows "AMBULANCE APPROACHING — CLEAR
  LEFT LANE" exactly like a connected-car instrument panel.

## Minute 2–3 — Resilience + perception + benchmarks
- Command Center → **Cut sensor feed**: watchdog trips in 3 s → junction flips to
  FALLBACK_FIXED → sensors return → adaptive control resumes.
- Camera feed: `--camera` runs YOLO11n+ByteTrack on a real intersection clip —
  per-approach counts, stop-line queues, pedestrian counting in the crosswalk band,
  and an ambulance-livery heuristic that can fire an authenticated corridor ping.
- Show `reports/benchmark.png`: PPO vs max-pressure vs fixed-time on average
  waiting time, queue length, CO₂.
- Close: "Everything runs on one MQTT fabric — same SPaT schema as USDOT
  CARMA-Streets (SAE J2735). The Android app, ESP32 box and roadside camera each
  have a software twin here today; swap in the hardware tomorrow with no code
  changes."

## Backup answers
- Q: Why not just fixed time? → benchmark chart.
- Q: What if the AI goes wrong? → SafetyChecker unit tests + live fallback demo.
- Q: Where's the hardware? → every device is software-simulated 1:1 (Priority App,
  ESP32 voice box, camera node); all speak the same MQTT topics the real hardware
  will use.
- Q: Real deployment? → replace the SUMO state feed with the vision node's; the
  broker is replaceable by any MQTT/RSU infrastructure.
