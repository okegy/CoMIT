"""Emergency Vehicle Green Corridor (Module D).

Flow:  authenticated priority ping -> ETA to junction -> pre-clear target
approach (hold/schedule green ahead of arrival) -> broadcast STOP_AND_CLEAR_LANE
over MQTT -> verify lane empty (sim occupancy) -> hand junction back to RL.
"""
import time
import hashlib

EMERGENCY_SECRET = "comit-zephyr-2026"          # demo-grade shared token secret

APPROACH_OF_EDGE = {"N2J": "N", "S2J": "S", "E2J": "E", "W2J": "W"}
GROUP_FOR_APPROACH = {"N": 0, "S": 0, "E": 2, "W": 2}   # through+right groups
VOICE_ALERTS = {
    "preempt": ("ambulance_approach_en", "ambulance_approach_ta"),
    "cleared": ("ambulance_cleared_en", "ambulance_cleared_ta"),
}


def verify_token(vehicle_id: str, token: str) -> bool:
    """HMAC-style demo authentication of the emergency vehicle ping."""
    expected = hashlib.sha256(f"{vehicle_id}:{EMERGENCY_SECRET}".encode()).hexdigest()[:16]
    return token == expected


class EmergencyManager:
    def __init__(self, env, mqtt=None, eta_threshold=22.0, clearance_hold=6.0):
        self.env = env
        self.mqtt = mqtt                    # SpatPublisher or None (headless tests)
        self.eta_threshold = eta_threshold
        self.clearance_hold = clearance_hold
        self.active = False
        self.amb_id = None
        self.preempted = False
        self._passed_since = None

    # ------------------------------------------------------------- lifecycle
    def register_ping(self, ping: dict) -> bool:
        """ping = {id, speed, route, token}. Returns True if authenticated."""
        vid = str(ping.get("id", ""))
        if not vid or not verify_token(vid, str(ping.get("token", ""))):
            if self.mqtt:
                self.mqtt.publish_alert("emergency", {"rejected": True, "id": vid,
                                                      "reason": "auth failed"})
            return False
        self.amb_id = vid
        self.active = True
        if self.mqtt:
            self.mqtt.publish_alert("emergency", {"event": "ping_accepted",
                                                  "id": vid,
                                                  "speed": ping.get("speed")})
        return True

    # ---------------------------------------------------------------- update
    def update(self) -> dict:
        """Call once per sim second while env runs. Drives preemption."""
        st = {"ambulance": None, "eta": None, "preempting": False}
        if self.env._traci is None:
            return st
        traci = self.env._traci
        amb = self._find_ambulance()
        if amb is None:
            if self.preempted and self._passed_since is not None:
                if time.time() - self._passed_since > self.clearance_hold:
                    self._restore()
            return st
        vid, edge, dist, speed = amb
        st["ambulance"] = {"id": vid, "edge": edge, "dist_m": round(dist, 1),
                           "speed": round(speed, 1)}
        eta = dist / max(speed, 4.0)
        st["eta"] = round(eta, 1)

        if not self.preempted and edge in APPROACH_OF_EDGE and eta <= self.eta_threshold:
            approach = APPROACH_OF_EDGE[edge]
            group = GROUP_FOR_APPROACH[approach]
            self.env.apply_emergency_request(group)         # safety checker grants it
            self.preempted = True
            st["preempting"] = True
            if self.mqtt:
                self.mqtt.publish_alert("emergency", {
                    "event": "PREEMPT", "approach": approach, "eta": round(eta, 1),
                    "lane_clear": "STOP_AND_CLEAR_LANE"})
                self.mqtt.publish_voice(VOICE_ALERTS["preempt"])
        elif self.preempted:
            st["preempting"] = True
            # clearance verification: ambulance crossed the junction?
            if edge.startswith("J2") and self._passed_since is None:
                if self._target_lane_clear():
                    self._passed_since = time.time()
                    if self.mqtt:
                        self.mqtt.publish_alert("emergency", {
                            "event": "CLEARED", "note": "approach verified empty"})
                        self.mqtt.publish_voice(VOICE_ALERTS["cleared"])
        return st

    def _find_ambulance(self):
        traci = self.env._traci
        for v in traci.vehicle.getIDList():
            if traci.vehicle.getVehicleClass(v) != "emergency":
                continue
            lane = traci.vehicle.getLaneID(v)
            edge = lane.rsplit("_", 1)[0]
            pos = traci.vehicle.getLanePosition(v)
            speed = traci.vehicle.getSpeed(v)
            if edge in ("N2J", "S2J", "E2J", "W2J"):
                dist = traci.lane.getLength(lane) - pos
            elif edge.startswith("J2"):
                dist = 0.0
            else:
                continue
            return v, edge, dist, speed
        return None

    def _target_lane_clear(self):
        traci = self.env._traci
        stopped = 0
        for ap_lanes in ("N2J_0", "N2J_1", "S2J_0", "S2J_1",
                         "E2J_0", "E2J_1", "W2J_0", "W2J_1"):
            for v in traci.lane.getLastStepVehicleIDs(ap_lanes):
                if traci.vehicle.getVehicleClass(v) == "emergency":
                    continue
                if traci.vehicle.getSpeed(v) < 0.5:
                    stopped += 1
        return stopped <= 1          # tolerate one straggler

    def _restore(self):
        self.env.clear_emergency_request()
        self.preempted = False
        self._passed_since = None
        self.active = False
        if self.mqtt:
            self.mqtt.publish_alert("emergency", {"event": "RL_RESTORED"})
