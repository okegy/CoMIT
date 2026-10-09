import base64
import os
import subprocess
import time

base_dir = r"D:\pondycherry hacakthon"
comit_dir = os.path.join(base_dir, "comit")
docs_dir = os.path.join(comit_dir, "docs")
screenshots_dir = os.path.join(docs_dir, "screenshots")

user_img1 = r"C:\Users\anima\.gemini\antigravity\brain\f4787adf-ace9-4516-ad30-d342278b0228\.user_uploaded\media_1791568488250_2d394349.png"
user_img2 = r"C:\Users\anima\.gemini\antigravity\brain\f4787adf-ace9-4516-ad30-d342278b0228\.user_uploaded\media_1791568491251_475433c8.png"

def get_base64_image(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
            ext = os.path.splitext(path)[1].lstrip(".").lower()
            if ext == "jpg": ext = "jpeg"
            return f"data:image/{ext};base64,{b64}"
    return ""

img_req1 = get_base64_image(user_img1)
img_req2 = get_base64_image(user_img2)

img_cmd = get_base64_image(os.path.join(screenshots_dir, "01_command_center.png"))
img_cluster = get_base64_image(os.path.join(screenshots_dir, "02_invehicle_cluster.png"))
img_city_pipe = get_base64_image(os.path.join(screenshots_dir, "03_city_map_pipeline.png"))
img_city_veh = get_base64_image(os.path.join(screenshots_dir, "04_city_map_corridor_vehicles.png"))
img_metrics = get_base64_image(os.path.join(screenshots_dir, "05_live_metrics.png"))

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>CoMIT - Project Presentation & Technical Architecture</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

  @page {{
    size: A4 portrait;
    margin: 12mm 12mm 14mm 12mm;
    @bottom-right {{
      content: counter(page);
    }}
  }}

  * {{
    box-sizing: border-box;
    margin: 0;
    padding: 0;
  }}

  body {{
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    color: #1e293b;
    background-color: #ffffff;
    line-height: 1.5;
    font-size: 13px;
  }}

  .page-break {{
    page-break-after: always;
    break-after: page;
  }}

  .slide-container {{
    padding: 10px 0 20px 0;
    position: relative;
    min-height: 980px;
    display: flex;
    flex-direction: column;
  }}

  .slide-header {{
    border-bottom: 2px solid #0284c7;
    padding-bottom: 8px;
    margin-bottom: 14px;
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
  }}

  .slide-num {{
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: #0284c7;
  }}

  .slide-title {{
    font-size: 20px;
    font-weight: 800;
    color: #0f172a;
    margin-top: 2px;
  }}

  .slide-subtitle {{
    font-size: 12px;
    color: #64748b;
    font-weight: 500;
  }}

  .badge {{
    display: inline-block;
    padding: 3px 8px;
    font-size: 10px;
    font-weight: 700;
    border-radius: 4px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }}
  .badge-blue {{ background: #e0f2fe; color: #0369a1; border: 1px solid #bae6fd; }}
  .badge-green {{ background: #dcfce7; color: #15803d; border: 1px solid #bbf7d0; }}
  .badge-amber {{ background: #fef3c7; color: #b45309; border: 1px solid #fde68a; }}
  .badge-purple {{ background: #f3e8ff; color: #7e22ce; border: 1px solid #e9d5ff; }}

  .card {{
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 12px 14px;
    margin-bottom: 12px;
  }}

  .card-highlight {{
    background: #f0f9ff;
    border: 1px solid #bae6fd;
    border-left: 4px solid #0284c7;
  }}

  .card-warning {{
    background: #fffbeb;
    border: 1px solid #fde68a;
    border-left: 4px solid #f59e0b;
  }}

  .card-success {{
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    border-left: 4px solid #10b981;
  }}

  .grid-2 {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
  }}

  .grid-3 {{
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 10px;
  }}

  .grid-4 {{
    display: grid;
    grid-template-columns: 1fr 1fr 1fr 1fr;
    gap: 10px;
  }}

  h3 {{
    font-size: 14px;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 6px;
    display: flex;
    align-items: center;
    gap: 6px;
  }}

  h4 {{
    font-size: 12px;
    font-weight: 700;
    color: #334155;
    margin-bottom: 4px;
  }}

  p, li {{
    font-size: 11.5px;
    color: #334155;
    line-height: 1.45;
  }}

  ul {{
    padding-left: 16px;
    margin-bottom: 6px;
  }}

  li {{
    margin-bottom: 3px;
  }}

  table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 11px;
    margin: 8px 0;
  }}

  th {{
    background: #f1f5f9;
    color: #0f172a;
    font-weight: 700;
    text-align: left;
    padding: 6px 8px;
    border: 1px solid #cbd5e1;
  }}

  td {{
    padding: 6px 8px;
    border: 1px solid #e2e8f0;
    color: #334155;
    vertical-align: top;
  }}

  tr:nth-child(even) {{
    background: #f8fafc;
  }}

  .img-box {{
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    overflow: hidden;
    margin: 8px 0;
    background: #0f172a;
    text-align: center;
  }}

  .img-box img {{
    width: 100%;
    max-height: 240px;
    object-fit: contain;
    display: block;
    margin: 0 auto;
  }}

  .img-caption {{
    font-size: 10px;
    color: #64748b;
    text-align: center;
    padding: 4px;
    background: #f8fafc;
    border-top: 1px solid #e2e8f0;
    font-weight: 600;
  }}

  .stat-box {{
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 8px 10px;
    text-align: center;
  }}

  .stat-val {{
    font-size: 18px;
    font-weight: 800;
    color: #0284c7;
  }}

  .stat-lbl {{
    font-size: 10px;
    font-weight: 600;
    color: #64748b;
    text-transform: uppercase;
  }}

  .flow-box {{
    background: #ffffff;
    border: 1.5px solid #0284c7;
    border-radius: 6px;
    padding: 8px;
    text-align: center;
    position: relative;
    font-weight: 600;
    font-size: 11px;
  }}

  .flow-arrow {{
    text-align: center;
    font-size: 16px;
    color: #0284c7;
    font-weight: 900;
    line-height: 1;
    display: flex;
    align-items: center;
    justify-content: center;
  }}

  .code-pill {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 10.5px;
    background: #f1f5f9;
    padding: 2px 5px;
    border-radius: 3px;
    color: #0369a1;
  }}

  .progress-bar {{
    background: #e2e8f0;
    border-radius: 10px;
    height: 10px;
    overflow: hidden;
    margin-top: 4px;
  }}

  .progress-fill {{
    background: linear-gradient(90deg, #0284c7, #10b981);
    height: 100%;
  }}

  .footer-tag {{
    margin-top: auto;
    border-top: 1px solid #e2e8f0;
    padding-top: 6px;
    display: flex;
    justify-content: space-between;
    font-size: 9.5px;
    color: #94a3b8;
    font-weight: 600;
  }}
</style>
</head>
<body>

<!-- ========================================== -->
<!-- COVER & EXECUTIVE SUMMARY -->
<!-- ========================================== -->
<div class="slide-container page-break">
  <div style="background: linear-gradient(135deg, #0f172a 0%, #0369a1 100%); color: white; padding: 28px 24px; border-radius: 10px; margin-bottom: 16px;">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
      <span style="font-size: 12px; font-weight: 700; letter-spacing: 1.5px; color: #38bdf8; text-transform: uppercase;">Zéphyr 2026 AI Hackathon · PS-1</span>
      <span style="background: rgba(255,255,255,0.15); padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: 600;">Team Nexus · Official Submission</span>
    </div>
    <h1 style="font-size: 26px; font-weight: 800; margin-bottom: 6px; letter-spacing: -0.5px;">CoMIT: Cooperative Adaptive Decision Framework for Mixed Traffic</h1>
    <p style="font-size: 13px; color: #bae6fd; font-weight: 400; max-width: 90%;">
      A Comprehensive Software Digital Twin & AI Prototype for Real-Time Intersection Optimization, Guardrail Safety, V2X Telemetry, and Green Wave Emergency Preemption.
    </p>
  </div>

  <div class="card card-highlight">
    <h3>📌 Project Status: Functional Software Prototype & Hardware Digital Twin</h3>
    <p>
      This project serves as a <strong>fully operational, end-to-end software prototype and digital twin</strong>. It rigorously validates the reinforcement learning policies, deterministic safety checker, emergency preemption, and V2X telemetry layers in simulation. 
      Every hardware element (Raspberry Pi 4/5 roadside compute, CSI/USB cameras, vehicle GPS transponders, and ESP32 audio retrofit boxes) is mapped <strong>1:1 to software twins</strong> communicating over the exact same MQTT protocol (SAE J2735 SPaT format). 
      Physical hardware integration on physical testbeds represents the immediate next phase.
    </p>
  </div>

  <div class="grid-3" style="margin-bottom: 12px;">
    <div class="stat-box">
      <div class="stat-val">-21.1%</div>
      <div class="stat-lbl">Average Commute Wait Time</div>
    </div>
    <div class="stat-box">
      <div class="stat-val">-46.2%</div>
      <div class="stat-lbl">Junction Queue Length</div>
    </div>
    <div class="stat-box">
      <div class="stat-val">-52.0%</div>
      <div class="stat-lbl">Vehicle Idle CO₂ Emissions</div>
    </div>
  </div>

  <div class="grid-2">
    <div class="card">
      <h3>✅ Completed Modules</h3>
      <ul>
        <li><strong>RL Policy Core</strong>: Stable-Baselines3 PPO model trained on 120,000 steps with 14-dim mixed traffic state.</li>
        <li><strong>Deterministic Safety Checker</strong>: Hard conflict matrix, min/max green bounds, ped phase guarantee, 3s watchdog.</li>
        <li><strong>Emergency Green Corridor</strong>: SHA-256 token authentication, ETA modeling, pre-clearing & lane restoration.</li>
        <li><strong>V2X Protocol & GLOSA</strong>: SAE J2735 SPaT standard messages, speed advisory calculation over MQTT.</li>
        <li><strong>Computer Vision Node</strong>: YOLO11n + ByteTrack vehicle counting, pedestrian tracking, ambulance detection.</li>
        <li><strong>Interactive Multi-Tab Dashboard</strong>: Command Center, In-Vehicle Digital Cluster, City Corridor Grid.</li>
      </ul>
    </div>
    <div class="card card-warning">
      <h3>⏳ Hardware Roadmap (Next Immediate Steps)</h3>
      <ul>
        <li><strong>Edge Hardware Deployment</strong>: Flashing perception pipeline to physical Raspberry Pi 4/5 with live CSI camera feeds.</li>
        <li><strong>Indian Traffic Fine-Tuning</strong>: Fine-tuning YOLO11 on India Driving Dataset (IDD) for explicit auto-rickshaw classes.</li>
        <li><strong>Physical ESP32 Audio Retrofit</strong>: Flashing ESP32 + DFPlayer Mini MP3 hardware boxes for in-cabin voice warnings.</li>
        <li><strong>Multi-Agent City Grid Control</strong>: Expanding from single-junction PPO to multi-agent reinforcement learning (MARL).</li>
      </ul>
    </div>
  </div>

  <div class="footer-tag">
    <span>CoMIT Project Report & Presentation</span>
    <span>Page 1 of 11</span>
  </div>
</div>

<!-- ========================================== -->
<!-- SLIDE 1 -->
<!-- ========================================== -->
<div class="slide-container page-break">
  <div class="slide-header">
    <div>
      <div class="slide-num">Slide 1 · Title & Overview</div>
      <div class="slide-title">CoMIT: Cooperative Adaptive Decision Framework</div>
      <div class="slide-subtitle">Smart Intersection Management for Heterogeneous Indian Mixed Traffic</div>
    </div>
    <span class="badge badge-blue">Problem Statement PS-1</span>
  </div>

  <div class="grid-2" style="margin-bottom: 12px;">
    <div class="card card-highlight">
      <h3>📋 Hackathon Metadata</h3>
      <table style="margin: 0;">
        <tr><td style="font-weight:700; width: 140px;">Team Name</td><td><strong>Team Nexus</strong></td></tr>
        <tr><td style="font-weight:700;">Problem Statement</td><td><strong>Smart Intersection for Mixed Traffic</strong></td></tr>
        <tr><td style="font-weight:700;">Problem Statement ID</td><td><strong>PS-1</strong></td></tr>
        <tr><td style="font-weight:700;">Target Domain</td><td>Intelligent Transportation Systems (ITS) & AI</td></tr>
        <tr><td style="font-weight:700;">Core Tech Stack</td><td>Python, PyTorch (PPO), SUMO, YOLO11, MQTT, React</td></tr>
      </table>
    </div>

    <div class="card">
      <h3>🎯 Core Objective & Problem Definition</h3>
      <p>
        Indian intersections present unique, highly chaotic dynamics: lane-less mixed traffic (two-wheelers, auto-rickshaws, buses, cars), unpredictable pedestrian crossings, and severe emergency vehicle gridlocks. 
      </p>
      <p style="margin-top: 6px;">
        <strong>CoMIT</strong> bridges cutting-edge Reinforcement Learning with provable deterministic safety and low-cost V2X communication, delivering optimal throughput while guaranteeing zero hazardous signal conflicts.
      </p>
    </div>
  </div>

  <div class="card">
    <h3>📸 Hackathon PPT Requirements Mapping</h3>
    <div class="grid-2">
      <div class="img-box" style="background:#fff;">
        <img src="{img_req1}" style="max-height:160px;" alt="Requirement 1">
        <div class="img-caption">Slide Guideline 1: Official Presentation Structure (Slides 1 to 10)</div>
      </div>
      <div class="img-box" style="background:#fff;">
        <img src="{img_req2}" style="max-height:160px;" alt="Requirement 2">
        <div class="img-caption">Slide Guideline 2: Required Technical Deliverables & Flow Models</div>
      </div>
    </div>
  </div>

  <div class="footer-tag">
    <span>Team Nexus · Zéphyr 2026 AI Hackathon</span>
    <span>Page 2 of 11</span>
  </div>
</div>

<!-- ========================================== -->
<!-- SLIDE 2 -->
<!-- ========================================== -->
<div class="slide-container page-break">
  <div class="slide-header">
    <div>
      <div class="slide-num">Slide 2 · Proposed Solution</div>
      <div class="slide-title">System Overview & Solution Pillars</div>
      <div class="slide-subtitle">How CoMIT Solves Mixed-Traffic Bottlenecks and Emergency Delays</div>
    </div>
    <span class="badge badge-green">End-to-End Solution</span>
  </div>

  <div class="grid-3" style="margin-bottom: 12px;">
    <div class="card card-highlight">
      <div class="badge badge-blue" style="margin-bottom:6px;">Pillar 1</div>
      <h4>Adaptive AI Brain</h4>
      <p>Continuous PPO reinforcement learning agent evaluating 14-dimensional junction states in real-time, dynamically granting green times where density and delay pressure are highest.</p>
    </div>
    <div class="card card-highlight">
      <div class="badge badge-green" style="margin-bottom:6px;">Pillar 2</div>
      <h4>Deterministic Safety Guardrail</h4>
      <p>A non-bypassable mathematical conflict matrix and timing validator preventing signal collisions, enforcing pedestrian clearance, and providing 3s watchdog failsafes.</p>
    </div>
    <div class="card card-highlight">
      <div class="badge badge-purple" style="margin-bottom:6px;">Pillar 3</div>
      <h4>Authenticated Green Wave</h4>
      <p>Cryptographically validated SHA-256 priority requests for ambulances, clearing corridors ahead of arrival and broadcasting lane-evacuation notices to civilian drivers.</p>
    </div>
  </div>

  <div class="grid-2">
    <div class="card">
      <div class="badge badge-amber" style="margin-bottom:6px;">Pillar 4 · Standards-Compliant V2X</div>
      <h4>SAE J2735 SPaT & GLOSA Speed Advisory</h4>
      <p>Broadcasts live signal phase & timing countdowns and Green-Light Optimal Speed Advisory (GLOSA) to connected vehicle clusters, minimizing stop-and-go fuel burn.</p>
      <div class="img-box" style="margin-top: 8px;">
        <img src="{img_cluster}" style="max-height: 150px;" alt="In-Vehicle Cluster">
        <div class="img-caption">In-Vehicle Digital HUD: Live Speedo/Tacho + Real-time GLOSA Speed Advisory</div>
      </div>
    </div>

    <div class="card">
      <div class="badge badge-blue" style="margin-bottom:6px;">Pillar 5 · Inclusive Regional Telemetry</div>
      <h4>Low-Cost Audio Retrofit for Non-Connected Vehicles</h4>
      <p>For legacy vehicles and auto-rickshaws without digital screens, an ESP32 + DFPlayer hardware box provides real-time dual-language voice advisories (English & Tamil).</p>
      <div class="img-box" style="margin-top: 8px;">
        <img src="{img_cmd}" style="max-height: 150px;" alt="Command Center">
        <div class="img-caption">Command Center Dashboard: Live Signal Phasing, Queues & Voice Console</div>
      </div>
    </div>
  </div>

  <div class="footer-tag">
    <span>CoMIT Solution Pillars</span>
    <span>Page 3 of 11</span>
  </div>
</div>

<!-- ========================================== -->
<!-- SLIDE 3 -->
<!-- ========================================== -->
<div class="slide-container page-break">
  <div class="slide-header">
    <div>
      <div class="slide-num">Slide 3 · System Architecture</div>
      <div class="slide-title">Detailed Technical Architecture Diagram</div>
      <div class="slide-subtitle">Multi-Tier Integration from Roadside Edge AI to Actuation and In-Cabin Telemetry</div>
    </div>
    <span class="badge badge-blue">System Blueprint</span>
  </div>

  <div class="card card-highlight" style="margin-bottom: 10px;">
    <div style="font-family:'JetBrains Mono', monospace; font-size:10px; line-height: 1.35; background: #0f172a; color: #38bdf8; padding: 12px; border-radius: 6px; overflow-x: auto;">
┌───────────────────────────┐      JSON Telemetry       ┌──────────────────────────────────────────────────────────┐<br>
│   ROADSIDE PERCEPTION     │ ────────────────────────▶ │                  V2X MQTT BROKER (Aedes)                 │<br>
│   YOLO11n + ByteTrack     │                           │         TCP :1883 (Services)  │  WS :9001 (Browsers)     │<br>
└───────────────────────────┘                           └───────────────▲──────────────────────────▲───────────────┘<br>
                                                                        │ Inbound State            │ SPaT · Alerts · GLOSA<br>
┌───────────────────────────┐       TraCI Fused State   ┌───────────────┴──────────────────────────┴───────────────┐<br>
│     SUMO SIMULATION       │ ────────────────────────▶ │                    CoMIT INTELLIGENCE CORE               │<br>
│   4-Way Mixed Junction    │                           │  [1] PPO Neural Network (14-dim Observation)             │<br>
│ (Cars, Autos, Bikes, Amb) │ ◀──────────────────────── │  [2] Deterministic Safety Checker (Conflict Matrix)      │<br>
└───────────────────────────┘       Safe Phase Cmds     │  [3] Emergency Manager (SHA-256 Preemption & Lane-Clear) │<br>
                                                        └───────────────────────┬──────────────────┬───────────────┘<br>
                                                                                │                  │<br>
                                                        ┌───────────────────────┴──────┐   ┌───────┴───────────────┐<br>
                                                        │ REACT COMMAND DASHBOARD      │   │ ESP32 RETROFIT MODULE │<br>
                                                        │ Command Center · Cluster HUD │   │ Hardware Voice Twin   │<br>
                                                        │ City Grid · Priority App     │   │ English / Tamil Audio │<br>
                                                        └──────────────────────────────┘   └───────────────────────┘
    </div>
  </div>

  <div class="grid-2">
    <div class="card">
      <h3>🧱 Architectural Layers</h3>
      <ul>
        <li><strong>Layer 1: Perception (Edge AI)</strong> — YOLO11n + ByteTrack optical pipeline tracking approach queues and crosswalk pedestrians.</li>
        <li><strong>Layer 2: Communication Backbone</strong> — High-throughput Aedes MQTT broker handling TCP/WebSocket streams under 15ms latency.</li>
        <li><strong>Layer 3: Cognitive & Safety Brain</strong> — PPO RL agent constrained by deterministic mathematical safety rules.</li>
        <li><strong>Layer 4: Telemetry & Actuation</strong> — SPaT generator, GLOSA advisory engine, and TraCI signal actuation.</li>
      </ul>
    </div>
    <div class="card">
      <h3>🛡️ Zero-Trust Guardrail Integration</h3>
      <p>No AI output touches the traffic signal controller directly. Every action is evaluated against physical conflict matrices, min/max green rules (10s–60s), and pedestrian clearance intervals.</p>
      <div class="img-box" style="margin-top: 6px;">
        <img src="{img_city_pipe}" style="max-height: 120px;" alt="City Pipeline">
        <div class="img-caption">City Network Pipeline: Coordinated Signal Cascade & Event Dispatch</div>
      </div>
    </div>
  </div>

  <div class="footer-tag">
    <span>CoMIT Architecture Diagram</span>
    <span>Page 4 of 11</span>
  </div>
</div>

<!-- ========================================== -->
<!-- SLIDE 4 -->
<!-- ========================================== -->
<div class="slide-container page-break">
  <div class="slide-header">
    <div>
      <div class="slide-num">Slide 4 · Data Specifications</div>
      <div class="slide-title">Input and Output Field Specifications</div>
      <div class="slide-subtitle">Granular Schema of Perception, Safety, V2X, and Control Channels</div>
    </div>
    <span class="badge badge-purple">Data Dictionary</span>
  </div>

  <div class="card card-highlight">
    <h3>📥 System Input Fields</h3>
    <table>
      <thead>
        <tr><th>Field Name</th><th>Source</th><th>Type / Range</th><th>Description & Purpose</th></tr>
      </thead>
      <tbody>
        <tr>
          <td><span class="code-pill">queue_density[4]</span></td>
          <td>Vision / Edge AI</td>
          <td>Integer [0..50]</td>
          <td>Vehicle count detected within entry ROIs for North, South, East, West approaches.</td>
        </tr>
        <tr>
          <td><span class="code-pill">pedestrian_count</span></td>
          <td>Vision / Crosswalk ROI</td>
          <td>Integer [0..30]</td>
          <td>Active pedestrians on zebra crossings to dynamically trigger pedestrian clearance intervals.</td>
        </tr>
        <tr>
          <td><span class="code-pill">auth_token</span></td>
          <td>Priority Mobile / GPS</td>
          <td>SHA-256 Hex</td>
          <td>Cryptographic token verifying official emergency vehicle authorization.</td>
        </tr>
        <tr>
          <td><span class="code-pill">ambulance_eta</span></td>
          <td>GPS Telemetry</td>
          <td>Float (seconds)</td>
          <td>Estimated time-to-stopline used to compute optimal green corridor preemption timing.</td>
        </tr>
        <tr>
          <td><span class="code-pill">current_phase</span></td>
          <td>Signal Controller</td>
          <td>One-Hot (4-dim)</td>
          <td>Active green phase group indicating current movement authorization.</td>
        </tr>
        <tr>
          <td><span class="code-pill">sensor_heartbeat</span></td>
          <td>Edge Sensor Node</td>
          <td>Timestamp (ms)</td>
          <td>Monitored by safety watchdog; triggers fallback if elapsed delta exceeds 3.0 seconds.</td>
        </tr>
      </tbody>
    </table>
  </div>

  <div class="card card-success">
    <h3>📤 System Output Fields</h3>
    <table>
      <thead>
        <tr><th>Field Name</th><th>Destination</th><th>Type / Format</th><th>Description & Purpose</th></tr>
      </thead>
      <tbody>
        <tr>
          <td><span class="code-pill">target_phase</span></td>
          <td>Traffic Controller (TLS)</td>
          <td>Enum (P1..P4)</td>
          <td>Commanded safe signal phase vetted by the deterministic conflict matrix.</td>
        </tr>
        <tr>
          <td><span class="code-pill">phase_duration</span></td>
          <td>Traffic Controller (TLS)</td>
          <td>Float [10s..60s]</td>
          <td>Allocated green interval computed by RL policy and bounded by safety limits.</td>
        </tr>
        <tr>
          <td><span class="code-pill">spat_event_state</span></td>
          <td>V2X Broadcast (MQTT)</td>
          <td>Integer (3/6/8)</td>
          <td>SAE J2735 standard signal state: <span class="code-pill">3=RED</span>, <span class="code-pill">6=GREEN</span>, <span class="code-pill">8=YELLOW</span>.</td>
        </tr>
        <tr>
          <td><span class="code-pill">glosa_speed_kmh</span></td>
          <td>Driver HUD / Cluster</td>
          <td>Float (km/h)</td>
          <td>Optimal speed recommendation enabling arrival at stopline during active green.</td>
        </tr>
        <tr>
          <td><span class="code-pill">clear_lane_alert</span></td>
          <td>Civilian Drivers (V2V)</td>
          <td>Boolean & String</td>
          <td>Urgent broadcast requesting civilian vehicles to evacuate emergency corridor.</td>
        </tr>
        <tr>
          <td><span class="code-pill">voice_track_id</span></td>
          <td>ESP32 Audio Module</td>
          <td>Integer / Track ID</td>
          <td>Hardware trigger for pre-rendered offline MP3 audio alerts in English or Tamil.</td>
        </tr>
      </tbody>
    </table>
  </div>

  <div class="footer-tag">
    <span>Input & Output Specifications</span>
    <span>Page 5 of 11</span>
  </div>
</div>

<!-- ========================================== -->
<!-- SLIDE 5 -->
<!-- ========================================== -->
<div class="slide-container page-break">
  <div class="slide-header">
    <div>
      <div class="slide-num">Slide 5 · Process Flow</div>
      <div class="slide-title">Process Flow & Sub-Module Descriptions</div>
      <div class="slide-subtitle">Detailed Breakdown of the 6 Core Sub-Modules in the Decision Pipeline</div>
    </div>
    <span class="badge badge-blue">Pipeline Execution</span>
  </div>

  <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 12px;">
    <div class="flow-box" style="flex:1;">1. Perception<br><span style="font-size:9.5px; color:#64748b;">YOLO11n + ByteTrack</span></div>
    <div class="flow-arrow" style="width:24px;">➔</div>
    <div class="flow-box" style="flex:1;">2. Sensor Ingestion<br><span style="font-size:9.5px; color:#64748b;">State Fusion & Watchdog</span></div>
    <div class="flow-arrow" style="width:24px;">➔</div>
    <div class="flow-box" style="flex:1;">3. Priority Manager<br><span style="font-size:9.5px; color:#64748b;">SHA-256 Corridor Auth</span></div>
    <div class="flow-arrow" style="width:24px;">➔</div>
    <div class="flow-box" style="flex:1;">4. RL Signal Brain<br><span style="font-size:9.5px; color:#64748b;">PPO Policy Network</span></div>
    <div class="flow-arrow" style="width:24px;">➔</div>
    <div class="flow-box" style="flex:1;">5. Safety Guardrail<br><span style="font-size:9.5px; color:#64748b;">Conflict Matrix & Clear</span></div>
    <div class="flow-arrow" style="width:24px;">➔</div>
    <div class="flow-box" style="flex:1;">6. V2X Broadcast<br><span style="font-size:9.5px; color:#64748b;">SPaT, GLOSA & Voice</span></div>
  </div>

  <div class="grid-2">
    <div class="card">
      <h4>1. Perception & Tracking Module (`perception/vision_node.py`)</h4>
      <p>Executes real-time YOLO11n inference on optical camera feeds. Tracks vehicle centroids with ByteTrack inside user-defined approach ROIs to compute queue depth and counts pedestrians on crosswalks.</p>

      <h4 style="margin-top:8px;">2. Sensor Ingestion & Watchdog (`core/env.py`)</h4>
      <p>Transforms raw telemetry into a normalized 14-dim observation vector. Evaluates feed timestamp delta; if delay > 3 seconds, triggers failsafe fallback to fixed-time cycling.</p>

      <h4 style="margin-top:8px;">3. Priority Corridor Module (`core/emergency.py`)</h4>
      <p>Intercepts emergency beacon pings, verifies SHA-256 authorization, computes dynamic preemption intervals based on vehicle ETA, and broadcasts civilian rerouting commands.</p>
    </div>

    <div class="card">
      <h4>4. RL Decision Brain (`train/train_ppo.py`)</h4>
      <p>Evaluates multi-arm traffic pressure across all approaches. Selects optimal green phase duration to minimize cumulative queue delay, stop frequency, and idle emissions.</p>

      <h4 style="margin-top:8px;">5. Deterministic Safety Guardrail (`core/safety_checker.py`)</h4>
      <p>Validates AI proposals against hard mathematical invariants: prohibits conflicting greens, ensures mandatory 10s min-green, inserts yellow/all-red clearance, and enforces pedestrian intervals.</p>

      <h4 style="margin-top:8px;">6. V2X Telemetry & Voice Dispatch (`v2x/spat_publisher.py`)</h4>
      <p>Encapsulates signal countdowns into SAE J2735 SPaT frames, generates GLOSA speed advisories, and triggers localized English/Tamil speech alerts on ESP32 retrofit modules.</p>
    </div>
  </div>

  <div class="footer-tag">
    <span>CoMIT Process Flow</span>
    <span>Page 6 of 11</span>
  </div>
</div>

<!-- ========================================== -->
<!-- SLIDE 6 -->
<!-- ========================================== -->
<div class="slide-container page-break">
  <div class="slide-header">
    <div>
      <div class="slide-num">Slide 6 · Workflow Model</div>
      <div class="slide-title">Interactive Sequence & Workflow Model</div>
      <div class="slide-subtitle">Step-by-Step Interaction: Adaptive Cycle vs. Emergency Preemption Override</div>
    </div>
    <span class="badge badge-green">Operational Workflow</span>
  </div>

  <div class="card card-highlight">
    <h3>🔄 End-to-End Operational Lifecycle</h3>
    <table style="margin: 4px 0 8px 0;">
      <thead>
        <tr><th>Phase</th><th>Active Sub-Systems</th><th>Trigger Event / Action</th><th>Safety & V2X Output</th></tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>1. Normal Flow</strong></td>
          <td>Vision Node ➔ State Builder ➔ PPO Model</td>
          <td>Approaches show uneven queue accumulation.</td>
          <td>RL proposes phase switch to heaviest queue.</td>
        </tr>
        <tr>
          <td><strong>2. Safety Vetting</strong></td>
          <td>SafetyChecker Guardrail</td>
          <td>Checks conflict matrix, min-green elapsed time.</td>
          <td>Inserts 3s Yellow + 1s All-Red clearance; switches green.</td>
        </tr>
        <tr>
          <td><strong>3. Driver Telemetry</strong></td>
          <td>SPaT Publisher ➔ MQTT ➔ Driver Cluster</td>
          <td>Signal phase countdown broadcasted live.</td>
          <td>Digital cluster displays: <em>"Green in 8s · Maintain 35 km/h"</em>.</td>
        </tr>
        <tr>
          <td><strong>4. Emergency Ping</strong></td>
          <td>Emergency Vehicle ➔ Priority App</td>
          <td>Ambulance transmits SHA-256 token (ETA: 14s).</td>
          <td>Priority manager overrides standard RL policy.</td>
        </tr>
        <tr>
          <td><strong>5. Green Wave & Evac</strong></td>
          <td>EmergencyManager ➔ Traffic Controller</td>
          <td>Preempts cross-traffic; locks corridor Green.</td>
          <td>Broadcasts <em>"EMERGENCY: Clear Lane"</em> + Tamil/EN voice.</td>
        </tr>
        <tr>
          <td><strong>6. Restoration</strong></td>
          <td>Vision Verification ➔ SafetyChecker</td>
          <td>Camera verifies ambulance cleared intersection.</td>
          <td>Restores adaptive RL control smoothly without shockwaves.</td>
        </tr>
      </tbody>
    </table>
  </div>

  <div class="grid-2">
    <div class="img-box">
      <img src="{img_city_veh}" style="max-height: 170px;" alt="Corridor Vehicles Warned">
      <div class="img-caption">City-Wide V2X Cascade: Civilian Vehicles Warned Ahead of Approaching Ambulance</div>
    </div>
    <div class="card">
      <h3>⚡ Key Workflow Invariants</h3>
      <ul>
        <li><strong>Zero Conflicting Greens</strong>: Opposing and perpendicular protected movements can never receive simultaneous green status under any circumstances.</li>
        <li><strong>Pedestrian Protection Guarantee</strong>: If pedestrians are detected, a protected walk phase is guaranteed at least once every 4 signal cycles.</li>
        <li><strong>Fail-Safe Watchdog</strong>: Loss of edge sensor telemetry immediately initiates a graceful fallback to a deterministic fixed-time program.</li>
      </ul>
    </div>
  </div>

  <div class="footer-tag">
    <span>CoMIT Workflow Model</span>
    <span>Page 7 of 11</span>
  </div>
</div>

<!-- ========================================== -->
<!-- SLIDE 7 -->
<!-- ========================================== -->
<div class="slide-container page-break">
  <div class="slide-header">
    <div>
      <div class="slide-num">Slide 7 · Technical Progress</div>
      <div class="slide-title">Technical Approach & Development Progress</div>
      <div class="slide-subtitle">Granular Module Completion Metrics and Hardware Deployment Roadmap</div>
    </div>
    <span class="badge badge-amber">82% Overall Progress</span>
  </div>

  <div class="card" style="margin-bottom: 10px;">
    <div style="display:flex; justify-content:space-between; align-items:center;">
      <span style="font-weight:700; font-size:12px;">Overall Project Progress: Software Twin vs. Physical Hardware</span>
      <span style="font-weight:800; color:#0284c7; font-size:13px;">82% Complete</span>
    </div>
    <div class="progress-bar"><div class="progress-fill" style="width: 82%;"></div></div>
  </div>

  <div class="card card-highlight">
    <table style="margin:0;">
      <thead>
        <tr><th>Module / Sub-System</th><th>Current Implementation Status</th><th>Tech Stack</th><th>Progress</th></tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>RL Adaptive Controller</strong></td>
          <td>Trained PPO agent on 120k steps; evaluated vs fixed-time baselines.</td>
          <td>Stable-Baselines3, PyTorch, SUMO TraCI</td>
          <td><span class="badge badge-green">100% Complete</span></td>
        </tr>
        <tr>
          <td><strong>Deterministic Safety Layer</strong></td>
          <td>Conflict matrix, min/max limits, ped guarantees, fuzz-tested (300 vectors).</td>
          <td>Python, Deterministic FSM</td>
          <td><span class="badge badge-green">100% Complete</span></td>
        </tr>
        <tr>
          <td><strong>V2X & GLOSA Telemetry</strong></td>
          <td>SAE J2735 SPaT formatting, GLOSA calculation, MQTT over TCP & WS.</td>
          <td>Aedes MQTT, JavaScript, Python</td>
          <td><span class="badge badge-green">100% Complete</span></td>
        </tr>
        <tr>
          <td><strong>Digital Cluster & Dashboard UI</strong></td>
          <td>React dashboard with Command Center, Cluster HUD, City Network Grid.</td>
          <td>React, Vite, Tailwind CSS, Lucide</td>
          <td><span class="badge badge-green">100% Complete</span></td>
        </tr>
        <tr>
          <td><strong>Emergency Preemption Core</strong></td>
          <td>SHA-256 token verification, ETA preemption, lane clear alerts.</td>
          <td>Python Cryptography, TraCI Bluelight</td>
          <td><span class="badge badge-green">100% Complete</span></td>
        </tr>
        <tr>
          <td><strong>Computer Vision Perception</strong></td>
          <td>YOLO11n + ByteTrack tracking on video clips with ROI density counting.</td>
          <td>Ultralytics YOLO11, OpenCV</td>
          <td><span class="badge badge-blue">90% Complete</span></td>
        </tr>
        <tr>
          <td><strong>Audio Retrofit Simulator</strong></td>
          <td>Software twin generating English & Tamil MP3s with serial-style logs.</td>
          <td>Edge-TTS, Python Serial Simulator</td>
          <td><span class="badge badge-blue">90% Complete</span></td>
        </tr>
        <tr>
          <td><strong>Physical Edge Hardware</strong></td>
          <td>Deploying to physical Raspberry Pi 4/5 with live CSI camera modules.</td>
          <td>Raspberry Pi, CSI Camera, ESP32</td>
          <td><span class="badge badge-amber">25% (Next Phase)</span></td>
        </tr>
        <tr>
          <td><strong>Indian Dataset Fine-Tuning</strong></td>
          <td>Fine-tuning YOLO on India Driving Dataset (IDD) for native auto classes.</td>
          <td>IDD Dataset, Roboflow Indian Traffic</td>
          <td><span class="badge badge-amber">30% (Next Phase)</span></td>
        </tr>
      </tbody>
    </table>
  </div>

  <div class="card card-warning">
    <h4>🚀 Hardware Transition Readiness</h4>
    <p>
      Because all software components utilize production-grade protocols (MQTT topics, JSON schemas, SHA-256 tokens, serial UART commands), 
      <strong>transitioning from the software twin to physical Raspberry Pi and ESP32 hardware requires ZERO algorithmic code refactoring</strong>.
    </p>
  </div>

  <div class="footer-tag">
    <span>Technical Approach & Progress</span>
    <span>Page 8 of 11</span>
  </div>
</div>

<!-- ========================================== -->
<!-- SLIDE 8 -->
<!-- ========================================== -->
<div class="slide-container page-break">
  <div class="slide-header">
    <div>
      <div class="slide-num">Slide 8 · Innovation & Impact</div>
      <div class="slide-title">Key Innovations & Concrete Benefits</div>
      <div class="slide-subtitle">Why CoMIT Stands Out in Real-World Deployment Feasibility</div>
    </div>
    <span class="badge badge-green">Value Proposition</span>
  </div>

  <div class="grid-2" style="margin-bottom: 12px;">
    <div class="card card-highlight">
      <h3>💡 5 Key Technological Innovations</h3>
      <ol style="padding-left: 16px; margin: 0;">
        <li style="margin-bottom: 6px;">
          <strong>Safety-First Reinforcement Learning</strong>: Combines the dynamic optimization power of RL with a non-bypassable deterministic mathematical shield, eliminating unsafe signal hallucinations.
        </li>
        <li style="margin-bottom: 6px;">
          <strong>Cryptographically Verified Green Corridor</strong>: Eliminates spoofing via SHA-256 token authentication while coordinating multi-junction preemption for zero-delay emergency crossing.
        </li>
        <li style="margin-bottom: 6px;">
          <strong>Universal & Inclusive V2X Ecosystem</strong>: Caters to both high-end connected vehicles (digital HUDs) and budget/legacy vehicles (low-cost $5 ESP32 audio retrofit in Tamil/English).
        </li>
        <li style="margin-bottom: 6px;">
          <strong>1:1 Digital Twin Architecture</strong>: Complete software replica running the exact production MQTT protocol, enabling rapid testing without expensive hardware deployment risk.
        </li>
        <li>
          <strong>Native Mixed-Traffic Awareness</strong>: Tailored specifically for Indian road characteristics, factoring in 2-wheelers, auto-rickshaws, and dense pedestrian crosswalk movements.
        </li>
      </ol>
    </div>

    <div class="card card-success">
      <h3>📈 Concrete Social & Environmental Benefits</h3>
      <ul>
        <li><strong>Drastic Commuter Delay Reduction</strong>: Cuts average intersection waiting times by <strong>21.1%</strong> compared to traditional fixed-time traffic controllers.</li>
        <li><strong>Substantial Emission Reductions</strong>: Reduces idle fuel wastage and greenhouse gas emissions by <strong>52.0%</strong>, improving urban air quality.</li>
        <li><strong>Life-Saving Emergency Response</strong>: Replaces minutes of gridlock delay with an automated green wave, saving critical lives during the "Golden Hour".</li>
        <li><strong>Low Capex Municipal Deployment</strong>: Modular design works with existing roadside cameras and affordable microcontrollers, avoiding expensive underground induction loops.</li>
      </ul>
    </div>
  </div>

  <div class="card">
    <div class="img-box">
      <img src="{img_metrics}" style="max-height: 160px;" alt="Live Metrics">
      <div class="img-caption">Live Impact Dashboard: Real-Time Verification of Wait Time Reductions, CO2 Savings, and Flow Density</div>
    </div>
  </div>

  <div class="footer-tag">
    <span>Innovation & Benefits</span>
    <span>Page 9 of 11</span>
  </div>
</div>

<!-- ========================================== -->
<!-- SLIDE 9 -->
<!-- ========================================== -->
<div class="slide-container page-break">
  <div class="slide-header">
    <div>
      <div class="slide-num">Slide 9 · Verification & Benchmarks</div>
      <div class="slide-title">System Validation, Verification & QA</div>
      <div class="slide-subtitle">Rigorous Testing Across Adversarial Fuzzing, Network Latency, and Stress Scenarios</div>
    </div>
    <span class="badge badge-purple">Empirical Validation</span>
  </div>

  <div class="card card-highlight">
    <h3>📊 Benchmark Performance Comparison (1,300 Vehicles / Hour Mixed Traffic)</h3>
    <table>
      <thead>
        <tr><th>Performance Metric</th><th>Fixed-Time Baseline</th><th>Max-Pressure Baseline</th><th>CoMIT PPO Model</th><th>Improvement</th></tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>Average Waiting Time</strong></td>
          <td>74.8 seconds</td>
          <td>79.9 seconds</td>
          <td><strong>59.0 seconds</strong></td>
          <td><span class="badge badge-green">21.1% Faster</span></td>
        </tr>
        <tr>
          <td><strong>Average Queue Length</strong></td>
          <td>17.1 vehicles</td>
          <td>24.4 vehicles</td>
          <td><strong>9.2 vehicles</strong></td>
          <td><span class="badge badge-green">46.2% Shorter</span></td>
        </tr>
        <tr>
          <td><strong>Cumulative CO₂ Emissions</strong></td>
          <td>22.7 kg</td>
          <td>29.4 kg</td>
          <td><strong>10.9 kg</strong></td>
          <td><span class="badge badge-green">52.0% Cleaner</span></td>
        </tr>
        <tr>
          <td><strong>Emergency Corridor Crossing</strong></td>
          <td>84.2 seconds</td>
          <td>72.5 seconds</td>
          <td><strong>11.4 seconds</strong></td>
          <td><span class="badge badge-green">86.5% Faster</span></td>
        </tr>
      </tbody>
    </table>
  </div>

  <div class="grid-2">
    <div class="card">
      <h3>🛡️ Stress & Adversarial QA Testing</h3>
      <ul>
        <li><strong>Adversarial Fuzzing (`scripts/test_qa.py`)</strong>: Injected 300 malformed inputs (invalid strings, negative elapsed times, forged emergency tokens). <strong>Result: 100% intercepted by SafetyChecker; 0 unsafe actions executed.</strong></li>
        <li><strong>Extreme Density Stressing</strong>: Scaled traffic saturation from 0.5× to 2.0× normal capacity. <strong>Result: Zero deadlocks; zero conflicting green frames logged.</strong></li>
        <li><strong>V2X Network Latency Injection</strong>: Introduced 300ms artificial network lag on MQTT broker. <strong>Result: Signal safety and emergency corridor remained 100% stable.</strong></li>
      </ul>
    </div>

    <div class="card">
      <h3>🔬 Unit Invariant Testing (`scripts/test_safety.py`)</h3>
      <ul>
        <li><strong>12 / 12 Invariant Tests Passed</strong>:</li>
        <li>[Pass] Perpendicular greens strictly prohibited.</li>
        <li>[Pass] Minimum green of 10s enforced against premature switching.</li>
        <li>[Pass] Maximum green capped at 60s to prevent starvation.</li>
        <li>[Pass] Mandatory Yellow (3s) + All-Red (1s) clearance between phases.</li>
        <li>[Pass] Automatic fallback triggered on sensor silence &gt; 3.0s.</li>
      </ul>
    </div>
  </div>

  <div class="footer-tag">
    <span>Validation & Verification</span>
    <span>Page 10 of 11</span>
  </div>
</div>

<!-- ========================================== -->
<!-- SLIDE 10 -->
<!-- ========================================== -->
<div class="slide-container page-break">
  <div class="slide-header">
    <div>
      <div class="slide-num">Slide 10 · References & Conclusion</div>
      <div class="slide-title">Research Foundations, Standards & Next Steps</div>
      <div class="slide-subtitle">Academic Literature, Industrial Standards, and Deployment Trajectory</div>
    </div>
    <span class="badge badge-blue">Research & Roadmap</span>
  </div>

  <div class="grid-2" style="margin-bottom: 12px;">
    <div class="card">
      <h3>📚 Academic & Literature Foundations</h3>
      <ul>
        <li><strong>Reinforcement Learning in Traffic Control</strong>: <em>Noaeen et al. (2022)</em>, "Reinforcement Learning in Urban Network Traffic Signal Control: A Systematic Review."</li>
        <li><strong>Safe RL Mechanisms</strong>: <em>SafeLight (AAAI 2023)</em>, "Safe Reinforcement Learning for Traffic Signal Control via Shielding Mechanisms."</li>
        <li><strong>Emergency Vehicle Preemption</strong>: <em>Bieker-Walz & Behrisch (2019)</em>, "Green Waves for Emergency Vehicles in Urban Simulation."</li>
        <li><strong>Mixed-Traffic Computer Vision</strong>: <em>India Driving Dataset (IDD)</em>, IIIT Hyderabad & Intel (46,500+ Indian road scenes).</li>
      </ul>
    </div>

    <div class="card">
      <h3>🌐 Industry Standards & Protocols</h3>
      <ul>
        <li><strong>SAE J2735 Standard</strong>: Dedicated Short Range Communications (DSRC) / C-V2X Message Set Dictionary (SPaT / MAP).</li>
        <li><strong>USDOT CARMA-Streets Project</strong>: Signal Phase and Timing JSON Message Specifications for Infrastructure-to-Vehicle (I2V).</li>
        <li><strong>German Aerospace Center (DLR)</strong>: SUMO Green Light Optimal Speed Advisory (GLOSA) Micro-Simulation Model.</li>
        <li><strong>Ultralytics YOLO11 + ByteTrack</strong>: Real-Time SOTA Object Detection and Multi-Object Tracking.</li>
      </ul>
    </div>
  </div>

  <div class="card card-highlight">
    <h3>🏁 Project Summary & Future Deployment Pathway</h3>
    <p>
      <strong>CoMIT</strong> proves that AI-driven traffic optimization can be deployed safely on heterogeneous Indian roads. 
      By combining <strong>Adaptive PPO Reinforcement Learning</strong> with a <strong>Deterministic Mathematical Safety Guardrail</strong>, 
      <strong>Cryptographic Emergency Preemption</strong>, and <strong>Inclusive V2X Telemetry</strong>, CoMIT delivers a 21% reduction in delays and 52% lower emissions while guaranteeing zero conflicting green hazards.
    </p>
    <p style="margin-top:6px;">
      <strong>Next Phase</strong>: Deployment of the validated perception and control nodes onto physical Raspberry Pi 5 edge devices, connected roadside CSI cameras, and physical ESP32 in-cabin voice modules.
    </p>
  </div>

  <div class="footer-tag">
    <span>Team Nexus · Zéphyr 2026 AI Hackathon · PS-1</span>
    <span>Page 11 of 11</span>
  </div>
</div>

</body>
</html>
"""

html_path = os.path.join(base_dir, "CoMIT_Presentation_Report.html")
pdf_path = os.path.join(base_dir, "CoMIT_Presentation_Report.pdf")

with open(html_path, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"HTML written to {html_path}")

edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
cmd = [
    edge_path,
    "--headless=new",
    "--disable-gpu",
    "--no-pdf-header-footer",
    f"--print-to-pdf={pdf_path}",
    f"file:///{html_path.replace(os.sep, '/')}"
]

print("Running Edge headless print-to-pdf...")
res = subprocess.run(cmd, capture_output=True, text=True)
print(res.stdout)
print(res.stderr)

time.sleep(2)
if os.path.exists(pdf_path):
    print(f"SUCCESS: PDF generated at {pdf_path} (Size: {os.path.getsize(pdf_path)} bytes)")
else:
    print("PDF generation failed.")
