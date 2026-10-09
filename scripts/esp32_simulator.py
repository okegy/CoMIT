"""ESP32 + DFPlayer retrofit voice module — SOFTWARE SIMULATOR.

Behaves exactly like the planned hardware box (ESP32 + DFPlayer Mini + speaker):
subscribes to v2x/alert/voice over MQTT and "plays" the numbered clip,
printing the same serial log the firmware would emit. On this laptop the clip
is opened through the OS default player path (pygame if available; otherwise
log-only — the dashboard's voice console always plays audio too).

Hardware swap-in (no code changes): flash an ESP32 with the same MQTT
subscription, put assets/audio/*.mp3 numbered 0001..0014 on a FAT32 microSD in
a DFPlayer Mini, and point it at the same broker. See docs/REFERENCES.md.
"""
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIO = os.path.join(ROOT, "assets", "audio")

CLIP_INDEX = {name: i + 1 for i, name in enumerate(
    ["welcome", "ambulance_approach", "lane_clear", "ambulance_cleared",
     "green_in_10", "red_in_10", "fallback"])}


def find_clip(path_fragment):
    """path_fragment like 'audio/ambulance_approach_ta.mp3' -> local file."""
    base = os.path.basename(path_fragment)
    local = os.path.join(AUDIO, base)
    if os.path.exists(local):
        return local
    stem = base.replace(".mp3", "").rsplit("_", 1)[0]
    return os.path.join(AUDIO, f"{stem}_en.mp3") if os.path.exists(
        os.path.join(AUDIO, f"{stem}_en.mp3")) else None


def play(local_path):
    try:
        import pygame
        pygame.mixer.init()
        pygame.mixer.music.load(local_path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
    except Exception:
        try:
            os.startfile(local_path)     # Windows default player
        except Exception:
            pass                          # log-only mode


def main():
    import paho.mqtt.client as mqtt
    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="esp32-voicebox")
    c.on_message = lambda cl, u, m: on_voice(m.payload)
    c.connect("localhost", 1883)
    c.loop_start()
    c.subscribe("v2x/alert/voice")
    print("[esp32] retrofit voice module ONLINE — waiting for alerts "
          "(hardware swap: ESP32 + DFPlayer Mini, same MQTT topic)")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass


def on_voice(payload):
    msg = json.loads(payload)
    local = find_clip(msg.get("ta") or msg.get("en") or "")
    if not local:
        print("[esp32] unknown clip", msg)
        return
    stem = os.path.basename(local).replace(".mp3", "").rsplit("_", 1)[0]
    idx = CLIP_INDEX.get(stem, 0)
    print(f"[esp32] serial> DFPlayer: play track {idx:04d}.mp3  ({stem})")
    print(f"[esp32]         vol=22/30 lang={'TA+EN' if '_ta' in os.path.basename(local) else 'EN'}")
    play(local)


if __name__ == "__main__":
    sys.exit(main())
