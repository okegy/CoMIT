"""Benchmark CoMIT controllers: Fixed-Time vs Max-Pressure vs PPO.

Metrics per episode: average vehicle waiting time, average queue length,
CO2 emissions, throughput, emergency wait. Outputs CSV + matplotlib charts.

Usage:
    python train/evaluate.py --episodes 3 --seconds 1200
    python train/evaluate.py --episodes 1 --seconds 600 --quick
"""
import argparse
import os
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                                   # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.env import CoMITEnv                                     # noqa: E402
from stable_baselines3 import PPO                                 # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APPROACHES = ("N", "S", "E", "W")


class MaxPressurePolicy:
    """Classic max-pressure: serve the approach pair with the biggest queue."""
    def __init__(self):
        self.current = 0

    def act(self, obs, ap_state):
        # groups: 0=NS, 2=EW (through+right groups carry the bulk)
        q_ns = ap_state["N"]["queue"] + ap_state["S"]["queue"]
        q_ew = ap_state["E"]["queue"] + ap_state["W"]["queue"]
        return 1 if q_ns >= q_ew else 3     # action 1 -> group0, action 3 -> group2


def run_episode(mode, seconds, density, seed, model=None, gui=False):
    env = CoMITEnv(use_gui=gui, num_seconds=seconds, delta_time=5,
                   demand_density=density, mode=("fixed" if mode == "fixed" else "rl"),
                   out_csv=os.path.join(ROOT, "reports", "benchmark.csv"),
                   label=mode)
    obs, _ = env.reset(seed=seed)
    mp = MaxPressurePolicy()
    done = False
    while not done:
        if mode == "fixed":
            action = 0                      # env runs the fixed SUMO program
        elif mode == "maxpressure":
            action = mp.act(obs, env._approach_state())
        elif mode == "ppo":
            action, _ = model.predict(obs, deterministic=True)
        else:
            raise ValueError(mode)
        obs, r, terminated, trunc, info = env.step(int(action))
        done = terminated or trunc
    m = dict(env.episode_metrics)
    env.close()
    m.update({"mode": mode, "seed": seed, "seconds": seconds})
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--episodes", type=int, default=3)
    ap.add_argument("--seconds", type=int, default=1200)
    ap.add_argument("--density", type=float, default=1.0)
    ap.add_argument("--quick", action="store_true")
    a = ap.parse_args()
    if a.quick:
        a.episodes, a.seconds = 1, 600

    model_path = os.path.join(ROOT, "train", "models", "ppo_comit.zip")
    model = PPO.load(model_path) if os.path.exists(model_path) else None
    modes = ["fixed", "maxpressure"] + (["ppo"] if model else [])

    rows = []
    for mode in modes:
        for ep in range(a.episodes):
            seed = 100 + ep
            print(f"[eval] {mode} episode {ep + 1}/{a.episodes} seed={seed}")
            m = run_episode(mode, a.seconds, a.density, seed, model)
            rows.append(m)
            print(f"       avg_wait={m['wait']:.1f}s queue={m['queue'] / max(m['steps'], 1):.2f} "
                  f"co2={m['co2']:.0f}g arrived={m['arrived']}")

    df = pd.DataFrame(rows)
    df["avg_queue"] = df["queue"] / df["steps"].clip(lower=1)
    out_csv = os.path.join(ROOT, "reports", "benchmark.csv")
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    df.to_csv(out_csv, mode="a", index=False,
              header=not os.path.exists(out_csv))
    summary = df.groupby("mode")[["wait", "avg_queue", "co2", "arrived"]].mean()

    # charts
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.2))
    fig.suptitle("CoMIT Benchmark — Fixed-Time vs Max-Pressure vs RL (PPO)", fontsize=13)
    for ax, (col, title) in zip(axes, [("wait", "Avg waiting time (s)"),
                                       ("avg_queue", "Avg queue length (veh)"),
                                       ("co2", "CO2 emissions (g, total)")]):
        summary[col].plot(kind="bar", ax=ax, color=["#c0392b", "#e67e22", "#27ae60"][:len(summary)])
        ax.set_title(title)
        ax.set_xlabel("")
        ax.tick_params(axis="x", rotation=0)
        for c in ax.containers:
            ax.bar_label(c, fmt="%.1f", fontsize=9)
    out_png = os.path.join(ROOT, "reports", "benchmark.png")
    fig.tight_layout()
    fig.savefig(out_png, dpi=140)
    print("\n=== SUMMARY (mean over episodes) ===")
    print(summary.round(2))
    print(f"charts -> {out_png}\ncsv    -> {out_csv}")


if __name__ == "__main__":
    main()
