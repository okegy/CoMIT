"""CoMITEnv — Gymnasium environment wrapping the SUMO intersection.

State  (per approach): queue length, cumulative wait; phase one-hot (4 green
                       groups) + elapsed green; emergency flag (ambulance <= 300 m).
Action (discrete 5):   0 = keep phase, 1..4 = switch to green group 0..3.
Reward:                -sum(waiting time) - alpha * stops - beta * emergency delay.
Safety:                every action passes through SafetyChecker before TraCI.

Performance: state extraction uses SUMO *subscriptions* (bulk results in one
call per step) instead of per-vehicle RPCs.
"""
import os
import time
import numpy as np
import gymnasium as gym
from gymnasium import spaces

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sim.sumo_bin import find_sumo                      # noqa: E402
from sim.generate_routes import generate                # noqa: E402
from core.safety_checker import (SafetyChecker, SafetyState, KEEP)  # noqa: E402
from core.fusion import APPROACH_LANES                   # noqa: E402

SIM_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sim")
NET_FILE = os.path.join(SIM_DIR, "intersection.net.xml")

EMERGENCY_RADIUS = 300.0
LANE_OF_APPROACH = {lane: ap for ap, lanes in APPROACH_LANES.items() for lane in lanes}
EDGE_OF_APPROACH = {"N": "N2J", "S": "S2J", "E": "E2J", "W": "W2J"}


class CoMITEnv(gym.Env):
    metadata = {"render_modes": []}

    def __init__(self, use_gui=False, num_seconds=3600, delta_time=5,
                 min_green=10, max_green=60, yellow=3, all_red=3,
                 demand_density=1.0, emergency=False, mode="rl",
                 reward_alpha=0.5, reward_beta=10.0, out_csv=None, label="comit",
                 ambulance_at=None, ambulance_route="W_E"):
        super().__init__()
        self.use_gui = use_gui
        self.num_seconds = num_seconds
        self.delta_time = delta_time
        self.yellow = yellow
        self.all_red = all_red
        self.demand_density = demand_density
        self.emergency_enabled = emergency
        self.mode = mode                      # 'rl' | 'fixed' | 'maxpressure'
        self.reward_alpha = reward_alpha
        self.reward_beta = reward_beta
        self.out_csv = out_csv
        self.label = label
        self.ambulance_at = ambulance_at
        self.ambulance_route = ambulance_route

        self.safety = SafetyChecker(min_green=min_green, max_green=max_green,
                                    yellow=yellow, all_red=all_red)
        self.safety_state = SafetyState()
        self._traci = None
        self._route_file = None
        self.action_space = spaces.Discrete(5)
        # 4 approaches x (queue, wait/60) + phase one-hot(4) + elapsed/60 + emergency
        self.observation_space = spaces.Box(low=0, high=200, shape=(14,), dtype=np.float32)
        self._seed = np.random.randint(0, 2**31 - 1)
        self._veh_subs = set()

    # ------------------------------------------------------------- startup
    def _start_sumo(self):
        import traci
        from traci import constants as tc
        self._tc = tc
        self._route_file = os.path.join(SIM_DIR, f"_routes_{self.label}_{self._seed}.rou.xml")
        generate(self._route_file, seed=int(self._seed), duration=self.num_seconds + 60,
                 density=self.demand_density,
                 ambulance_at=(self.ambulance_at if self.emergency_enabled else None),
                 ambulance_route=self.ambulance_route)
        cmd = [find_sumo(self.use_gui), "-n", NET_FILE, "-r", self._route_file,
               "--step-length", "1.0", "--no-warnings", "true",
               "--time-to-teleport", "300", "--lateral-resolution", "3.2"]
        if self.emergency_enabled:
            cmd += ["--device.bluelight.reactiondist", "100"]
        traci.start(cmd, label=self.label)
        self._traci = traci.getConnection(self.label)

        # bulk subscriptions: lanes + edges (vehicles subscribe on appearance)
        for lanes in APPROACH_LANES.values():
            for lane in lanes:
                self._traci.lane.subscribe(lane, (tc.LAST_STEP_VEHICLE_NUMBER,
                                                  tc.LAST_STEP_VEHICLE_HALTING_NUMBER))
        for edge in EDGE_OF_APPROACH.values():
            self._traci.edge.subscribe(edge, (tc.VAR_CO2EMISSION,))

        traci.trafficlight.setProgram("J", "comit_fixed" if self.mode == "fixed" else "comit")
        traci.trafficlight.setPhase("J", 0)
        traci.trafficlight.setPhaseDuration("J", 10**6)  # env drives durations
        self.sim_time = 0.0
        self._green_start = 0.0
        self._current_green_group = 0
        self._ped_due = False
        self._prev_total_wait = 0.0
        self._prev_total_stops = 0

    # ------------------------------------------------------- state helpers
    def _vehicle_data(self):
        """One bulk call: {veh: {acc_wait, wait, lane, pos, vclass}} + new subs."""
        tc = self._tc
        tr = self._traci
        for v in tr.vehicle.getIDList():
            if v not in self._veh_subs:
                tr.vehicle.subscribe(v, (tc.VAR_ACCUMULATED_WAITING_TIME,
                                         tc.VAR_WAITING_TIME,
                                         tc.VAR_LANE_ID,
                                         tc.VAR_LANEPOSITION,
                                         tc.VAR_VEHICLECLASS))
                self._veh_subs.add(v)
        res = tr.vehicle.getAllSubscriptionResults()
        out = {}
        for v, d in res.items():
            lane = d.get(tc.VAR_LANE_ID, "")
            out[v] = {"acc_wait": d.get(tc.VAR_ACCUMULATED_WAITING_TIME, 0.0),
                      "wait": d.get(tc.VAR_WAITING_TIME, 0.0),
                      "lane": lane,
                      "pos": d.get(tc.VAR_LANEPOSITION, 0.0),
                      "vclass": d.get(tc.VAR_VEHICLECLASS, "passenger")}
        return out

    def _approach_state(self, vdata=None):
        tc = self._tc
        lane_res = self._traci.lane.getAllSubscriptionResults()
        if vdata is None:
            vdata = self._vehicle_data()
        st = {}
        for ap, lanes in APPROACH_LANES.items():
            queue = sum(lane_res.get(l, {}).get(tc.LAST_STEP_VEHICLE_HALTING_NUMBER, 0)
                        for l in lanes)
            count = sum(lane_res.get(l, {}).get(tc.LAST_STEP_VEHICLE_NUMBER, 0)
                        for l in lanes)
            wait = sum(v["acc_wait"] for v in vdata.values()
                       if v["lane"] in lanes)
            st[ap] = {"queue": int(queue), "count": int(count), "wait": wait}
        return st

    def _totals(self, vdata):
        wait = sum(v["acc_wait"] for v in vdata.values())
        stops = sum(1 for v in vdata.values() if v["wait"] > 1.0)
        return wait, stops

    def _emergency_flag(self, vdata=None):
        if vdata is None:
            vdata = self._vehicle_data()
        for v in vdata.values():
            if v["vclass"] != "emergency":
                continue
            lane, pos = v["lane"], v["pos"]
            edge = lane.rsplit("_", 1)[0] if "_" in lane else ""
            if edge in ("N2J", "S2J", "E2J", "W2J"):
                length = self._traci.lane.getLength(lane)
                if length - pos <= EMERGENCY_RADIUS:
                    return 1, edge
            elif edge.startswith("J2"):
                return 1, edge
        return 0, None

    def _observe(self, vdata, ap):
        em, _ = self._emergency_flag(vdata)
        onehot = [1.0 if g == self._current_green_group else 0.0 for g in range(4)]
        obs = []
        for a in ("N", "S", "E", "W"):
            obs += [ap[a]["queue"], ap[a]["wait"] / 60.0]
        obs += onehot + [min((self.sim_time - self._green_start) / 60.0, 1.5), float(em)]
        return np.array(obs, dtype=np.float32), em

    def _green_elapsed(self):
        return self.sim_time - self._green_start

    def _set_green(self, group, duration):
        """Move TLS to green `group` through the yellow + all-red clearance."""
        tl = self._traci.trafficlight
        cur_phase = tl.getPhase("J")
        if cur_phase in (0, 3, 6, 9) and cur_phase != group * 3:
            tl.setPhase("J", cur_phase + 1)          # yellow
            tl.setPhaseDuration("J", self.yellow)
            self._advance(self.yellow)
            tl.setPhase("J", 2)                      # all-red (ped clearance)
            ped = self.safety.ped_all_red if self._ped_due else self.safety.all_red
            tl.setPhaseDuration("J", ped)
            self._advance(ped)
            if self._ped_due:
                self.safety_state.cycles_since_ped = 0
                self._ped_due = False
            else:
                self.safety_state.cycles_since_ped += 1
        elif cur_phase in (1, 4, 7, 10):             # mid-yellow: finish clearance
            self._advance(self.yellow)
            tl.setPhase("J", 2)
            self._advance(self.all_red)
        tl.setPhase("J", group * 3)
        tl.setPhaseDuration("J", max(duration, 1))
        self._current_green_group = group
        self._green_start = self.sim_time
        self.safety_state.current_green = group
        self.safety_state.elapsed_green = 0.0

    def _advance(self, seconds):
        """Step the simulation `seconds` (1 s steps), accumulating reward."""
        r = 0.0
        for _ in range(int(seconds)):
            self._traci.simulationStep()
            self.sim_time += 1.0
            r += self._step_reward()
        return r

    def _step_reward(self):
        vdata = self._vehicle_data()
        w, s = self._totals(vdata)
        dw = w - self._prev_total_wait
        ds = s - self._prev_total_stops
        em, _ = self._emergency_flag(vdata)
        em_pen = self.reward_beta if (em and dw > 0) else 0.0
        self._prev_total_wait = w
        self._prev_total_stops = s
        return -dw - self.reward_alpha * max(ds, 0) - em_pen

    # ------------------------------------------------------------ gym API
    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        if seed is not None:
            self._seed = seed
        else:
            self._seed = np.random.randint(0, 2**31 - 1)
        if self._traci is not None:
            try:
                self._traci.close()
            except Exception:
                pass
            self._veh_subs = set()
        self.safety_state = SafetyState()
        self.safety_state.last_sensor_ts = time.time()
        self.episode_metrics = {"wait": 0.0, "queue": 0.0, "co2": 0.0, "steps": 0,
                                "arrived": 0, "em_time": 0.0, "switches": 0}
        self._start_sumo()
        vdata = self._vehicle_data()
        ap = self._approach_state(vdata)
        obs, _ = self._observe(vdata, ap)
        return obs, {}

    def step(self, action):
        decision = self.safety.validate(action, self.safety_state, time.time())
        a = decision.action

        if decision.fallback:
            self._traci.trafficlight.setProgram("J", "comit_fixed")
            r = self._advance(self.delta_time)
        elif a == KEEP:
            self._traci.trafficlight.setPhaseDuration("J", self.delta_time)
            r = self._advance(self.delta_time)
            self.safety_state.elapsed_green += self.delta_time
        else:
            group = int(a) - 1
            self.episode_metrics["switches"] += 1
            self._set_green(group, self.delta_time + 2)
            r = self._advance(self.delta_time)
            self.safety_state.elapsed_green += self.delta_time

        self.safety_state.last_sensor_ts = time.time()
        vdata = self._vehicle_data()
        ap = self._approach_state(vdata)
        obs, em = self._observe(vdata, ap)
        self._update_metrics(ap, vdata)
        reward = r / self.delta_time
        terminated = self.sim_time >= self.num_seconds
        info = {"safety": decision, "approach": ap, "emergency": em,
                "sim_time": self.sim_time,
                "phase": {0: "NS through+right", 1: "NS left",
                          2: "EW through+right", 3: "EW left"}[self._current_green_group]}
        if terminated:
            self._collect_final_metrics()
            info["episode_metrics"] = self.episode_metrics
            if self.out_csv:
                self._write_csv()
        return obs, reward, terminated, False, info

    def _update_metrics(self, ap, vdata):
        tc = self._tc
        m = self.episode_metrics
        m["steps"] += 1
        m["queue"] += sum(v["queue"] for v in ap.values()) / len(ap)
        edge_res = self._traci.edge.getAllSubscriptionResults()
        for e, d in edge_res.items():
            m["co2"] += d.get(tc.VAR_CO2EMISSION, 0.0) / 1000.0   # mg -> g
        em, _ = self._emergency_flag(vdata)
        if em:
            m["em_time"] += 1.0

    def _collect_final_metrics(self):
        m = self.episode_metrics
        m["arrived"] = self._traci.simulation.getArrivedNumber()
        vdata = self._vehicle_data()
        if vdata:
            m["wait"] = float(np.mean([v["acc_wait"] for v in vdata.values()]))
        else:
            m["wait"] = 0.0

    def _write_csv(self):
        import csv
        m = self.episode_metrics
        new = not os.path.exists(self.out_csv)
        os.makedirs(os.path.dirname(self.out_csv), exist_ok=True)
        with open(self.out_csv, "a", newline="") as f:
            w = csv.writer(f)
            if new:
                w.writerow(["label", "seed", "avg_wait_s", "avg_queue", "co2_g",
                            "arrived", "emergency_wait_s", "switches"])
            w.writerow([self.label, self._seed, round(m["wait"], 2),
                        round(m["queue"] / max(m["steps"], 1), 2),
                        round(m["co2"], 1), m["arrived"], round(m["em_time"], 1),
                        m["switches"]])

    # ------------------------------------------------- manual control (demo)
    def apply_emergency_request(self, group):
        self.safety_state.emergency_request = group

    def clear_emergency_request(self):
        self.safety_state.emergency_request = None

    def mark_sensor_ok(self, ts=None):
        self.safety_state.last_sensor_ts = ts if ts is not None else time.time()

    def mark_sensor_stale(self):
        self.safety_state.last_sensor_ts = -1e9

    def close(self):
        if self._traci is not None:
            try:
                self._traci.close()
            except Exception:
                pass
            self._traci = None

    def render(self):
        pass
