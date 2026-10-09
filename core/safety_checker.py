"""CoMIT Safety Checker — deterministic guardrail between the RL agent and the junction.

Enforces hard limits regardless of what the RL policy outputs:
  * schema validity of the action
  * minimum / maximum green time
  * yellow + all-red clearance between conflicting movements (conflict matrix)
  * guaranteed pedestrian clearance interval every N cycles
  * sensor watchdog: stale sensor input -> fixed-time fallback
"""
from dataclasses import dataclass, field

# Phase layout in sim/tls.tls.xml (program "comit"):
#   green TLS indices:   0, 3, 6, 9   (== group index * 3)
#   yellow indices:      green + 1
#   all-red indices:     green + 2
# "Group" 0..3 below is the RL/safety-level index of each green movement.
GROUPS = (0, 1, 2, 3)
GROUP_NAME = {0: "NS through+right", 1: "NS left", 2: "EW through+right", 3: "EW left"}

# Which movement groups can be green at the same time (True = conflicting).
# Groups: 0=NS through+right, 1=NS left, 2=EW through+right, 3=EW left
CONFLICT_MATRIX = [
    #  g0     g1     g2     g3
    [False, True,  True,  True ],   # g0 NS through+right : conflicts with NS left, EW through, EW left
    [True,  False, True,  True ],   # g1 NS left          : conflicts with NS through, EW through, EW left
    [True,  True,  False, True ],   # g2 EW through+right : conflicts with NS through, NS left, EW left
    [True,  True,  True,  False],   # g3 EW left          : conflicts with NS through, NS left, EW through
]

KEEP = 0


@dataclass
class SafetyState:
    """Bookkeeping the checker needs about the junction."""
    current_green: int = 0          # group index 0..3 currently green
    elapsed_green: float = 0.0      # seconds since current green started
    cycles_since_ped: int = 0       # completed green phases since last extended ped interval
    last_sensor_ts: float = 0.0     # wall/sim clock of last good sensor frame
    fallback_active: bool = False
    emergency_request: int | None = None  # group index requested green, or None


@dataclass
class SafetyDecision:
    action: int | str               # validated action for the env
    overridden: bool = False
    reason: str | None = None
    ped_interval: bool = False      # next all-red should be extended for pedestrians
    fallback: bool = False
    log: list = field(default_factory=list)


class SafetyChecker:
    def __init__(self, min_green=10.0, max_green=60.0, yellow=3.0, all_red=3.0,
                 ped_all_red=8.0, ped_every=4, sensor_timeout=3.0):
        self.min_green = min_green
        self.max_green = max_green
        self.yellow = yellow
        self.all_red = all_red
        self.ped_all_red = ped_all_red
        self.ped_every = ped_every
        self.sensor_timeout = sensor_timeout
        self.stats = {"overrides": 0, "fallbacks": 0, "invalid_actions": 0,
                      "ped_intervals": 0, "emergency_grants": 0}

    # ------------------------------------------------------------------ core
    def is_conflicting(self, group_a: int, group_b: int) -> bool:
        return CONFLICT_MATRIX[group_a][group_b]

    def validate(self, action, st: SafetyState, now: float) -> SafetyDecision:
        """Return the action the junction is allowed to execute."""
        d = SafetyDecision(action=action)

        # --- watchdog: stale sensors -> deterministic fixed-time fallback ---
        if now - st.last_sensor_ts > self.sensor_timeout:
            self.stats["fallbacks"] += 1
            st.fallback_active = True
            d.fallback = True
            d.overridden = True
            d.action = "FALLBACK_FIXED"
            d.reason = f"sensor data stale {now - st.last_sensor_ts:.1f}s > {self.sensor_timeout}s"
            return d
        st.fallback_active = False

        # --- emergency preemption bypasses min-green (never the conflict rules) ---
        if st.emergency_request is not None and st.current_green != st.emergency_request:
            self.stats["emergency_grants"] += 1
            d.action = st.emergency_request + 1      # encode group as action 1..4
            d.overridden = True
            d.reason = f"EMERGENCY: green requested for group {st.emergency_request}"
            return d

        # --- schema validation (strict: only real integers 0..4 pass) ---
        # operator.index accepts ints + numpy integers, rejects floats/strs/None
        v = None
        try:
            import operator
            v = operator.index(action)
        except (TypeError, ValueError):
            v = None
        if v is None or not 0 <= v <= 4:
            self.stats["invalid_actions"] += 1
            d.overridden = True
            d.action = KEEP
            d.reason = f"invalid action schema ({action!r}) -> keep current phase"
            return d
        action = v

        # --- min green ---
        if action != KEEP and st.elapsed_green < self.min_green:
            self.stats["overrides"] += 1
            d.overridden = True
            d.action = KEEP
            d.reason = f"min green {self.min_green}s not reached ({st.elapsed_green:.1f}s)"
            return d

        # --- max green: force rotation ---
        if action == KEEP and st.elapsed_green >= self.max_green:
            self.stats["overrides"] += 1
            next_group = (st.current_green + 1) % len(GROUPS)
            d.overridden = True
            d.action = next_group + 1             # encode group as action 1..4
            d.reason = f"max green {self.max_green}s reached -> rotating"
            return d

        # --- pedestrian guarantee ---
        if action != KEEP and (st.cycles_since_ped + 1) % self.ped_every == 0:
            d.ped_interval = True
            self.stats["ped_intervals"] += 1
        return d
