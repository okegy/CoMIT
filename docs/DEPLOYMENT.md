# CoMIT — Deployment Guide (running 24/7)

## Reality check

CoMIT has three moving parts:

| Part | What it needs | Can it be 24/7? |
|---|---|---|
| **Dashboard** (React, static build) | any static host | ✅ yes, free (Vercel / GitHub Pages / Netlify) |
| **MQTT broker** (aedes / Mosquitto / EMQX) | an always-on socket host | ✅ yes (free public broker or small VM) |
| **Simulation core** (`run_demo.py`: SUMO + PPO + safety + camera) | an always-on machine with SUMO binaries | ⚠️ needs a VM — a laptop sleeps |

A laptop demo is not 24/7 by definition. Below are the supported paths, cheapest first.

## Option A — 24/7 on a cloud VM (recommended, ~₹300–500/month)

Any 2-vCPU Ubuntu VM works (Alibaba Cloud ECS, AWS Lightsail, DigitalOcean, Oracle Cloud
free tier). All SUMO + Python deps install on Linux without Windows-specific issues:

```bash
# on the VM (Ubuntu 22.04)
sudo apt update && sudo apt install -y python3-venv nodejs npm
git clone https://github.com/okegy/CoMIT.git && cd CoMIT
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cd dashboard && npm install && npm run build && cd ..

# run everything under a process manager (auto-restart = effectively 24/7)
sudo apt install -y supervisor
sudo tee /etc/supervisor/conf.d/comit.conf <<'EOF'
[program:comit-core]
command=/home/ubuntu/CoMIT/.venv/bin/python scripts/run_demo.py --mode ppo --scenario emergency --seconds 86400 --density 1.0
directory=/home/ubuntu/CoMIT
autorestart=true

[program:comit-broker]
command=node v2x/broker.js
directory=/home/ubuntu/CoMIT
autorestart=true
EOF
sudo supervisorctl reread && sudo supervisorctl update
# dashboard: serve dashboard/dist with nginx on :80
```

Open firewall ports 80 (dashboard), 1883/9001 (MQTT, TLS/credentials recommended if
public). The dashboard's MQTT URL is configurable via `VITE_MQTT_URL` at build time
(e.g. `wss://your-vm-ip:9001`).

## Option B — free public broker + local sim (demo-friendly)

Keep the sim on your laptop, but make the *dashboard* globally reachable:

1. `cd dashboard && npm run build`
2. Deploy `dashboard/dist` to Vercel/GitHub Pages (free, 24/7, HTTPS).
3. Build once with a public broker so any phone/browser can watch:
   `VITE_MQTT_URL=wss://broker.emqx.io:8084/mqtt npm run build`
   and run the demo locally with `broker.emqx.io` as the broker
   (set `BROKER=broker.emqx.io` in `v2x/spat_publisher.py` / demo args).
4. Anyone opening the hosted dashboard sees your live junction in real time.

Limitation: if the laptop stops, the dashboard shows a stalled feed (still 24/7 hosting,
not 24/7 simulation).

## Option C — laptop only (current default)

`run_demo.py` runs everything locally with the auto-started aedes broker; the
**Stop simulation** button in the dashboard (or Ctrl-C in the terminal) halts it
gracefully. A 24 h run is simply `--seconds 86400` with the laptop set to never sleep.

## CI (already included)

`.github/workflows/ci.yml` runs the safety unit tests + 300-action fuzz suite on every
push (Ubuntu runner) so regressions to the safety layer can never merge silently.
