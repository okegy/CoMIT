# CoMIT — Cooperative Adaptive Decision Framework for Mixed Traffic

**Team Nexus · Zéphyr 2026 AI Hackathon · PS-1 Smart Intersection for Mixed Traffic**

A fully software-based proof-of-concept of an intelligent intersection for Indian
mixed traffic: cars, motorcycles, auto-rickshaws, buses, trucks, pedestrians and
emergency vehicles — with an RL signal brain, a deterministic safety layer,
an emergency green corridor, SAE-J2735-style V2X messaging over MQTT, a live
dashboard, and a YOLO+ByteTrack camera perception node.

```
┌──────────────┐   camera JSON    ┌─────────────────────────────────────┐
│ Vision node  │ ───────────────▶ │            MQTT broker              │
│ YOLO11n+BT   │                  │  aedes (TCP :1883 / WS :9001)       │
└──────────────┘                  └──────▲───────────────▲──────────────┘
                                         │ lane state    │ SPaT · alerts · voice
┌──────────────┐   fused state    ┌──────┴───────────────┴──────────────┐
│ SUMO         │ ───────────────▶ │           CoMIT core (Python)       │
│ 4-way mixed  │                  │  PPO policy → SafetyChecker → TLS   │
│ traffic sim  │ ◀─────────────── │  EmergencyManager (green corridor)  │
└──────────────┘   phase cmds     └─────────────────────────────────────┘
                                              │
                              ┌───────────────┴────────────────┐
                              │  Dashboard (React+Vite+Tailwind)│
                              │  signals · queues · GLOSA ·     │
                              │  voice module (EN + தமிழ்)       │
                              └────────────────────────────────┘
```

## Quick start

```bash
# 1. Python env (Windows)
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt

# 2. ONE command — broker auto-starts, dashboard + camera feed + ego vehicle included
.venv\Scripts\python scripts\run_demo.py --mode ppo --scenario emergency --realtime --dashboard --open
```

Dashboard tabs (http://localhost:5173):
- **Command Center** — SPaT countdowns, live queues, safety-layer decisions, GLOSA, voice console
- **In-Vehicle** — a full instrument cluster (like a Kia/Audi cluster): speedo + tacho with
  animated needles, "Anna Nagar Junction — Please wait, It's Red — Green in Ns" SPaT card,
  distance to stop line and GLOSA advisory speed — all computed live from a simulated
  **ego connected vehicle** looping the W→E corridor (`v2x/vehicle/ego` on MQTT)
- **Priority App** — a mobile-shaped software replacement for the Android priority app:
  one tap requests a green corridor with a real SHA-256-signed token over the same MQTT path

Dashboard buttons: **Trigger emergency ping** and **Cut sensor feed** (watchdog → fixed-time fallback).

Optional extras:
```bash
.venv\Scripts\python scripts\esp32_simulator.py      # ESP32+DFPlayer retrofit voice box simulator
.venv\Scripts\python perception\vision_node.py --source assets\video\intersection_street.mp4 --loop --show
```

## Train the RL controller

```bash
.venv\Scripts\python train\train_ppo.py --timesteps 100000
.venv\Scripts\python train\evaluate.py --episodes 3     # fixed vs max-pressure vs PPO
# charts + CSV → reports/
```

## Components

| Path | What |
|---|---|
| `sim/` | 4-way SUMO junction, 2 lanes/approach, 4 protected phases (through/right + left per axis), mixed-traffic vTypes, ambulance with bluelight device |
| `core/env.py` | `CoMITEnv` — Gymnasium env: 14-dim state (queues, waits, phase one-hot, elapsed, emergency flag), 5 discrete actions, reward = −Σwait − α·stops − β·emergency-delay |
| `core/safety_checker.py` | Deterministic guardrail: conflict matrix, min/max green (10/60 s), yellow+all-red clearance, guaranteed ped interval every 4 cycles, 3 s sensor watchdog → fixed-time fallback |
| `core/emergency.py` | Token-authenticated priority ping → ETA model → pre-clear green → `STOP_AND_CLEAR_LANE` broadcast → lane-empty verification → RL restore |
| `v2x/broker.js` | aedes MQTT broker (no system install, auto-started by run_demo) |
| `v2x/spat_publisher.py` | J2735-style SPaT frames (event_state 3=RED/6=GREEN/8=YELLOW, `min_end_time`), lane-state, KPIs, ego-vehicle GLOSA feed, voice + emergency alerts |
| `v2x/glosa.py` | Green-Light Optimal Speed Advisory (SUMO GLOSA formula) |
| `perception/vision_node.py` | YOLO11n + ByteTrack (built into `ultralytics`), per-approach ROIs, stop-line queue count, **pedestrian crosswalk counting**, and an **ambulance livery heuristic** that can fire an authenticated corridor ping (`--allow-ping`) → publishes to MQTT |
| `train/` | SB3 PPO training + benchmark evaluation (fixed-time / max-pressure / PPO) with charts |
| `scripts/run_demo.py` | One-command integrated demo (`--realtime` 1x pace, `--camera` CV feed, `--dashboard --open`) |
| `scripts/esp32_simulator.py` | Software twin of the ESP32+DFPlayer retrofit voice box — same MQTT topic, DFPlayer-style serial logs, plays the actual MP3s |
| `scripts/make_voice_clips.py` | Pre-generates EN + TA voice MP3s (edge-tts) → plays offline at demo time; same files drop onto an ESP32+DFPlayer Mini SD card for the physical retrofit module |

## Benchmarks

Run `train/evaluate.py` and see `reports/benchmark.png` + `benchmark.csv`
(average waiting time, queue length, CO₂, throughput across controllers).

## Safety guarantees (the differentiator)

Every RL action passes through `SafetyChecker` before TraCI touches the
junction. Unit-tested invariants (`scripts/test_safety.py`): perpendicular
greens can never coexist (conflict matrix), green is never shorter than
`min_green` nor longer than `max_green`, every switch is separated by
yellow → all-red, every 4th clearance interval is extended for pedestrians,
and a stale sensor feed (>3 s) hands control to the fixed-time program.

## Perception notes

Two demo clips ship in `assets/video/` (Pexels license, no attribution needed):
`intersection_street.mp4` (ROIs pre-calibrated) and `busy_road.mp4`.
```bash
.venv\Scripts\python perception\vision_node.py --source assets\video\intersection_street.mp4 --show
```
COCO (what YOLO11n ships with) has **no auto-rickshaw class** — autos are
picked up as car/motorcycle. For the full Indian mix, fine-tune on
[Traffic-Indian-Vehicles (Roboflow, 3,001 imgs, rickshaw/auto classes)](https://universe.roboflow.com/sayali-jadhav/traffic-indian-vehicles-j8y8b)
or [IDD-Detection (IIIT-H, 46,588 imgs)](https://idd.insaan.iiit.ac.in/).
See `docs/REFERENCES.md` for all sources.

## Retrofit voice module (hardware path)

`scripts/esp32_simulator.py` is the software twin of the hardware box: it
subscribes to `v2x/alert/voice`, prints DFPlayer-style serial logs
(`play track 0002.mp3, vol=22/30`) and plays the clip. To go physical:
flash an ESP32 with the same MQTT subscription, put `assets/audio/*.mp3`
numbered on a FAT32 microSD in a **DFPlayer Mini** (UART, 3 W speaker) and
point it at the same broker — zero software changes.

## Licenses

This repo: MIT for our code. Runs on open source: SUMO (EPL-2.0/GPL-2.0),
`sumo-rl` patterns (MIT), Ultralytics YOLO (AGPL-3.0 — fine for an open-source
hackathon entry), aedes (MIT), SB3 (MIT).
