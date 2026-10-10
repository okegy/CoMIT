"""CoMIT integrated demo — one command.

Runs: MQTT broker (auto-started if not up) + SUMO intersection +
(PPO policy | max-pressure | fixed-time) + SafetyChecker + EmergencyManager +
SPaT/V2X publisher + ego connected vehicle with live GLOSA feed + dashboard.

Scenarios:
    --scenario emergency  ambulance departs at t=40s with authenticated ping
    --scenario fallback   sensor feed cut at t=120s -> watchdog -> fixed-time
    (dashboard buttons can trigger both at any time via v2x/cmd/#)

Usage:
    python scripts/run_demo.py --mode ppo --scenario emergency --gui --dashboard --open
"""
import argparse
import hashlib
import os
import shutil
import socket
import subprocess
import sys
import time
import threading

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.env import CoMITEnv                      # noqa: E402
from core.emergency import EmergencyManager        # noqa: E402
from v2x.spat_publisher import SpatPublisher       # noqa: E402
from v2x.glosa import advisory_speed               # noqa: E402

SIGNAL_NAME = "JN-1 · Anna Nagar Junction"
EMERGENCY_ID = "AMB-001"

# fixed-time baseline at density 1.0 (from train/evaluate.py benchmark runs)
BASELINE = {"wait_s": 74.82, "co2_g_per_s": 22653.5 / 900.0, "queue": 17.08}

# map vehicles onto the dashboard's 340x340 junction SVG
APPROACH_YX = {
    "W2J": [(130, 200), (130, 182)], "E2J": [(210, 200), (210, 182)],
    "N2J": [(150, 210), (168, 210)], "S2J": [(190, 130), (172, 130)],
    "J2E": [(210, 150), (210, 168)], "J2W": [(130, 150), (130, 168)],
    "J2S": [(190, 210), (172, 210)], "J2N": [(150, 130), (168, 130)],
}
VCLASS_TYPE = {"passenger": "car", "motorcycle": "moto", "bus": "bus",
               "truck": "truck", "emergency": "amb"}


def vehicle_map_payload(vdata, traci, lane_lengths):
    items = []
    for v, d in vdata.items():
        lane = d["lane"]
        edge = lane.rsplit("_", 1)[0] if "_" in lane else ""
        if edge not in APPROACH_YX:
            continue
        try:
            lane_idx = int(lane.rsplit("_", 1)[1])
        except (ValueError, IndexError):
            lane_idx = 0
        if lane not in lane_lengths:
            try:
                lane_lengths[lane] = traci.lane.getLength(lane)
            except Exception:
                lane_lengths[lane] = 300.0
        L = lane_lengths[lane]
        if edge in ("W2J", "E2J", "N2J", "S2J"):
            dist = L - d["pos"]                       # distance to stop line
        else:
            dist = d["pos"]                           # past the junction
        px = min(dist / max(L, 1), 1.0) * 280.0
        bx, by = APPROACH_YX[edge][min(lane_idx, 1)]
        if edge == "W2J":   x, y = bx - px, by
        elif edge == "E2J": x, y = bx + px, by
        elif edge == "N2J": x, y = bx, by + px
        elif edge == "S2J": x, y = bx, by - px
        elif edge == "J2E": x, y = bx + px, by
        elif edge == "J2W": x, y = bx - px, by
        elif edge == "J2S": x, y = bx, by + px
        else:              x, y = bx, by - px          # J2N
        items.append({"id": v, "x": round(x, 1), "y": round(y, 1),
                      "t": VCLASS_TYPE.get(d["vclass"], "car"),
                      "cv": v.startswith("ego-"),
                      "em": d["vclass"] == "emergency"})
    return items


def sha16(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()[:16]


def port_open(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.3)
        return s.connect_ex(("127.0.0.1", port)) == 0


def ensure_broker():
    if port_open(1883) and port_open(9001):
        print("[demo] MQTT broker already running")
        return None
    print("[demo] starting MQTT broker (node v2x/broker.js)")
    return subprocess.Popen(["node", os.path.join(ROOT, "v2x", "broker.js")],
                            stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)


class EgoVehicle:
    """A connected vehicle looping on the W->E corridor; feeds the cluster UI."""

    def __init__(self, env, sp, route="W_E"):
        self.env = env
        self.sp = sp
        self.route = route
        self.id = None
        self._spawn_at = 3.0

    def update(self):
        tr = self.env._traci
        if tr is None:
            return
        if self.id is None or self.id not in tr.vehicle.getIDList():
            if self.env.sim_time >= self._spawn_at:
                vid = f"ego-{int(self.env.sim_time)}"
                tr.vehicle.add(vid, self.route, typeID="car", depart="now",
                               departLane="free", departSpeed="max")
                self.id = vid
                self._spawn_at = self.env.sim_time + 60   # respawn after pass
            return
        lane = tr.vehicle.getLaneID(self.id)
        edge = lane.rsplit("_", 1)[0] if "_" in lane else ""
        speed = tr.vehicle.getSpeed(self.id) * 3.6
        dist, ttg, group_state = None, None, "red"
        green_group = self.env._current_green_group
        # ego needs the EW through group (2) to cross
        need = 2
        if edge == "W2J":
            dist = tr.lane.getLength(lane) - tr.vehicle.getLanePosition(self.id)
        elif edge.startswith("J2"):
            dist = 0.0
            group_state = "green"
        if dist is not None and edge == "W2J":
            phase = tr.trafficlight.getPhase("J")
            if green_group == need and phase in (0, 3, 6, 9):
                group_state = "green"
                ttg = max(self.env._green_start + 60 - self.env.sim_time, 0)
            elif phase in (0, 3, 6, 9):
                group_state = "red"
                # seconds until group `need` turns green: walk the phase cycle
                ttg = self._time_until_green(phase)
            else:
                group_state = "yellow" if green_group == need else "red"
                ttg = 6
        adv = advisory_speed(dist or 0, ttg or 0)
        self.sp.publish_ego({
            "id": self.id, "signal": SIGNAL_NAME,
            "speed_kmh": round(speed, 1),
            "dist_m": round(dist, 1) if dist is not None else None,
            "group_state": group_state, "time_to_green": ttg,
            "advisory_kmh": adv["v"], "advice": adv["advice"],
            "emergency": self.env.safety_state.emergency_request is not None,
            "sim_time": self.env.sim_time,
        })

    def _time_until_green(self, phase):
        """Rough walk of the comit program from current phase to group-2 green (6)."""
        order = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
        i = order.index(phase) if phase in order else 0
        steps = 0
        while order[i] != 6 and steps < 12:
            i = (i + 1) % 12
            steps += 1
        return steps * 1.0 + max(self.env._green_elapsed() - self.env.safety.min_green, 0)


def paho_cmd_client(on_msg):
    import paho.mqtt.client as mqtt
    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="comit-cmd")
    c.on_message = lambda cl, u, m: on_msg(m.topic, m.payload)
    for attempt in range(20):
        try:
            c.connect("localhost", 1883)
            break
        except OSError:
            time.sleep(0.5)
    c.loop_start()
    c.subscribe("v2x/cmd/#")
    return c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["ppo", "maxpressure", "fixed"], default="ppo")
    ap.add_argument("--scenario", choices=["none", "emergency", "fallback"],
                    default="none")
    ap.add_argument("--seconds", type=int, default=600)
    ap.add_argument("--density", type=float, default=1.0)
    ap.add_argument("--gui", action="store_true", help="show sumo-gui")
    ap.add_argument("--dashboard", action="store_true", help="launch Vite dev server")
    ap.add_argument("--open", action="store_true", help="open the dashboard browser tab")
    ap.add_argument("--realtime", action="store_true",
                    help="pace simulation at 1x wall-clock (for live demos)")
    ap.add_argument("--camera", action="store_true",
                    help="also run the CV edge node on the bundled sample video")
    ap.add_argument("--video", default=None,
                    help="custom video file path or '0' for webcam for real-time AI perception")
    ap.add_argument("--vision-model", default="yolo11n.pt",
                    help="path to pretrained YOLO vision weights (e.g. UVH-26, Roboflow Indian Traffic)")
    ap.add_argument("--v2x-latency", type=float, default=0,
                    help="inject N ms latency into outbound V2X messages "
                         "(QA: system must stay safe with 100–500 ms delay)")
    a = ap.parse_args()

    import json as _json
    _lat = a.v2x_latency / 1000.0

    def delayed(fn, *args, **kwargs):
        """Publish through the latency injector (QA protocol §3.3)."""
        if _lat <= 0:
            fn(*args, **kwargs)
        else:
            threading.Timer(_lat, lambda: fn(*args, **kwargs)).start()

    broker_proc = ensure_broker()

    camera_proc = None
    if a.camera or a.video is not None:
        cam_src = a.video if a.video is not None else os.path.join(ROOT, "assets", "video", "intersection_street.mp4")
        camera_proc = subprocess.Popen(
            [sys.executable, os.path.join(ROOT, "perception", "multi_camera_streamer.py"),
             "--source", str(cam_src), "--model", str(a.vision_model), "--loop", "--allow-ping"],
            stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        print(f"[demo] multi-camera AI streamer started on source={cam_src} with model={a.vision_model} (MJPEG on port 8088)")

    if a.dashboard:
        npm = shutil.which("npm.cmd") or shutil.which("npm")
        threading.Thread(target=lambda: subprocess.run(
            [npm, "run", "dev"], cwd=os.path.join(ROOT, "dashboard")),
            daemon=True).start()
        print("dashboard -> http://localhost:5173  (MQTT ws://localhost:9001)")
    if a.open:
        time.sleep(4)
        url = "http://localhost:5173/"
        if os.name == "nt":
            subprocess.Popen(["cmd", "/c", "start", "", url],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.Popen(["xdg-open", url],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # ------------------------------------------------------------- RL policy
    model = None
    if a.mode == "ppo":
        from stable_baselines3 import PPO
        p = os.path.join(ROOT, "train", "models", "ppo_comit.zip")
        if os.path.exists(p):
            model = PPO.load(p)
            print("[demo] loaded PPO policy")
        else:
            print("[demo] no trained model found — falling back to max-pressure")
            a.mode = "maxpressure"

    # ------------------------------------------------------------- env + V2X
    emergency_scenario = a.scenario == "emergency"
    env = CoMITEnv(use_gui=a.gui, num_seconds=a.seconds, delta_time=5,
                   demand_density=a.density, mode=("fixed" if a.mode == "fixed" else "rl"),
                   emergency=emergency_scenario, label="demo",
                   ambulance_at=(min(40, a.seconds // 3) if emergency_scenario else None))
    sp = SpatPublisher()
    sp.start()
    em = EmergencyManager(env, mqtt=sp)
    ego = EgoVehicle(env, sp)

    state = {"sensor_fail_until": 0.0, "voice_phase": None,
             "fallback_announced": False, "stop": False}

    def on_cmd(topic, payload):
        import json as js
        msg = js.loads(payload)
        if topic == "v2x/cmd/stop":
            state["stop"] = True
            print("[demo] STOP command received — shutting down gracefully")
            sp.publish_alert("status", {"event": "STOPPED",
                                        "note": "simulation halted by operator"})
            return
        if topic == "v2x/cmd/emergency_ping":
            ok = em.register_ping(msg)
            if ok:
                tr = env._traci
                if em._find_ambulance() is None:
                    tr.vehicle.add("amb-live", "W_E", typeID="ambulance",
                                   depart="now", departLane="free", departSpeed="max")
                print("[demo] EMERGENCY ping accepted — corridor armed")
        elif topic == "v2x/cmd/sensor_fail":
            env.mark_sensor_stale()
            state["sensor_fail_until"] = time.time() + float(msg.get("seconds", 25))
            print("[demo] sensor feed CUT — watchdog will trip in 3s")

    paho_cmd_client(on_cmd)

    if emergency_scenario:
        em.register_ping({"id": EMERGENCY_ID, "speed": 15,
                          "token": sha16(f"{EMERGENCY_ID}:comit-zephyr-2026")})

    def choose_action(obs, ap_state):
        if a.mode == "ppo" and model is not None:
            act, _ = model.predict(obs, deterministic=True)
            return int(act)
        if a.mode == "maxpressure":
            q_ns = ap_state["N"]["queue"] + ap_state["S"]["queue"]
            q_ew = ap_state["E"]["queue"] + ap_state["W"]["queue"]
            return 1 if q_ns >= q_ew else 3
        return 0

    obs, _ = env.reset(seed=2026)
    sp.publish_voice(("welcome_en", "welcome_ta"), cooldown_key="welcome")

    lane_lengths = {}
    impact = {"co2_saved_g": 0.0, "last_t": 0.0}
    torch = None
    if model is not None:
        try:
            import torch  # noqa
        except ImportError:
            torch = None

    def rl_confidence(action_probs_obs):
        """Max action probability of the PPO policy = decision confidence."""
        if model is None or torch is None:
            return None
        try:
            with torch.no_grad():
                t = torch.as_tensor(action_probs_obs, dtype=torch.float32).unsqueeze(0)
                dist = model.policy.get_distribution(t)
                return round(float(dist.distribution.probs[0].max()), 3)
        except Exception:
            return None
    print(f"[demo] running {a.seconds}s of simulation in mode={a.mode} "
          f"scenario={a.scenario} — open http://localhost:5173")
    done = False
    last_wall = time.time()
    while not done:
        ap_state = env._approach_state()

        # scripted scenario hooks
        if a.scenario == "fallback" and 120 <= env.sim_time < 145:
            env.mark_sensor_stale()
        elif state["sensor_fail_until"] and time.time() > state["sensor_fail_until"]:
            env.mark_sensor_ok()
            state["sensor_fail_until"] = 0.0

        action = choose_action(obs, ap_state)
        obs, r, terminated, trunc, info = env.step(action)
        done = terminated or trunc or state["stop"]

        if a.realtime:
            # hold 1x wall-clock pace: 5 sim seconds per decision step
            now = time.time()
            pause = env.delta_time - (now - last_wall)
            if pause > 0:
                time.sleep(pause)
            last_wall = time.time()
        # sensors are fresh at decision time unless explicitly cut
        # (in realtime the wall-clock pause would otherwise look like staleness)
        env.mark_sensor_ok()

        dec = info["safety"]
        em_status = em.update()
        ego.update()
        em_status_approach = None
        if em.preempted and em_status.get("ambulance"):
            from core.emergency import APPROACH_OF_EDGE
            em_status_approach = APPROACH_OF_EDGE.get(em_status["ambulance"]["edge"])

        # ------------------------------------------------------ V2X publish
        # QA: outbound SPaT/lane/KPI go through the latency injector when
        # --v2x-latency is set; emergency alerts stay on the fast path.
        phase = env._traci.trafficlight.getPhase("J")
        phase_state = "green" if phase in (0, 3, 6, 9) else (
            "yellow" if phase in (1, 4, 7, 10) else "allred")
        ped_window = phase in (2, 5, 8, 11)
        tts = max(env._green_start + env.safety.max_green - env.sim_time,
                  env.delta_time)
        fallback = dec.fallback or env.safety_state.fallback_active
        delayed(sp.publish_spat, env._current_green_group, phase_state,
                min(tts, 90), env.sim_time,
                fallback=fallback, emergency=em.preempted)
        delayed(sp.publish_lane_state, info["approach"], env.sim_time)

        # impact metrics vs fixed-time baseline (spec §2.2)
        dt = max(env.sim_time - impact["last_t"], 0.0)
        impact["last_t"] = env.sim_time
        actual_co2_rate = env.episode_metrics["co2"] / max(env.sim_time, 1.0)
        impact["co2_saved_g"] += max(
            (BASELINE["co2_g_per_s"] * a.density - actual_co2_rate) * dt, 0.0)
        base_wait = BASELINE["wait_s"] * a.density
        cur_wait = sum(v["wait"] for v in info["approach"].values()) / 4.0
        wait_red = max((base_wait - cur_wait) / max(base_wait, 1) * 100.0, 0.0)
        conf = rl_confidence(obs)
        delayed(sp.publish_kpi, {
            "sim_time": env.sim_time,
            "vehicles": sum(v["count"] for v in info["approach"].values()),
            "avg_wait": cur_wait,
            "co2_g_s": actual_co2_rate,
            "phase": info.get("phase"),
            "ped_window": ped_window,
            "queue_total": sum(v["queue"] for v in info["approach"].values()),
            "co2_saved_kg": round(impact["co2_saved_g"] / 1000.0, 3),
            "wait_reduction_pct": round(wait_red, 1),
            "rl_confidence": conf,
            "controller": a.mode,
            "v2x_latency_ms": a.v2x_latency})

        # digital-twin vehicle blips (spec §2.1: color-coded by type)
        try:
            vdata_now = env._vehicle_data()
            delayed(sp.client.publish, "v2x/vehicles", _json.dumps(
                {"time_stamp": env.sim_time,
                 "corridor": ({"from": em_status_approach, "to": "E"}
                              if em.preempted and em_status_approach else None),
                 "vehicles": vehicle_map_payload(vdata_now, env._traci, lane_lengths)}))
        except Exception:
            pass

        sp.publish_alert("decision", {
            "event": "decision",
            "rl_action": int(action) if isinstance(action, (int,)) else str(action),
            "executed": dec.action, "overridden": dec.overridden,
            "reason": dec.reason, "fallback": fallback})
        if fallback and not state["fallback_announced"]:
            state["fallback_announced"] = True
            sp.publish_voice(("fallback_en", "fallback_ta"), cooldown_key="fallback1")
        if not fallback:
            state["fallback_announced"] = False
        # voice: red signal ~10 s ahead for the retrofit module
        green_left = (env._green_start + env.delta_time + 2) - env.sim_time
        if (phase_state == "green" and 0 < green_left <= 10
                and state["voice_phase"] != env._green_start):
            state["voice_phase"] = env._green_start
            sp.publish_voice(("red_in_10_en", "red_in_10_ta"),
                             cooldown_key=f"red{env._green_start}")

    m = env.episode_metrics
    print("\n=== episode complete ===")
    print(f"avg wait {m['wait']:.1f}s | avg queue {m['queue']/max(m['steps'],1):.2f} | "
          f"CO2 {m['co2']:.0f}g | emergency wait {m['em_time']:.0f}s | switches {m['switches']}")
    env.close()
    sp.stop()
    if camera_proc:
        camera_proc.terminate()
    if broker_proc:
        broker_proc.terminate()


if __name__ == "__main__":
    main()

