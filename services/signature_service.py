"""
services/signature_service.py — AI Signature Presence Detection
==============================================================
Provides automated verification that uploaded letters contain signatures
in the expected regions (Class Tutor and HOD).
"""

import cv2
import numpy as np
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class SignatureService:
    """Service to detect the presence of digital/handwritten signatures on documents."""

    def verify_signatures(self, file_path: str) -> dict:
        """
        AI check for existence of signatures on the document.
        Logic: Looks for 'ink' (connected components) in the bottom sections of the page.
        """
        try:
            # Check if file exists
            if not Path(file_path).exists():
                return {"valid": False, "error": "File not found"}

            # Read image
            img = cv2.imread(file_path)
            if img is None:
                # If it's a PDF, we'd need a PDF-to-image converter here.
                # For now, we assume PDF might fail or only images are supported.
                return {"valid": False, "error": "Invalid image format"}

            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Inverse threshold (white background becomes black, ink becomes white)
            _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)

            height, width = thresh.shape

            # Define regions of interest (ROI) for signatures (usually bottom part)
            # Tutor signature: Bottom Left
            # HOD signature: Bottom Right

            # Region 1: Class Tutor (Bottom Left: roughly 70-95% vertical, 5-45% horizontal)
            tutor_roi = thresh[
                int(height * 0.7) : int(height * 0.95),
                int(width * 0.05) : int(width * 0.45),
            ]

            # Region 2: HOD (Bottom Right: roughly 70-95% vertical, 55-95% horizontal)
            hod_roi = thresh[
                int(height * 0.7) : int(height * 0.95),
                int(width * 0.55) : int(width * 0.95),
            ]

            tutor_ink = np.sum(tutor_roi > 0)
            hod_ink = np.sum(hod_roi > 0)

            # Threshold for "enough ink" to count as a signature
            min_pixels = 500

            tutor_signed = tutor_ink > min_pixels
            hod_signed = hod_ink > min_pixels

            return {
                "valid": tutor_signed and hod_signed,
                "details": {
                    "tutor_signed": bool(tutor_signed),
                    "hod_signed": bool(hod_signed),
                    "tutor_density": int(tutor_ink),
                    "hod_density": int(hod_ink),
                },
            }

        except Exception as e:
            logger.error(f"Signature verification error: {e}")
            return {"valid": False, "error": str(e)}

    def check_letter_validity(self, file_path: str) -> bool:
        """Helper to return a simple boolean for quick checks."""
        res = self.verify_signatures(file_path)
        return res.get("valid", False)
