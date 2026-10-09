"""Pre-generate all retrofit voice-module audio clips (English + Tamil) via edge-tts.
Run once while online; the demo itself is fully offline afterwards.
MP3s land in assets/audio/ and are copied into dashboard/public/audio/."""
import asyncio
import os
import shutil
import edge_tts

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "audio")

EN = "en-IN-NeerjaNeural"
TA = "ta-IN-PallaviNeural"

CLIPS = {
    "ambulance_approach": {
        "en": "Ambulance approaching. Please move to the left and clear the lane.",
        "ta": "ஆம்புலன்ஸ் வருகிறது. இடப்புறம் நகர்ந்து பாதையை காலி செய்யுங்கள்.",
    },
    "lane_clear": {
        "en": "Please stop and clear the lane for the emergency vehicle.",
        "ta": "அவசர வாகனம் வருவதற்காக நிற்கவும், பாதையை காலி செய்யுங்கள்.",
    },
    "ambulance_cleared": {
        "en": "Thank you. The intersection is now clear.",
        "ta": "நன்றி. சந்திப்பு இப்போது காலியாக உள்ளது.",
    },
    "green_in_10": {
        "en": "Green signal in ten seconds. Get ready to move.",
        "ta": "பத்து வினாடிகளில் பச்சை விளக்கு. செல்ல தயாராகுங்கள்.",
    },
    "red_in_10": {
        "en": "Red signal ahead in ten seconds.",
        "ta": "பத்து வினாடிகளில் சிவப்பு விளக்கு.",
    },
    "welcome": {
        "en": "CoMIT smart intersection system active.",
        "ta": "CoMIT ஸ்மார்ட் சந்திப்பு அமைப்பு செயலில் உள்ளது.",
    },
    "fallback": {
        "en": "System running in safe mode. Fixed time control active.",
        "ta": "அமைப்பு பாதுகாப்பான முறையில் இயங்குகிறது.",
    },
}


async def gen(text, voice, path):
    tts = edge_tts.Communicate(text, voice)
    await tts.save(path)


async def main():
    os.makedirs(OUT, exist_ok=True)
    for name, langs in CLIPS.items():
        for lang, text in langs.items():
            path = os.path.join(OUT, f"{name}_{lang}.mp3")
            try:
                await gen(text, EN if lang == "en" else TA, path)
                print("ok  ", os.path.basename(path))
            except Exception as e:
                print("FAIL", os.path.basename(path), e)
    # mirror into the dashboard's public dir
    pub = os.path.join(ROOT, "dashboard", "public", "audio")
    os.makedirs(pub, exist_ok=True)
    for f in os.listdir(OUT):
        if f.endswith(".mp3"):
            shutil.copy2(os.path.join(OUT, f), os.path.join(pub, f))
    print("copied to dashboard/public/audio")


if __name__ == "__main__":
    asyncio.run(main())
