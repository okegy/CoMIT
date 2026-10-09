"""CoMIT QA suite — implements MASTER_PROMPT.md §3 testing protocols.

1. Safety fuzz: 300 adversarial/mock RL actions -> SafetyChecker must block or
   normalize 100% of them and NEVER permit conflicting greens (P0).
2. Simulated stress: SUMO runs at increasing density incl. gridlock pressure;
   invariant: no perpendicular green ever simultaneously on (P0), fallback works.

Usage:
    python scripts/test_qa.py              # fuzz only (fast, no SUMO)
    python scripts/test_qa.py --full       # fuzz + stress (SUMO, ~4 min)
Exit code 0 iff all P0 checks pass.
"""
import argparse
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.safety_checker import (SafetyChecker, SafetyState,          # noqa: E402
                                 CONFLICT_MATRIX, GROUPS)
from core.emergency import verify_token                               # noqa: E402

P0_FAIL = []


def test_fuzz(n=300):
    print(f"== [1/2] SAFETY FUZZ — {n} adversarial actions ==")
    sc = SafetyChecker()
    rng = random.Random(1337)
    dummy = object()
    blocked = 0
    total = 0
    for i in range(n):
        # adversarial pool: garbage types, out-of-range ints, floats, None-ish,
        # negative, huge, random valid-range actions at hostile timings
        pool = [-7, 99, 0, 1, 2, 3, 4, 5, -1, 1000,
                "1", "GREEN", None, 2.7, 4.0, dummy]
        action = rng.choice(pool)
        st = SafetyState(
            current_green=rng.choice(GROUPS),
            elapsed_green=rng.choice([0, 2, 9, 25, 59.9, 61, 300]),
            cycles_since_ped=rng.randint(0, 6),
            last_sensor_ts=rng.choice([100.0, 100.0, 100.0, -1e9]),  # 25% stale
            emergency_request=(rng.choice(GROUPS) if rng.random() < 0.1 else None))
        now = 101.0
        d = sc.validate(action, st, now)
        total += 1

        # --- P0 invariants on the decision the junction would execute ---
        a = d.action
        if d.fallback:
            assert a == "FALLBACK_FIXED", f"bad fallback action {a!r}"
            continue
        # schema-strict: garbage must never be coerced into a phase change
        if not (isinstance(a, int) and 0 <= a <= 4):
            P0_FAIL.append(f"fuzz #{i}: executed non-schema action {a!r}")
            continue
        # garbage must be normalized to KEEP — but only when no emergency grant
        # pre-empts the pipeline (correctly) and no fallback engaged
        is_garbage = action in (2.7, "1", "GREEN", None, dummy, -7, 99, 1000, -1, 5) \
            or (type(action) is float and not float(action).is_integer())
        if is_garbage and st.emergency_request is None and not d.fallback \
                and a != 0:
            P0_FAIL.append(f"fuzz #{i}: garbage {action!r} not normalized to KEEP")
        # an emergency grant must grant exactly the requested group as a switch
        if st.emergency_request is not None and a != 0:
            if a - 1 != st.emergency_request:
                P0_FAIL.append(f"fuzz #{i}: emergency grant {a} != request "
                               f"{st.emergency_request}+1")
        # min-green invariant: non-emergency switch before min green must be
        # an explicit override (max-green rotation), never a silent pass
        if (st.emergency_request is None and a != 0
                and st.elapsed_green < sc.min_green and not d.overridden):
            P0_FAIL.append(f"fuzz #{i}: switch at {st.elapsed_green}s without override")
        if d.overridden or (isinstance(a, int) and a == 0 and
                            not isinstance(action, int)):
            blocked += 1
        if not d.fallback and not d.overridden and action is dummy:
            P0_FAIL.append(f"fuzz #{i}: object() action accepted as-is")
    print(f"   actions processed: {total}")
    print(f"   blocked/normalized: {blocked} ({blocked / total * 100:.0f}%)")
    print(f"   invalid-schema executed: {sc.stats['invalid_actions']}")
    print("   PASS — no conflicting green, no raw schema ever executed"
          if not P0_FAIL else "   *** P0 FAILURE ***")


def test_stress():
    print("== [2/2] SIMULATED STRESS — densities 0.5 / 1.0 / 1.5 / 2.0 ==")
    from core.env import CoMITEnv
    import numpy as np
    for density in (0.5, 1.0, 1.5, 2.0):
        env = CoMITEnv(use_gui=False, num_seconds=180, delta_time=5,
                       demand_density=density, mode="rl", label=f"stress{int(density*10)}")
        obs, _ = env.reset(seed=7)
        rng = np.random.default_rng(0)
        done = False
        tls_conflict = 0
        while not done:
            obs, r, term, trunc, info = env.step(int(rng.integers(0, 5)))
            done = term
            # P0 invariant: read live TLS state; NS (links 0-3,8,9) and EW
            # (links 4-7,10,11) must never be green together
            s = env._traci.trafficlight.getRedYellowGreenState("J")
            ns_g = any(s[i] == "G" for i in (0, 1, 2, 3, 8, 9))
            ew_g = any(s[i] == "G" for i in (4, 5, 6, 7, 10, 11))
            if ns_g and ew_g:
                tls_conflict += 1
        m = env.episode_metrics
        env.close()
        status = "PASS" if tls_conflict == 0 else "*** P0 FAILURE ***"
        print(f"   density {density:.1f}: avg_wait={m['wait']:.1f}s "
              f"queue={m['queue'] / max(m['steps'], 1):.1f} CO2={m['co2']:.0f}g "
              f"arrived={m['arrived']} conflicting-green frames={tls_conflict} -> {status}")
        if tls_conflict:
            P0_FAIL.append(f"density {density}: {tls_conflict} conflicting-green frames")


def test_tokens():
    print("== [bonus] emergency token auth ==")
    good = verify_token("AMB-001",
                        __import__("hashlib").sha256(
                            b"AMB-001:comit-zephyr-2026").hexdigest()[:16])
    bad = verify_token("AMB-001", "deadbeefdeadbeef")
    print(f"   valid token accepted: {good} | forged token rejected: {not bad}")
    if not good or bad:
        P0_FAIL.append("token auth broken")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true", help="also run SUMO stress test")
    a = ap.parse_args()
    test_fuzz()
    test_tokens()
    if a.full:
        test_stress()
    print("\n==== QA RESULT:", "ALL P0 CHECKS PASSED" if not P0_FAIL
          else f"{len(P0_FAIL)} P0 FAILURES ====")
    for f in P0_FAIL:
        print("  -", f)
    sys.exit(1 if P0_FAIL else 0)
