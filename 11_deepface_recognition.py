"""
11_deepface_recognition.py — Deep learning recognizer wrapper (optional)
-------------------------------------------------------------------
This is a lightweight wrapper that attempts to use TensorFlow/Keras if
available to produce embeddings for a face ROI. It is intentionally
minimal so projects without TensorFlow can still run.
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class DeepFaceRecognizer:
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path
        self.model = None
        try:
            import tensorflow as tf

            self.tf = tf
        except Exception:
            self.tf = None

    def load_model(self):
        if self.tf is None:
            logger.warning("TensorFlow not available — DeepFaceRecognizer disabled")
            return False
        # Placeholder: user can load a saved model here
        try:
            if self.model_path:
                self.model = self.tf.keras.models.load_model(self.model_path)
                logger.info("Loaded deep model from %s", self.model_path)
                return True
            logger.info(
                "No model_path provided; DeepFaceRecognizer ready for custom loading"
            )
            return True
        except Exception as exc:
            logger.exception("Failed to load deep model: %s", exc)
            return False

    def predict_embedding(self, face_roi) -> Optional[list]:
        if self.tf is None or self.model is None:
            return None
        # Preprocess face_roi according to model requirements (user must adapt)
        try:
            import numpy as np

            img = np.asarray(face_roi).astype("float32") / 255.0
            img = self.tf.image.resize(img, (160, 160))
            img = img[None, ...]
            emb = self.model.predict(img)
            return emb.tolist()
        except Exception:
            logger.exception("Deep embedding prediction failed")
            return None
