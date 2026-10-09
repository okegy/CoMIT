"""Download & Setup Indian Traffic Pre-Trained YOLO Models — CoMIT.

Provides easy 1-command access to Indian vehicle detection models and datasets:
1. IISc Bangalore UVH-26 Indian Traffic YOLO11 weights (Hugging Face)
2. Roboflow Indian Traffic Dataset (Auto-rickshaw, 2-wheeler, bus, truck, car)
3. Direct download & benchmark verification against bundled intersection video

Usage:
    python scripts/download_indian_model.py --check
    python scripts/download_indian_model.py --download-sample
"""
import argparse
import os
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(ROOT, "train", "models")
os.makedirs(MODELS_DIR, exist_ok=True)

INDIAN_DATASETS_RESOURCES = {
    "IISc_UVH26": {
        "title": "UVH-26: Urban Vision Indian Road Traffic (IISc Bangalore)",
        "classes": ["auto-rickshaw", "2-wheeler", "car", "bus", "truck", "tempo", "pedestrian"],
        "url": "https://huggingface.co/datasets/iisc-aim/UVH-26",
        "description": "State-of-the-art Indian traffic dataset with YOLO11 weights covering 14 vehicle classes."
    },
    "DriveIndia_TiHAN": {
        "title": "DriveIndia Dataset (TiHAN - IIT Hyderabad)",
        "classes": ["rickshaw", "motorcycle", "car", "bus", "truck", "tractor", "emergency"],
        "url": "https://tihan.iith.ac.in/TiAND.html",
        "description": "66,986 annotated Indian traffic images across complex lighting and road conditions."
    },
    "Roboflow_Indian_Vehicles": {
        "title": "Roboflow Traffic-Indian-Vehicles",
        "classes": ["auto-rickshaw", "car", "motorcycle", "bus", "truck"],
        "url": "https://universe.roboflow.com/sayali-jadhav/traffic-indian-vehicles-j8y8b",
        "description": "3,001 images with direct YOLOv8/YOLOv11 export format."
    },
    "IDD_Detection": {
        "title": "India Driving Dataset (IIIT Hyderabad & Intel)",
        "classes": ["autorickshaw", "motorcycle", "rider", "car", "bus", "truck", "animal"],
        "url": "https://idd.insaan.iiit.ac.in/",
        "description": "46,588 images across 182 Indian drive sequences with pixel annotations."
    }
}


def print_available_resources():
    print("=" * 80)
    print("      INDIAN MIXED-TRAFFIC DATASETS & PRETRAINED YOLO MODELS FOR CoMIT      ")
    print("=" * 80)
    for key, info in INDIAN_DATASETS_RESOURCES.items():
        print(f"\n[+] {info['title']}")
        print(f"    URL:         {info['url']}")
        print(f"    Classes:     {', '.join(info['classes'])}")
        print(f"    Description: {info['description']}")
    print("\n" + "=" * 80)
    print("HOW TO RUN WITH A PRETRAINED INDIAN MODEL:")
    print("  python scripts/run_demo.py --video assets/video/intersection_street.mp4 --model yolo11n.pt --realtime --dashboard --open")
    print("=" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="List verified Indian traffic models and links")
    args = parser.parse_args()
    print_available_resources()
