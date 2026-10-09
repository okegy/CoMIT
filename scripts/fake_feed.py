"""Publishes fake live data to MQTT for dashboard development/screenshots."""
import json, math, random, time
import paho.mqtt.client as mqtt

c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="fake-feed")
c.connect("localhost", 1883)
c.loop_start()
t = 0
groups = {0: "NS through", 1: "NS left", 2: "EW through", 3: "EW left"}
green_cycle = [0, 1, 2, 3]
i = 0
while True:
    t += 1
    g = green_cycle[(t // 8) % 4]
    tts = 8 - (t % 8)
    states = []
    for gi, name in groups.items():
        ev = 6 if gi == g else 3
        states.append({"signal_group": gi + 1, "movement_name": name,
                       "event_state": ev, "min_end_time": tts if gi == g else 12})
    c.publish("v2x/spat/jn1", json.dumps({"intersection_id": 1909, "time_stamp": t,
              "mode": "ADAPTIVE_RL", "states": states}))
    approaches = {a: {"queue": max(0, int(6 + 5 * math.sin(t / 9 + hash(a) % 7))
                      + random.randint(-1, 1)),
                      "wait": 15 + 10 * abs(math.sin(t / 11)),
                      "count": 12, "source": "fused(camera+v2x)"}
                  for a in ("N", "S", "E", "W")}
    c.publish("v2x/lane_state", json.dumps({"intersection_id": 1909,
              "time_stamp": t, "approaches": approaches}))
    c.publish("v2x/kpi", json.dumps({"sim_time": t * 5, "vehicles": 48,
              "avg_wait": 22.5, "co2_g_s": 41.2, "mode": "ADAPTIVE_RL"}))
    time.sleep(1)
