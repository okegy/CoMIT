"""Generate mixed-traffic route files for the CoMIT intersection.

Indian-style mixed traffic: cars, motorcycles, auto-rickshaws, buses, trucks,
plus an optional ambulance (emergency vType with bluelight device).
Output paths are constrained to this sim/ directory (no traversal).
"""
import os
import random
import argparse

VTYPES = """
    <vType id="car" vClass="passenger" length="4.3" maxSpeed="16.7" accel="2.6" decel="4.5" sigma="0.5" color="0.3,0.55,0.9"/>
    <vType id="moto" vClass="motorcycle" length="2.0" maxSpeed="15.0" accel="3.5" decel="5.0" sigma="0.6" latAlignment="arbitrary" color="0.9,0.7,0.2"/>
    <vType id="auto" vClass="passenger" length="2.9" minGap="0.8" maxSpeed="11.2" accel="1.8" decel="4.0" sigma="0.5" color="0.95,0.85,0.1"/>
    <vType id="bus" vClass="bus" length="12.0" maxSpeed="12.5" accel="1.2" decel="3.5" sigma="0.4" color="0.2,0.65,0.35"/>
    <vType id="truck" vClass="truck" length="8.0" maxSpeed="12.0" accel="1.3" decel="3.8" sigma="0.4" color="0.55,0.55,0.6"/>
    <vType id="ambulance" vClass="emergency" length="6.5" maxSpeed="22.0" accel="2.8" decel="6.0" sigma="0.2"
           guiShape="emergency" color="1,1,1">
        <param key="has.bluelight.device" value="true"/>
    </vType>
"""

# 12 movement routes through the junction
ROUTES = {
    "W_E": "W2J J2E", "W_N": "W2J J2N", "W_S": "W2J J2S",
    "E_W": "E2J J2W", "E_N": "E2J J2N", "E_S": "E2J J2S",
    "N_S": "N2J J2S", "N_E": "N2J J2E", "N_W": "N2J J2W",
    "S_N": "S2J J2N", "S_E": "S2J J2E", "S_W": "S2J J2W",
}

# vehicle mix (Indian intersection flavour)
MIX = [("moto", 0.34), ("car", 0.30), ("auto", 0.18), ("bus", 0.06), ("truck", 0.12)]


def sample_type(rng):
    r = rng.random()
    acc = 0.0
    for vt, p in MIX:
        acc += p
        if r <= acc:
            return vt
    return "car"


def generate(out_path, seed=42, duration=3600, density=1.0, ambulance_at=None,
             ambulance_route="W_E"):
    """Write a route file.

    density: multiplier on demand (1.0 ~ 700 veh/h per approach pair scaled below)
    ambulance_at: second at which an ambulance departs (None = no ambulance)
    """
    rng = random.Random(seed)
    lines = ['<routes>', VTYPES]
    for rid, edges in ROUTES.items():
        lines.append(f'    <route id="{rid}" edges="{edges}"/>')

    # collect vehicles then sort by departure (SUMO ignores unsorted files)
    # ~1300 veh/h at density 1.0 — busy intersection, queues form at red
    vehicles = []
    depart = 0.0
    period_base = 3600.0 / (1300.0 * density)
    i = 0
    while depart < duration:
        origin = rng.choice(["W", "E", "N", "S"])
        dests = [d for d in ["E", "W", "N", "S"] if d != origin]
        rid = f"{origin}_{rng.choice(dests)}"
        vt = sample_type(rng)
        vehicles.append((depart,
                         f'    <vehicle id="veh_{i}" type="{vt}" route="{rid}" '
                         f'depart="{depart:.1f}" departSpeed="max" departLane="free"/>'))
        i += 1
        depart += period_base * rng.uniform(0.5, 1.5)

    if ambulance_at is not None:
        vehicles.append((ambulance_at,
                         f'    <vehicle id="amb1" type="ambulance" route="{ambulance_route}" '
                         f'depart="{ambulance_at}" departSpeed="max" departLane="free"/>'))

    for _, xml in sorted(vehicles, key=lambda v: v[0]):
        lines.append(xml)

    lines.append('</routes>')
    # write only inside this project's sim/ directory; reject traversal
    safe_dir = os.path.abspath(os.path.dirname(__file__))
    target = os.path.abspath(out_path)
    if not target.startswith(safe_dir + os.sep):
        raise ValueError(f"route output must stay inside {safe_dir}, got {out_path!r}")
    with open(target, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return target


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="sim/routes.rou.xml")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--duration", type=int, default=3600)
    ap.add_argument("--density", type=float, default=1.0)
    ap.add_argument("--ambulance-at", type=int, default=None)
    ap.add_argument("--ambulance-route", default="W_E")
    a = ap.parse_args()
    print("wrote", generate(a.out, a.seed, a.duration, a.density,
                           a.ambulance_at, a.ambulance_route))
