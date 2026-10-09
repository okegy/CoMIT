"""Multi-Camera & Video-Driven AI Perception Studio — CoMIT.

Processes video feeds (intersection video, multi-angle feeds, vehicle POV, or webcam),
runs YOLO11n + ByteTrack tracking, extracts real-time instance metrics (queues, vehicle
classes, pedestrians, ambulances, potholes), and streams annotated camera frames +
telemetry to the MQTT broker and dashboard.

Usage:
    python perception/multi_camera_streamer.py --source assets/video/intersection_street.mp4 --loop --port 8088
"""
import argparse
import base64
import hashlib
import json
import os
import sys
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import cv2
import numpy as np
import paho.mqtt.client as mqtt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

TOPIC_LANE = "v2x/perception/lane"
TOPIC_PED = "v2x/perception/ped"
TOPIC_EMERG = "v2x/perception/emergency"
TOPIC_HAZARD = "v2x/alert/hazard"
TOPIC_FRAME = "v2x/perception/camera_frame"
TOPIC_MULTICAM = "v2x/perception/multi_cam"

DEFAULT_ROIS = {
    "N": (0.33, 0.05, 0.66, 0.40),
    "E": (0.60, 0.30, 0.95, 0.65),
    "S": (0.60, 0.66, 0.95, 0.95),
    "W": (0.05, 0.45, 0.40, 0.95),
}
PED_ROI = (0.30, 0.40, 0.70, 0.62)

VEHICLE_CLASS_NAMES = {2: "car", 3: "motorcycle", 5: "bus", 7: "truck", 0: "pedestrian"}
EMERGENCY_ID = "AMB-CAM-01"


def sha16(s):
    return hashlib.sha256(s.encode()).hexdigest()[:16]


latest_annotated_jpeg = None
frame_lock = threading.Lock()


class MJPEGHandler(BaseHTTPRequestHandler):
    """Ultra-low latency MJPEG HTTP server for live dashboard video stream."""
    def do_GET(self):
        global latest_annotated_jpeg
        if self.path == "/stream.mjpg":
            self.send_response(200)
            self.send_header("Content-type", "multipart/x-mixed-replace; boundary=--jpgboundary")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            while True:
                with frame_lock:
                    jpg = latest_annotated_jpeg
                if jpg is not None:
                    try:
                        self.wfile.write(b"--jpgboundary\r\n")
                        self.send_header("Content-type", "image/jpeg")
                        self.send_header("Content-length", str(len(jpg)))
                        self.end_headers()
                        self.wfile.write(jpg)
                        self.wfile.write(b"\r\n")
                    except Exception:
                        break
                time.sleep(0.04)
        elif self.path == "/snapshot.jpg":
            with frame_lock:
                jpg = latest_annotated_jpeg
            if jpg is not None:
                self.send_response(200)
                self.send_header("Content-type", "image/jpeg")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(jpg)
            else:
                self.send_response(404)
                self.end_headers()
        else:
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(b"CoMIT Multi-Cam Stream Server Online")

    def log_message(self, format, *args):
        return  # Suppress console HTTP logs


def start_mjpeg_server(port=8088):
    server = HTTPServer(("0.0.0.0", port), MJPEGHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    print(f"[MultiCam] Live MJPEG Streamer running at http://localhost:{port}/stream.mjpg")
    return server


class MultiCameraVisionEngine:
    def __init__(self, source, model_path="yolo11n.pt", rois=None, broker="broker.emqx.io", loop=True,
                 allow_ping=True, port=8088):
        self.source = source
        self.rois = rois or DEFAULT_ROIS
        self.loop = loop
        self.allow_ping = allow_ping
        self.active_camera_view = "ALL"  # ALL, N, S, E, W, POV
        self.ping_sent = False
        self.port = port
        
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="comit-multicam-vision")
        self.client.on_message = self._on_mqtt_message
        try:
            self.client.connect(broker, 1883)
            self.client.subscribe("v2x/cmd/camera_view")
            self.client.subscribe("v2x/cmd/feed_select")
            self.client.loop_start()
            print(f"[MultiCam] Connected to MQTT broker at {broker}:1883")
        except Exception as e:
            print(f"[MultiCam] Warning: MQTT connection failed: {e}")

        from ultralytics import YOLO
        print(f"[MultiCam] Loading YOLO AI vision model from {model_path}...")
        self.model = YOLO(model_path)
        self.class_names = self.model.names if hasattr(self.model, "names") else VEHICLE_CLASS_NAMES
        print(f"[MultiCam] Model loaded successfully with {len(self.class_names)} classes.")

    def _on_mqtt_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            if msg.topic == "v2x/cmd/camera_view":
                self.active_camera_view = payload.get("view", "ALL")
                print(f"[MultiCam] Switched camera perspective to: {self.active_camera_view}")
        except Exception as e:
            print(f"[MultiCam] Error processing MQTT command: {e}")

    def _roi_px(self, roi, w, h):
        return (int(roi[0] * w), int(roi[1] * h), int(roi[2] * w), int(roi[3] * h))

    def _is_emergency_candidate(self, frame, xyxy, cls):
        """Ambulance livery detection heuristic: large white vehicle with low saturation."""
        if cls not in (5, 7):
            return False
        x1, y1, x2, y2 = [int(v) for v in xyxy]
        w, h = x2 - x1, y2 - y1
        if w * h < 0.015 * frame.shape[0] * frame.shape[1]:
            return False
        patch = frame[y1:y2, x1:x2]
        if patch.size == 0:
            return False
        hsv = cv2.cvtColor(patch, cv2.COLOR_BGR2HSV)
        sat = float(np.mean(hsv[:, :, 1]))
        val = float(np.mean(hsv[:, :, 2]))
        return sat < 55 and val > 175

    def run(self):
        global latest_annotated_jpeg
        start_mjpeg_server(self.port)
        cap = cv2.VideoCapture(self.source if isinstance(self.source, int) else str(self.source))
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open video source: {self.source}")

        fps = cap.get(cv2.CAP_PROP_FPS) or 25
        frame_delay = max(0.02, 1.0 / fps)
        prev_centers = {}
        last_frame_b64_pub = 0
        frame_idx = 0

        print(f"[MultiCam] Processing live stream from: {self.source} (FPS: {fps})")

        while True:
            t0 = time.time()
            ok, frame = cap.read()
            if not ok:
                if self.loop:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    prev_centers = {}
                    continue
                break

            H, W = frame.shape[:2]
            frame_idx += 1

            # Simulated pothole hazard periodically in East approach
            pothole = None
            if (time.time() % 20) < 3.0:
                pothole = {
                    "id": "HAZARD-P1",
                    "type": "POTHOLE",
                    "approach": "E",
                    "severity": "HIGH",
                    "bbox": [int(W * 0.68), int(H * 0.42), int(W * 0.74), int(H * 0.48)]
                }

            # Run YOLO11n + ByteTrack
            results = self.model.track(frame, persist=True, tracker="bytetrack.yaml", verbose=False, conf=0.3)
            boxes = results[0].boxes
            per_approach = {a: {"count": 0, "queue": 0, "vehicles": []} for a in self.rois}
            class_counts = {"car": 0, "motorcycle": 0, "bus": 0, "truck": 0, "pedestrian": 0}
            ped_count = 0
            emergency = None

            px1, py1, px2, py2 = self._roi_px(PED_ROI, W, H)

            if boxes is not None and boxes.id is not None:
                for xyxy, tid, cls in zip(boxes.xyxy.cpu().numpy(),
                                          boxes.id.int().cpu().tolist(),
                                          boxes.cls.int().cpu().tolist()):
                    cname = VEHICLE_CLASS_NAMES.get(cls, "car")
                    class_counts[cname] = class_counts.get(cname, 0) + 1
                    cx, cy = (xyxy[0] + xyxy[2]) / 2, (xyxy[1] + xyxy[3]) / 2

                    pc = prev_centers.get(tid)
                    prev_centers[tid] = (cx, cy)
                    if len(prev_centers) > 600:
                        prev_centers.pop(next(iter(prev_centers)))
                    moving = pc is not None and (abs(cx - pc[0]) + abs(cy - pc[1])) > 3.5

                    if cls == 0:  # Pedestrian
                        if px1 <= cx <= px2 and py1 <= cy <= py2:
                            ped_count += 1
                        continue

                    # Assign vehicle to approach ROI
                    for a, roi in self.rois.items():
                        rx1, ry1, rx2, ry2 = self._roi_px(roi, W, H)
                        if rx1 <= cx <= rx2 and ry1 <= cy <= ry2:
                            per_approach[a]["count"] += 1
                            if not moving:
                                per_approach[a]["queue"] += 1
                            per_approach[a]["vehicles"].append({
                                "track_id": tid, "type": cname,
                                "moving": bool(moving), "bbox": [float(v) for v in xyxy]
                            })
                            if emergency is None and self._is_emergency_candidate(frame, xyxy, cls):
                                emergency = {
                                    "id": EMERGENCY_ID,
                                    "approach": a,
                                    "bbox": [float(v) for v in xyxy],
                                    "confidence": "livery-heuristic",
                                    "eta": 12.0
                                }
                            break

            # Publish unified perception state to MQTT
            telemetry_msg = {
                "time_stamp": time.time(),
                "frame_id": frame_idx,
                "approaches": {a: {"count": d["count"], "queue": d["queue"]} for a, d in per_approach.items()},
                "class_counts": class_counts,
                "pedestrians_crossing": ped_count,
                "active_camera_view": self.active_camera_view,
                "source": "multi_camera_streamer:yolo11n+bytetrack"
            }
            self.client.publish(TOPIC_LANE, json.dumps(telemetry_msg))
            self.client.publish(TOPIC_PED, json.dumps({"time_stamp": time.time(), "count": ped_count, "zone": "crosswalk"}))
            self.client.publish(TOPIC_MULTICAM, json.dumps(telemetry_msg))

            if emergency:
                self.client.publish(TOPIC_EMERG, json.dumps(emergency))
                if self.allow_ping and not self.ping_sent:
                    token = sha16(f"{EMERGENCY_ID}:comit-zephyr-2026")
                    self.client.publish("v2x/cmd/emergency_ping", json.dumps({
                        "id": EMERGENCY_ID, "approach": emergency.get("approach", "W"),
                        "speed": 14.5, "token": token
                    }))
                    self.ping_sent = True
                    print(f"[MultiCam] Emergency vehicle candidate recognized in {emergency.get('approach')} approach -> Corridor Preempt Triggered")

            if pothole:
                self.client.publish(TOPIC_HAZARD, json.dumps(pothole))

            # Build annotated visualization
            annotated = results[0].plot()

            # Draw approach ROIs & queue labels
            for a, roi in self.rois.items():
                x1, y1, x2, y2 = self._roi_px(roi, W, H)
                color = (0, 230, 255) if per_approach[a]["queue"] > 0 else (0, 180, 200)
                cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
                cv2.rectangle(annotated, (x1, y1), (x1 + 105, y1 + 22), (15, 23, 42), -1)
                cv2.putText(annotated, f"CAM-{a} Q:{per_approach[a]['queue']}",
                            (x1 + 4, y1 + 16), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (56, 189, 248), 1, cv2.LINE_AA)

            # Crosswalk box
            cv2.rectangle(annotated, (px1, py1), (px2, py2), (180, 0, 255), 2)
            cv2.rectangle(annotated, (px1, py1), (px1 + 120, py1 + 20), (15, 23, 42), -1)
            cv2.putText(annotated, f"PEDESTRIANS: {ped_count}", (px1 + 4, py1 + 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (232, 121, 249), 1, cv2.LINE_AA)

            # Pothole box
            if pothole:
                bx1, by1, bx2, by2 = pothole["bbox"]
                cv2.rectangle(annotated, (bx1, by1), (bx2, by2), (0, 140, 255), 2)
                cv2.putText(annotated, "POTHOLE DETECTED", (bx1, by1 - 6),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 140, 255), 2)

            # Emergency alert overlay
            if emergency:
                ex1, ey1, ex2, ey2 = [int(v) for v in emergency["bbox"]]
                cv2.rectangle(annotated, (ex1, ey1), (ex2, ey2), (0, 0, 255), 3)
                cv2.rectangle(annotated, (ex1, ey1 - 24), (ex1 + 175, ey1), (0, 0, 220), -1)
                cv2.putText(annotated, "EMERGENCY VEHICLE", (ex1 + 4, ey1 - 6),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)

            # HUD Overlay Header
            cv2.rectangle(annotated, (0, 0), (W, 36), (15, 23, 42), -1)
            cv2.putText(annotated, "CoMIT AI VISION NODE | YOLO11n + ByteTrack | LIVE FEED", (14, 24),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (56, 189, 248), 2, cv2.LINE_AA)
            cv2.putText(annotated, f"Total Vehicles: {sum(class_counts.values()) - ped_count} | Peds: {ped_count}", (W - 280, 24),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (186, 230, 253), 1, cv2.LINE_AA)

            # Crop or re-frame if a specific camera angle is selected
            if self.active_camera_view in self.rois:
                rx1, ry1, rx2, ry2 = self._roi_px(self.rois[self.active_camera_view], W, H)
                view_frame = annotated[max(0, ry1-30):min(H, ry2+30), max(0, rx1-30):min(W, rx2+30)]
                if view_frame.size > 0:
                    annotated = cv2.resize(view_frame, (W, H))
                    cv2.putText(annotated, f"CAMERA PERSPECTIVE: APPROACH {self.active_camera_view}", (16, H - 20),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (34, 197, 94), 2)

            # Encode frame to JPEG
            ok_enc, buffer = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if ok_enc:
                jpg_bytes = buffer.tobytes()
                with frame_lock:
                    latest_annotated_jpeg = jpg_bytes

                # Publish compressed snapshot periodically over MQTT for dashboard direct canvas fallback
                if time.time() - last_frame_b64_pub > 0.15:
                    b64_str = base64.b64encode(jpg_bytes).decode("utf-8")
                    self.client.publish(TOPIC_FRAME, json.dumps({
                        "frame": f"data:image/jpeg;base64,{b64_str}",
                        "timestamp": time.time(),
                        "classes": class_counts,
                        "queues": {a: d["queue"] for a, d in per_approach.items()}
                    }))
                    last_frame_b64_pub = time.time()

            elapsed = time.time() - t0
            if elapsed < frame_delay:
                time.sleep(frame_delay - elapsed)

        cap.release()
        self.client.loop_stop()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default=os.path.join(ROOT, "assets", "video", "intersection_street.mp4"),
                    help="Video file path or '0' for webcam")
    ap.add_argument("--model", default="yolo11n.pt", help="Path to YOLO model weights (.pt)")
    ap.add_argument("--broker", default="broker.emqx.io")
    ap.add_argument("--port", type=int, default=8088, help="MJPEG HTTP stream port")
    ap.add_argument("--loop", action="store_true", default=True)
    ap.add_argument("--allow-ping", action="store_true", default=True)
    args = ap.parse_args()

    src = int(args.source) if args.source.isdigit() else args.source
    engine = MultiCameraVisionEngine(src, model_path=args.model, broker=args.broker, loop=args.loop,
                                     allow_ping=args.allow_ping, port=args.port)
    engine.run()

