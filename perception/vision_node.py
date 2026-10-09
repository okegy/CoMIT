"""Computer Vision Edge Node (Module A camera feed) — v2.

YOLO11n + built-in ByteTrack over an intersection video (file / webcam / RTSP).
Publishes to MQTT:
  v2x/perception/lane      per-approach counts + stop-line queue
  v2x/perception/ped       pedestrian count in the crosswalk band
  v2x/perception/emergency camera-detected emergency-vehicle candidate
  v2x/cmd/emergency_ping   (with --allow-ping) authenticated corridor request

Detection classes (COCO): car 2, motorcycle 3, bus 5, truck 7, person 0.
Note: COCO has no 'auto-rickshaw'/'ambulance' class. Emergency candidates are
flagged as large bright-white bus/truck boxes (ambulance livery heuristic);
fine-tune on an Indian dataset (see docs/REFERENCES.md) to add proper classes.

Usage:
    python perception/vision_node.py --source assets/video/intersection_street.mp4 --loop
    python perception/vision_node.py --source 0 --show
    python perception/vision_node.py --source ... --snapshot reports/cam.jpg
"""
import argparse
import hashlib
import json
import time
import cv2
import numpy as np
import paho.mqtt.client as mqtt

TOPIC = "v2x/perception/lane"
TOPIC_PED = "v2x/perception/ped"
TOPIC_EMERG = "v2x/perception/emergency"
TOPIC_HAZARD = "v2x/alert/hazard"

# Approach ROIs (x1, y1, x2, y2 as frame fractions) calibrated for the bundled
# demo clip assets/video/intersection_street.mp4. Tune per camera.
DEFAULT_ROIS = {
    "N": (0.33, 0.05, 0.66, 0.40),
    "E": (0.60, 0.30, 0.95, 0.65),
    "S": (0.60, 0.66, 0.95, 0.95),
    "W": (0.05, 0.45, 0.40, 0.95),
}
PED_ROI = (0.30, 0.40, 0.70, 0.62)          # crosswalk band near stop line
VEHICLE_CLASSES = [2, 3, 5, 7]
PERSON_CLASS = 0
EMERGENCY_ID = "AMB-CAM-1"


def sha16(s):
    return hashlib.sha256(s.encode()).hexdigest()[:16]


class VisionNode:
    def __init__(self, source, rois=None, show=False, broker="broker.emqx.io",
                 loop=False, snapshot=None, allow_ping=False, ping_once=True):
        self.source = source
        self.rois = rois or DEFAULT_ROIS
        self.show = show
        self.loop = loop
        self.snapshot_path = snapshot
        self.allow_ping = allow_ping
        self.ping_once = ping_once
        self.ping_sent = False
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,
                                  client_id="comit-vision")
        self.client.connect(broker, 1883)
        self.client.loop_start()
        from ultralytics import YOLO
        self.model = YOLO("yolo11n.pt")

    def _roi_px(self, roi, w, h):
        return (int(roi[0] * w), int(roi[1] * h), int(roi[2] * w), int(roi[3] * h))

    def _is_emergency_candidate(self, frame, xyxy, cls):
        """Ambulance livery heuristic: big bus/truck box, bright-white body."""
        if cls not in (5, 7):        # bus / truck
            return False
        x1, y1, x2, y2 = [int(v) for v in xyxy]
        w, h = x2 - x1, y2 - y1
        if w * h < 0.015 * frame.shape[0] * frame.shape[1]:
            return False             # too small to be an ambulance at distance
        patch = frame[y1:y2, x1:x2]
        if patch.size == 0:
            return False
        hsv = cv2.cvtColor(patch, cv2.COLOR_BGR2HSV)
        sat = float(np.mean(hsv[:, :, 1]))
        val = float(np.mean(hsv[:, :, 2]))
        return sat < 55 and val > 175    # white / low-saturation livery

    def run(self):
        cap = cv2.VideoCapture(self.source if isinstance(self.source, int)
                               else str(self.source))
        if not cap.isOpened():
            raise RuntimeError(f"cannot open source {self.source}")
        fps_hint = cap.get(cv2.CAP_PROP_FPS) or 25
        prev_centers = {}
        while True:
            ok, frame = cap.read()
            if not ok:
                if self.loop:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    prev_centers = {}
                    continue
                break
            H, W = frame.shape[:2]
            
            # Phase 2: Simulate Infrastructure Monitoring (Pothole Detection)
            # For hackathon demo, mock a detection in the East approach randomly
            pothole = None
            if time.time() % 15 < 2:  # Active for 2 seconds every 15 seconds
                pothole = {"id": "HAZARD-1", "type": "POTHOLE", "approach": "E", "severity": "HIGH", "bbox": [W*0.7, H*0.4, W*0.75, H*0.45]}

            results = self.model.track(frame, persist=True, tracker="bytetrack.yaml",
                                       verbose=False, conf=0.3)
            boxes = results[0].boxes
            per_approach = {a: {"count": 0, "queue": 0} for a in self.rois}
            ped_count = 0
            emergency = None
            px1, py1, px2, py2 = self._roi_px(PED_ROI, W, H)
            if boxes is not None and boxes.id is not None:
                for xyxy, tid, cls in zip(boxes.xyxy.cpu().numpy(),
                                          boxes.id.int().cpu().tolist(),
                                          boxes.cls.int().cpu().tolist()):
                    cx, cy = (xyxy[0] + xyxy[2]) / 2, (xyxy[1] + xyxy[3]) / 2
                    pc = prev_centers.get(tid)
                    prev_centers[tid] = (cx, cy)
                    if len(prev_centers) > 500:
                        prev_centers.pop(next(iter(prev_centers)))
                    moving = pc is not None and abs(cx - pc[0]) + abs(cy - pc[1]) > 3
                    if cls == PERSON_CLASS:
                        if px1 <= cx <= px2 and py1 <= cy <= py2:
                            ped_count += 1
                        continue
                    # vehicle ROIs
                    for a, roi in self.rois.items():
                        rx1, ry1, rx2, ry2 = self._roi_px(roi, W, H)
                        if rx1 <= cx <= rx2 and ry1 <= cy <= ry2:
                            per_approach[a]["count"] += 1
                            if not moving:
                                per_approach[a]["queue"] += 1
                            if emergency is None and self._is_emergency_candidate(frame, xyxy, cls):
                                emergency = {"id": EMERGENCY_ID, "bbox": [float(v) for v in xyxy],
                                             "confidence": "livery-heuristic"}
                            break

            msg = {"time_stamp": time.time(),
                   "approaches": per_approach,
                   "pedestrians_crossing": ped_count,
                   "source": "camera:yolo11n+bytetrack"}
            self.client.publish(TOPIC, json.dumps(msg))
            self.client.publish(TOPIC_PED, json.dumps(
                {"time_stamp": time.time(), "count": ped_count,
                 "zone": "crosswalk"}))
            if emergency:
                self.client.publish(TOPIC_EMERG, json.dumps(emergency))
                if self.allow_ping and not (self.ping_once and self.ping_sent):
                    self.client.publish("v2x/cmd/emergency_ping", json.dumps(
                        {"id": EMERGENCY_ID, "speed": 12,
                         "token": sha16(f"{EMERGENCY_ID}:comit-zephyr-2026")}))
                    self.ping_sent = True
                    print(f"[vision] emergency candidate -> corridor ping ({EMERGENCY_ID})")
            
            if pothole:
                self.client.publish(TOPIC_HAZARD, json.dumps(pothole))

            annotated = results[0].plot() if (self.show or self.snapshot_path) else None
            if annotated is not None:
                for a, roi in self.rois.items():
                    x1, y1, x2, y2 = self._roi_px(roi, W, H)
                    color = (0, 200, 255)
                    cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(annotated, f"{a}: q={per_approach[a]['queue']}",
                                (x1 + 4, y1 + 18), cv2.FONT_HERSHEY_SIMPLEX,
                                0.55, (0, 255, 255), 1)
                cv2.rectangle(annotated, (px1, py1), (px2, py2), (180, 0, 255), 2)
                cv2.putText(annotated, f"ped={ped_count}", (px1 + 4, py2 - 8),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 120, 255), 1)
                if emergency:
                    e1, e2 = (int(v) for v in emergency["bbox"][:2]), (int(v) for v in emergency["bbox"][2:])
                    cv2.rectangle(annotated, (int(emergency["bbox"][0]), int(emergency["bbox"][1])),
                                  (int(emergency["bbox"][2]), int(emergency["bbox"][3])),
                                  (0, 0, 255), 3)
                    cv2.putText(annotated, "EMERGENCY?", (int(emergency["bbox"][0]), int(emergency["bbox"][1]) - 6),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                if pothole:
                    px1, py1, px2, py2 = [int(v) for v in pothole["bbox"]]
                    cv2.rectangle(annotated, (px1, py1), (px2, py2), (0, 165, 255), 2)  # Orange box
                    cv2.putText(annotated, "POTHOLE", (px1, py1 - 6),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)
                if self.snapshot_path:
                    cv2.imwrite(self.snapshot_path, annotated)
                    print(f"[vision] snapshot -> {self.snapshot_path}")
                    self.snapshot_path = None
                if self.show:
                    cv2.imshow("CoMIT vision node", annotated)
                    if cv2.waitKey(max(1, int(1000 / fps_hint / 2))) & 0xFF == ord('q'):
                        break
        cap.release()
        if self.show:
            cv2.destroyAllWindows()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True, help="video path, '0' for webcam, or RTSP URL")
    ap.add_argument("--show", action="store_true")
    ap.add_argument("--broker", default="broker.emqx.io")
    ap.add_argument("--loop", action="store_true", help="loop the video file")
    ap.add_argument("--snapshot", default=None, help="save one annotated frame to this path")
    ap.add_argument("--allow-ping", action="store_true",
                    help="let a camera-detected emergency request the corridor (authenticated)")
    a = ap.parse_args()
    src = int(a.source) if a.source.isdigit() else a.source
    VisionNode(src, show=a.show, broker=a.broker, loop=a.loop,
               snapshot=a.snapshot, allow_ping=a.allow_ping).run()

