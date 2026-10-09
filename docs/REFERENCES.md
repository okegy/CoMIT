# Research references (verified 2026-10-08)

## Simulation & RL
- LucasAlegre/sumo-rl — Gymnasium/PettingZoo SUMO traffic-signal wrapper, MIT, v1.4.5 — https://github.com/LucasAlegre/sumo-rl (MDP design reference; not a runtime dependency)
- RESCO benchmark (Pi-Star-Lab) — GPL-3.0, fixed-time/max-pressure baselines — https://github.com/Pi-Star-Lab/RESCO
- eclipse-sumo on PyPI (full binaries incl. sumo-gui, Windows wheels) — https://pypi.org/project/eclipse-sumo/
- SUMO emergency simulation (vClass=emergency, has.bluelight.device, reactiondist) — https://sumo.dlr.de/docs/Simulation/Emergency.html
- SUMO GLOSA device (advised-speed formula) — https://sumo.dlr.de/docs/Simulation/GLOSA.html
- TraCI API (setPhase/setPhaseDuration, getJamLengthVehicle, getAccumulatedWaitingTime, changeLane, setSpeedMode) — https://sumo.dlr.de/docs/TraCI/
- LibSignal (CoLight/PressLight/MPLight reimplementations) — https://github.com/DaRL-LibSignal/LibSignal
- Guojyjy/CoTV (MIT) — GLOSA + connected traffic patterns — https://github.com/Guojyjy/CoTV
- kosenina/EVPS — SUMO emergency-vehicle preemption simulator — https://github.com/kosenina/EVPS

## Computer vision & data
- Ultralytics YOLO11 + built-in trackers (bytetrack.yaml, persist=True) — https://docs.ultralytics.com/modes/track/
- Ultralytics QueueManager (stop-line ROI queue counting) — https://docs.ultralytics.com/guides/queue-management/
- COCO classes (no auto-rickshaw) — https://docs.ultralytics.com/datasets/detect/coco/
- IDD-Detection (IIIT-H + Intel; 46,588 imgs, 40 classes incl. autorickshaw; research registration) — https://idd.insaan.iiit.ac.in/
- DriveIndia (IIITH/TiHAN, 66,986 imgs, YOLO-format, 24 classes) — https://tihan.iith.ac.in/TiAND.html
- Roboflow Universe: Traffic-Indian-Vehicles (3,001 imgs, rickshaw/auto) — https://universe.roboflow.com/sayali-jadhav/traffic-indian-vehicles-j8y8b
- Roboflow Universe: Auto-Rickshaw v4 (4,514 imgs) — https://universe.roboflow.com/autorickshaw-detection/auto-rickshaw-9fpsm/dataset/4
- UA-DETRAC intersection video benchmark — http://detrac-db.rit.albany.edu/
- Pexels traffic-intersection videos (free license) — https://www.pexels.com/search/videos/traffic%20intersection/

## V2X & messaging
- SAE J2735 SPaT message set — https://www.sae.org/standards/content/j2735_202409/
- USDOT CARMA-Streets SPaT JSON schema (event_state 3/6/8, min_end_time/max_end_time) — https://usdot-fhwa-stol.github.io/documentation/carma-streets/md_streets_utils_streets_signal_phase_and_timing_README.html
- jpo-ode (J2735 data router) — https://github.com/usdot-jpo-ode/jpo-ode
- aedes MQTT broker (MIT, TCP+WS example) — https://github.com/moscajs/aedes
- MQTT.js (browser MQTT over WebSocket) — https://github.com/mqttjs/mqtt.js
- paho-mqtt 2.x migration guide — https://eclipse.dev/paho/files/paho.mqtt.python/html/migrations.html
- EMQX public broker (demo fallback, WSS :8084/mqtt) — https://broker.emqx.io/

## Dashboard & voice
- satnaing/shadcn-admin (MIT, 15.6k★) — UI patterns — https://github.com/satnaing/shadcn-admin
- tremor (Apache-2.0) chart components — https://github.com/tremorlabs/tremor
- edge-tts (Tamil: ta-IN-PallaviNeural / ta-IN-ValluvarNeural) — https://github.com/rany2/edge-tts
- Azure voice language support — https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support
- DFPlayer Mini + ESP32 retrofit voice module — https://wiki.dfrobot.com/DFPlayer_Mini_SKU_DFR0299.html

## Research backing (from the team's deck)
- Noaeen et al. 2022, RL in Urban Network Traffic Signal Control
- Bieker-Walz & Behrisch 2019, Green Waves for Emergency Vehicles
- Zhang, Cui & Ma 2024, RL-based control for signalized intersections with CAVs
- SafeLight (AAAI 2023) — safe RL for signal control — https://arxiv.org/abs/2208.05986

## Environment notes (this laptop)
- Windows Smart App Control blocked unsigned SUMO binaries (pip wheels AND official
  MSI are unsigned) — team disabled SAC to run SUMO. If re-enabled, no local SUMO.
- libsumo (in-process DLL) is also blocked by SAC; traci (TCP client) is used instead.
