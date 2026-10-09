"""Sensor fusion: unify simulation state + camera perception into one lane-state object.

This is the Module A "single intersection spatial model" — in the full deployment
camera detections (YOLO+ByteTrack) and V2X/GNSS telemetry are merged here; in the
software-only prototype the simulation provides the ground-truth feed and the
perception node provides the camera feed, and both land on the same MQTT topic.
"""
APPROACH_LANES = {
    "N": ["N2J_0", "N2J_1"],
    "S": ["S2J_0", "S2J_1"],
    "E": ["E2J_0", "E2J_1"],
    "W": ["W2J_0", "W2J_1"],
}


def fuse(sim_state: dict, perception: dict | None = None) -> dict:
    """sim_state:  {approach: {queue, wait, count}}
    perception: {approach: {queue, count}}  (optional, from vision node)
    Returns the fused per-approach state; camera queue overrides when fresher."""
    fused = {}
    for approach, s in sim_state.items():
        entry = {
            "queue": s["queue"],
            "wait": round(s["wait"], 1),
            "count": s["count"],
            "source": "v2x+gnss",
        }
        if perception and approach in perception:
            p = perception[approach]
            # camera is ground truth for visible stopped vehicles near the stop line
            entry["queue"] = max(entry["queue"], p.get("queue", 0))
            entry["count"] = max(entry["count"], p.get("count", 0))
            entry["source"] = "fused(camera+v2x)"
        fused[approach] = entry
    return fused
