"""
services/face_recognition_service.py — Face Recognition Service
===============================================================
Provides real-time face recognition for web-based attendance marking.
Uses LBPH algorithm with OpenCV for face detection and recognition.
"""

from __future__ import annotations

import base64
import io
import logging
import os
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, time as dtime
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

import config as _config

logger = logging.getLogger(__name__)

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False


@dataclass
class DetectedFace:
    reg_no: str
    name: str
    confidence: float
    status: str
    marked: bool = False
    x: int = 0
    y: int = 0
    w: int = 0
    h: int = 0


@dataclass
class PeriodInfo:
    name: str
    start: dtime
    late: dtime
    end: dtime
    status: str


class FaceRecognitionService:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if hasattr(self, "_initialized") and self._initialized:
            return
        
        self._initialized = True
        self._cascade = None
        self._recognizer = None
        self._student_map: Dict[int, Dict[str, Any]] = {}
        self._recently_marked: Dict[int, int] = {}
        self._attendance_cache: Dict[str, set] = {}
        self._present_today: Dict[str, str] = {}  # reg_no -> name (students detected today)
        self._frame_count = 0
        self._camera = None
        self._running = False
        self._stream_thread: Optional[threading.Thread] = None
        self._current_frame: Optional[np.ndarray] = None
        self._frame_lock = threading.Lock()
        self._current_period: Optional[PeriodInfo] = None
        self._detected_faces: List[DetectedFace] = []
        self._last_detection_time = 0
        self._load_model_error = None
        self._load_model()

    def _load_model(self) -> bool:
        try:
            if not os.path.exists(_config.CASCADE_PATH):
                logger.error("Cascade file not found: %s", _config.CASCADE_PATH)
                self._load_model_error = f"Cascade file not found: {_config.CASCADE_PATH}"
                return False
            
            self._cascade = cv2.CascadeClassifier(_config.CASCADE_PATH)
            if self._cascade.empty():
                logger.error("Failed to load cascade classifier")
                self._load_model_error = "Failed to load cascade classifier"
                return False

            self._recognizer = cv2.face.LBPHFaceRecognizer_create()
            
            if not os.path.exists(_config.TRAINER_FILE):
                logger.warning("Trainer file not found: %s", _config.TRAINER_FILE)
                self._load_model_error = f"Trainer file not found: {_config.TRAINER_FILE}"
                return False
            
            self._recognizer.read(_config.TRAINER_FILE)

            if not self._load_student_map():
                logger.warning("Student map empty - train model first")
                self._load_model_error = "Student map empty"
                return False

            logger.info("Face recognition model loaded successfully")
            self._load_model_error = None
            return True
        except cv2.error as exc:
            logger.error("OpenCV error loading model: %s", exc)
            self._load_model_error = str(exc)
            return False
        except Exception as exc:
            logger.error("Error loading model: %s", exc)
            self._load_model_error = str(exc)
            return False

    def get_last_error(self) -> Optional[str]:
        return getattr(self, '_load_model_error', None)

    def _load_student_map(self) -> bool:
        import csv
        try:
            # First, load students.csv to get name -> reg_no mapping
            name_to_regno = {}
            students_file = _config.STUDENTS_FILE
            if os.path.exists(students_file):
                with open(students_file, newline="", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # Handle both column name formats
                        name = row.get("Name") or row.get("name", "")
                        reg_no = row.get("RegNo") or row.get("reg_no", "")
                        if name and reg_no:
                            name_to_regno[name.upper()] = reg_no
            
            # Then load name_map.csv and map face IDs to names + reg_no
            with open(_config.NAME_MAP, newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    face_id = int(row["ID"])
                    name = row["Name"]
                    # Look up reg_no from students using name
                    reg_no = name_to_regno.get(name.upper(), name)  # Fallback to name if not found
                    self._student_map[face_id] = {
                        "reg_no": reg_no,
                        "name": name
                    }
            return len(self._student_map) > 0
        except FileNotFoundError:
            logger.error("name_map.csv not found")
            return False
        except Exception as exc:
            logger.error("Error loading student map: %s", exc)
            return False

    def is_ready(self) -> bool:
        return (
            self._cascade is not None
            and not self._cascade.empty()
            and self._recognizer is not None
            and len(self._student_map) > 0
        )

    def get_current_period(self) -> Optional[PeriodInfo]:
        now = datetime.now().time()
        for name_str, start_str, late_str, end_str in _config.PERIODS:
            start = dtime(*map(int, start_str.split(":")))
            late = dtime(*map(int, late_str.split(":")))
            end = dtime(*map(int, end_str.split(":")))
            if start <= now <= end:
                status = "ON_TIME" if now <= late else "LATE"
                return PeriodInfo(name_str, start, late, end, status)
        return None

    def _is_already_marked(self, reg_no: str, period_name: str) -> bool:
        if period_name not in self._attendance_cache:
            self._attendance_cache[period_name] = set()
            return False
        return str(reg_no) in self._attendance_cache[period_name]

    def mark_attendance(self, reg_no: str, name: str, period_name: str, status: str) -> bool:
        from firebase_service import FirebaseService
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            svc = FirebaseService()
            svc.mark_attendance(reg_no, name, today, period_name, status)
            if period_name not in self._attendance_cache:
                self._attendance_cache[period_name] = set()
            self._attendance_cache[period_name].add(str(reg_no))
            # Track student as present today
            self._present_today[str(reg_no)] = name
            logger.info(f"Marked attendance: {name} ({reg_no}) - {status} for {period_name}")
            return True
        except Exception as exc:
            logger.error(f"Failed to mark attendance: {exc}")
            return False

    def detect_faces_in_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, List[DetectedFace]]:
        if not self.is_ready():
            return frame, []

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self._cascade.detectMultiScale(
            gray,
            scaleFactor=1.3,
            minNeighbors=5,
            minSize=tuple(_config.MIN_FACE_SIZE)
        )

        detected = []
        period = self.get_current_period()
        period_name = period.name if period else None
        period_status = period.status if period else "ON_TIME"

        self._frame_count += 1

        for (x, y, w, h) in faces:
            face_roi = gray[y:y+h, x:x+w]
            try:
                label, confidence = self._recognizer.predict(face_roi)
            except Exception:
                continue

            recognized = confidence < _config.CONFIDENCE_THRESHOLD

            if recognized and label in self._student_map:
                student_info = self._student_map[label]
                reg_no = student_info["reg_no"]
                name = student_info["name"]
            else:
                reg_no = str(label)
                name = "Unknown"

            marked = False
            if recognized and name != "Unknown" and period_name:
                if not self._is_already_marked(reg_no, period_name):
                    self.mark_attendance(reg_no, name, period_name, period_status)
                    self._recently_marked[label] = self._frame_count
                    marked = True

                if label in self._recently_marked:
                    if self._frame_count - self._recently_marked[label] < 30:
                        marked = True

            color = (0, 255, 0)
            status_text = period_status if recognized else f"Conf: {int(confidence)}%"

            if recognized and name != "Unknown":
                if self._is_already_marked(reg_no, period_name):
                    status_text = "ALREADY MARKED"
                    color = (255, 200, 0)
                elif period_status == "ON_TIME":
                    color = (0, 255, 0)
                else:
                    color = (0, 165, 255)
            else:
                color = (0, 0, 255)

            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
            cv2.rectangle(frame, (x, y-35), (x+w, y), color, -1)
            cv2.putText(frame, f"{name} ({int(confidence)}%)", (x+5, y-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(frame, status_text, (x, y+h+22),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            detected.append(DetectedFace(
                reg_no=reg_no,
                name=name,
                confidence=float(confidence),
                status=status_text,
                marked=marked,
                x=int(x), y=int(y), w=int(w), h=int(h)
            ))

        self._detected_faces = detected
        self._last_detection_time = time.time()
        return frame, detected

    def process_frame_base64(self, frame_b64: str) -> Dict[str, Any]:
        try:
            img_data = base64.b64decode(frame_b64.split(",")[1] if "," in frame_b64 else frame_b64)
            nparr = np.frombuffer(img_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if frame is None:
                return {"success": False, "error": "Invalid image data"}

            processed_frame, faces = self.detect_faces_in_frame(frame)
            
            _, buffer = cv2.imencode(".jpg", processed_frame)
            processed_b64 = base64.b64encode(buffer).decode("utf-8")

            return {
                "success": True,
                "frame": f"data:image/jpeg;base64,{processed_b64}",
                "faces": [
                    {
                        "reg_no": f.reg_no,
                        "name": f.name,
                        "confidence": f.confidence,
                        "status": f.status,
                        "marked": f.marked,
                        "bbox": {"x": f.x, "y": f.y, "w": f.w, "h": f.h}
                    }
                    for f in faces
                ],
                "period": {
                    "name": self._current_period.name if self._current_period else None,
                    "status": self._current_period.status if self._current_period else None
                } if self.get_current_period() else None
            }
        except Exception as exc:
            logger.error(f"Error processing frame: {exc}")
            return {"success": False, "error": str(exc)}

    def get_stream_frame(self) -> Optional[bytes]:
        with self._frame_lock:
            if self._current_frame is None:
                return None
            _, buffer = cv2.imencode(".jpg", self._current_frame)
            return buffer.tobytes()

    def generate_frames(self):
        camera = cv2.VideoCapture(0)
        if not camera.isOpened():
            logger.error("Cannot open webcam")
            return

        logger.info("Camera stream started")
        
        while self._running:
            success, frame = camera.read()
            if not success:
                break

            self._current_period = self.get_current_period()
            processed_frame, _ = self.detect_faces_in_frame(frame)
            
            if self._current_period:
                period_info = f"{self._current_period.name} | {self._current_period.status}"
                cv2.rectangle(processed_frame, (0, 0), (processed_frame.shape[1], 50), (30, 30, 30), -1)
                cv2.putText(processed_frame, period_info, (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            _, buffer = cv2.imencode(".jpg", processed_frame)
            frame_bytes = buffer.tobytes()
            
            yield (b"--frame\r\n"
                   b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")
            
            time.sleep(0.03)

        camera.release()
        logger.info("Camera stream stopped")

    def start_stream(self) -> bool:
        if self._running:
            return True
        self._running = True
        self._stream_thread = threading.Thread(target=self._stream_loop, daemon=True)
        self._stream_thread.start()
        return True

    def _stream_loop(self):
        camera = cv2.VideoCapture(0)
        if not camera.isOpened():
            logger.error("Cannot open webcam")
            self._running = False
            return

        logger.info("Camera stream started")
        
        while self._running:
            success, frame = camera.read()
            if not success:
                break

            self._current_period = self.get_current_period()
            processed_frame, _ = self.detect_faces_in_frame(frame)
            
            if self._current_period:
                now_str = datetime.now().strftime("%H:%M:%S")
                period_info = f"{self._current_period.name} | {self._current_period.status} | {now_str}"
                cv2.rectangle(processed_frame, (0, 0), (processed_frame.shape[1], 45), (30, 30, 30), -1)
                cv2.putText(processed_frame, period_info, (10, 28),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            with self._frame_lock:
                self._current_frame = processed_frame
            
            time.sleep(0.03)

        camera.release()
        self._running = False
        logger.info("Camera stream stopped")

    def stop_stream(self):
        self._running = False
        if self._stream_thread and self._stream_thread.is_alive():
            self._stream_thread.join(timeout=2)

    def is_streaming(self) -> bool:
        return self._running

    def get_today_attendance(self) -> Dict[str, int]:
        from firebase_service import FirebaseService
        today = datetime.now().strftime("%Y-%m-%d")
        svc = FirebaseService()
        records = svc.get_attendance(date=today)
        
        stats = {"present": 0, "late": 0, "absent": 0, "total": len(self._student_map)}
        for r in records:
            status = r.get("status", "").upper()
            if status in ("ON_TIME", "PRESENT"):
                stats["present"] += 1
            elif status == "LATE":
                stats["late"] += 1
            elif status == "ABSENT":
                stats["absent"] += 1
        
        stats["marked"] = stats["present"] + stats["late"]
        return stats

    def get_present_students_today(self) -> Dict[str, str]:
        """Return students who were detected (present) today."""
        return self._present_today.copy()

    def detect_early_leaves(self, absent_students: list) -> list:
        """Detect students who left early - they were present earlier but now absent."""
        early_leaves = []
        for student in absent_students:
            reg_no = student.get("reg_no", "")
            name = student.get("name", "")
            if reg_no in self._present_today:
                early_leaves.append({
                    "reg_no": reg_no,
                    "name": name or self._present_today.get(reg_no, "Unknown"),
                    "detected_period": "Earlier Period",
                    "reason": "Left Early - Not Detected in Current Period"
                })
                logger.info(f"Early leave detected: {name} ({reg_no})")
        return early_leaves

    def send_early_leave_notifications(self, early_leaves: list) -> int:
        """Send email notifications for early leave students."""
        from services.email_service import EmailService
        email_service = EmailService()
        sent_count = 0
        
        leave_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        for student in early_leaves:
            # Send to Tutor
            tutor_sent = email_service.send_early_leave_alert(
                to_email=_config.TUTOR_EMAIL,
                student_name=student["name"],
                reg_no=student["reg_no"],
                reason=student["reason"],
                leave_time=leave_time,
            )
            # Send to HOD
            hod_sent = email_service.send_early_leave_alert(
                to_email=_config.HOD_EMAIL,
                student_name=student["name"],
                reg_no=student["reg_no"],
                reason=student["reason"],
                leave_time=leave_time,
            )
            if tutor_sent or hod_sent:
                sent_count += 1
        
        return sent_count

    def clear_today_tracking(self):
        """Clear today's tracking data."""
        self._present_today.clear()
        self._attendance_cache.clear()
