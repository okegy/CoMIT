"""GLOSA — Green Light Optimal Speed Advisory.

Formula follows SUMO's built-in GLOSA device (docs/Simulation/GLOSA.md):
  advised speed = distance-to-stop-line / time-until-green,
  clamped to [min_speed, speed_limit * max_speedfactor].
"""


def advisory_speed(distance_m: float, time_to_green_s: float,
                   speed_limit: float = 13.9, min_speed: float = 5.0,
                   max_speedfactor: float = 1.1) -> dict:
    if time_to_green_s <= 0:
        return {"v": round(speed_limit, 1), "advice": "GO — green now"}
    if distance_m <= 0:
        return {"v": 0.0, "advice": "At stop line — hold"}
    v = distance_m / time_to_green_s
    cap = speed_limit * max_speedfactor
    if v > cap:
        return {"v": round(cap, 1),
                "advice": f"Slow down: green in {time_to_green_s:.0f}s"}
    if v < min_speed:
        return {"v": round(min_speed, 1),
                "advice": f"Green in {time_to_green_s:.0f}s — expect short stop"}
    return {"v": round(v, 1),
            "advice": f"Maintain {v*3.6:.0f} km/h to make the green"}
