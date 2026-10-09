"""SPaT (Signal Phase and Timing) + alert publisher over MQTT.

Message schema mimics SAE J2735 SPaT as realised in USDOT CARMA-Streets
(event_state: 3=RED, 6=protected-GREEN, 8=protected-YELLOW; timing uses
min_end_time/max_end_time in tenths of a second — simplified to seconds here).
"""
import json
import time
import paho.mqtt.client as mqtt

BROKER = "localhost"
TOPIC_SPAT = "v2x/spat/jn1"
TOPIC_LANE = "v2x/lane_state"
TOPIC_EMERG = "v2x/alert/emergency"
TOPIC_VOICE = "v2x/alert/voice"
TOPIC_KPI = "v2x/kpi"
TOPIC_EGO = "v2x/vehicle/ego"

# traffic-light groups exposed to vehicles (matches tls.tls.xml green groups)
GROUPS = {0: "NS through+right", 1: "NS left", 2: "EW through+right", 3: "EW left"}


class SpatPublisher:
    def __init__(self, broker=BROKER, port=1883, client_id="comit-core"):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,
                                  client_id=client_id, protocol=mqtt.MQTTv311)
        self.client.on_connect = self._on_connect
        self.connected = False
        self.broker = broker
        self.port = port
        self._voice_sent = set()

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        self.connected = reason_code == 0
        print(f"[spat] broker connected: {reason_code}")

    def start(self, retries=20, delay=0.5):
        import time as _t
        for attempt in range(retries):
            try:
                self.client.connect(self.broker, self.port, keepalive=30)
                self.client.loop_start()
                return
            except OSError:
                if attempt == retries - 1:
                    raise
                _t.sleep(delay)

    def stop(self):
        try:
            self.client.loop_stop()
            self.client.disconnect()
        except Exception:
            pass

    # ------------------------------------------------------------------ SPaT
    def publish_spat(self, green_group: int, phase_state: str, time_to_switch: float,
                     sim_time: float, fallback: bool = False, emergency: bool = False):
        """One SPaT frame: every signal group with its current event_state."""
        states = []
        for g, name in GROUPS.items():
            if g == green_group and phase_state == "green":
                event, ttt = 6, time_to_switch
            elif g == green_group and phase_state == "yellow":
                event, ttt = 8, time_to_switch
            else:
                event, ttt = 3, max(time_to_switch, 0)
            states.append({"signal_group": g + 1, "movement_name": name,
                           "event_state": event,
                           "min_end_time": round(ttt, 1)})
        msg = {"intersection_id": 1909, "name": "CoMIT-Jn1",
               "time_stamp": round(sim_time, 1),
               "mode": "FALLBACK_FIXED" if fallback else ("EMERGENCY" if emergency else "ADAPTIVE_RL"),
               "states": states}
        self.client.publish(TOPIC_SPAT, json.dumps(msg), qos=0)
        return msg

    def publish_lane_state(self, fused: dict, sim_time: float):
        self.client.publish(TOPIC_LANE, json.dumps(
            {"intersection_id": 1909, "time_stamp": round(sim_time, 1),
             "approaches": fused}), qos=0)

    def publish_alert(self, kind: str, payload: dict):
        self.client.publish(TOPIC_EMERG, json.dumps(
            {"kind": kind, "ts": time.time(), **payload}), qos=1)

    def publish_voice(self, clips: tuple, cooldown_key=None):
        """clips: (english_clip, tamil_clip) filenames without extension."""
        key = cooldown_key or clips[0]
        if key in self._voice_sent:
            return
        self._voice_sent.add(key)
        self.client.publish(TOPIC_VOICE, json.dumps({
            "en": f"audio/{clips[0]}.mp3", "ta": f"audio/{clips[1]}.mp3"}), qos=1)

    def publish_kpi(self, kpis: dict):
        self.client.publish(TOPIC_KPI, json.dumps(kpis), qos=0)

    def publish_ego(self, ego: dict):
        """Connected-vehicle feed: distance to stop line, time-to-green,
        GLOSA advisory speed — consumed by the in-vehicle cluster UI."""
        self.client.publish(TOPIC_EGO, json.dumps(ego), qos=0)
