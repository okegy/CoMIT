"""Train the CoMIT RL signal controller with PPO (Stable-Baselines3).

Usage:
    python train/train_ppo.py --timesteps 100000
    python train/train_ppo.py --timesteps 20000 --quick   # pipeline smoke test
"""
import argparse
import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.env import CoMITEnv                                    # noqa: E402
from stable_baselines3 import PPO                                # noqa: E402
from stable_baselines3.common.monitor import Monitor             # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def make_env(gui=False, density=1.0, seconds=3600):
    env = CoMITEnv(use_gui=gui, num_seconds=seconds, delta_time=5,
                   demand_density=density, mode="rl",
                   out_csv=os.path.join(ROOT, "reports", "train_log.csv"))
    return Monitor(env)


def make_vec_envs(n_envs, density, seconds):
    if n_envs <= 1:
        from stable_baselines3.common.vec_env import DummyVecEnv
        return DummyVecEnv([lambda: make_env(density=density, seconds=seconds)])
    from stable_baselines3.common.vec_env import SubprocVecEnv
    return SubprocVecEnv(
        [(lambda: make_env(density=density, seconds=seconds)) for _ in range(n_envs)],
        start_method="spawn")


def linear_schedule(initial):
    def f(progress):
        return initial * progress
    return f


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--timesteps", type=int, default=100_000)
    ap.add_argument("--seconds", type=int, default=1800,
                    help="sim seconds per training episode")
    ap.add_argument("--density", type=float, default=0.8)
    ap.add_argument("--n-envs", type=int, default=4)
    ap.add_argument("--quick", action="store_true", help="tiny smoke-test run")
    a = ap.parse_args()
    if a.quick:
        a.timesteps, a.seconds, a.n_envs = 6000, 600, 2

    out_dir = os.path.join(ROOT, "train", "models")
    os.makedirs(out_dir, exist_ok=True)
    env = make_vec_envs(a.n_envs, a.density, a.seconds)

    model = PPO("MlpPolicy", env, learning_rate=linear_schedule(3e-4),
                n_steps=1024, batch_size=128, gamma=0.95, gae_lambda=0.95,
                ent_coef=0.01, verbose=1, seed=42)
    model.learn(total_timesteps=a.timesteps, progress_bar=False)
    model.save(os.path.join(out_dir, "ppo_comit"))
    print("saved ->", os.path.join(out_dir, "ppo_comit.zip"))
    env.close()


if __name__ == "__main__":
    main()
