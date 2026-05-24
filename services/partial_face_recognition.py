"""
services/partial_face_recognition.py — Partial Face Recognition helpers
---------------------------------------------------------------------
Lightweight heuristics to analyze partially visible faces (eyes/nose) and
provide an explanation / score. This is intentionally dependency-light and
designed as a best-effort enhancement that can be replaced with a proper
landmark-based recognizer later (dlib, mediapipe, deep models, etc.).
"""

from __future__ import annotations

import logging
import cv2
import numpy as np
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Try to load small Haar cascades for eyes / nose if available
_EYE_CASCADE = None
_NOSE_CASCADE = None
try:
    _EYE_CASCADE = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_eye.xml")
except Exception:
    _EYE_CASCADE = None

try:
    _NOSE_CASCADE = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_mcs_nose.xml"
    )
except Exception:
    _NOSE_CASCADE = None


def analyze_face_partial(gray_face: np.ndarray) -> Dict[str, Any]:
    """Analyze a grayscale face ROI and return heuristic features.

    Returns a dict with keys: 'eyes', 'nose', 'partial_score', 'explanation'
    """
    h, w = gray_face.shape[:2]
    result = {"eyes": 0, "nose": 0, "partial_score": 0, "explanation": []}

    # Detect eyes
    try:
        if _EYE_CASCADE is not None and not _EYE_CASCADE.empty():
            eyes = _EYE_CASCADE.detectMultiScale(
                gray_face, scaleFactor=1.1, minNeighbors=3, minSize=(8, 8)
            )
            result["eyes"] = len(eyes)
            if len(eyes) >= 1:
                result["explanation"].append("eyes detected")
    except Exception:
        logger.debug("Eye cascade failed on ROI")

    # Detect nose
    try:
        if _NOSE_CASCADE is not None and not _NOSE_CASCADE.empty():
            noses = _NOSE_CASCADE.detectMultiScale(
                gray_face, scaleFactor=1.1, minNeighbors=4, minSize=(10, 10)
            )
            result["nose"] = len(noses)
            if len(noses) >= 1:
                result["explanation"].append("nose detected")
    except Exception:
        logger.debug("Nose cascade failed on ROI")

    # Simple scoring: eyes count weighted more than nose
    score = min(100, result["eyes"] * 35 + result["nose"] * 25)
    result["partial_score"] = int(score)

    if not result["explanation"]:
        result["explanation"].append("no clear facial landmarks")

    return result
