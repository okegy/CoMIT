"""Unit tests for the SafetyChecker guardrail. Run: python scripts/test_safety.py"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.safety_checker import SafetyChecker, SafetyState, CONFLICT_MATRIX  # noqa

PASS = FAIL = 0


def check(name, cond):
    global PASS, FAIL
    print(("  PASS  " if cond else "  FAIL  ") + name)
    PASS, FAIL = PASS + (1 if cond else 0), FAIL + (0 if cond else 1)


print("== SafetyChecker unit tests ==")
sc = SafetyChecker(min_green=10, max_green=60, sensor_timeout=3.0)

# 1. conflict matrix is symmetric and perpendicular greens conflict
check("perpendicular greens conflict (g0,g2)",
      sc.is_conflicting(0, 2) and sc.is_conflicting(2, 0))
check("left turns conflict across axis (g1,g3)",
      sc.is_conflicting(1, 3) and sc.is_conflicting(3, 1))
check("no self conflict", not sc.is_conflicting(0, 0))

# 2. schema validation
st = SafetyState(current_green=0, elapsed_green=30, last_sensor_ts=100)
d = sc.validate(99, st, now=101)
check("invalid action -> keep", d.action == 0 and d.overridden)
d = sc.validate("banana", st, now=101)
check("garbage action -> keep", d.action == 0 and d.overridden)

# 3. min green enforced
st = SafetyState(current_green=0, elapsed_green=4, last_sensor_ts=100)
d = sc.validate(3, st, now=101)
check("switch blocked before min green", d.action == 0 and "min green" in d.reason)

# 4. normal switch allowed after min green
st = SafetyState(current_green=0, elapsed_green=25, last_sensor_ts=100)
d = sc.validate(3, st, now=101)
check("switch allowed after min green", d.action == 3 and not d.overridden)

# 5. max green forces rotation
st = SafetyState(current_green=0, elapsed_green=65, last_sensor_ts=100)
d = sc.validate(0, st, now=101)
check("max green forces switch", d.action != 0 and d.overridden)

# 6. emergency request overrides min green
st = SafetyState(current_green=2, elapsed_green=2, emergency_request=0,
                 last_sensor_ts=100)
d = sc.validate(0, st, now=101)
check("emergency grants early green", d.action == 1 and "EMERGENCY" in d.reason)

# 7. watchdog trips on stale sensors
st = SafetyState(current_green=0, elapsed_green=5, last_sensor_ts=90)
d = sc.validate(2, st, now=100)
check("stale sensors -> fallback", d.fallback and d.action == "FALLBACK_FIXED")

# 8. fresh sensors -> no fallback
st = SafetyState(current_green=0, elapsed_green=5, last_sensor_ts=100)
d = sc.validate(2, st, now=101)
check("fresh sensors -> no fallback", not d.fallback)

# 9. pedestrian interval every 4th switch
st = SafetyState(current_green=0, elapsed_green=25, cycles_since_ped=3,
                 last_sensor_ts=100)
d = sc.validate(3, st, now=101)
check("ped interval due on 4th switch", d.ped_interval)

print(f"\n{PASS} passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
