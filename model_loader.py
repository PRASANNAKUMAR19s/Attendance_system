# model_loader.py
"""
Downloads trainer.yml and name_map.csv from Firestore on startup.
Called once when the app starts on Render.
"""
import base64
import csv
import logging
import os

logger = logging.getLogger(__name__)


def ensure_model_files():
    """Download model files from Firestore if not present locally."""
    trainer_path = "trainer/trainer.yml"
    name_map_path = "name_map.csv"

    # Already exists (local dev) — skip download
    if os.path.exists(trainer_path) and os.path.exists(name_map_path):
        logger.info("Model files already present locally.")
        return True

    try:
        from firebase_admin import firestore

        db = firestore.client()

        # Download trainer.yml
        os.makedirs("trainer", exist_ok=True)
        doc = db.collection("models").document("trainer").get()
        if not doc.exists:
            logger.error("trainer.yml not found in Firestore!")
            return False

        data = base64.b64decode(doc.to_dict()["data"])
        with open(trainer_path, "wb") as f:
            f.write(data)
        logger.info("✅ trainer.yml downloaded from Firestore")

        # Download name_map.csv
        doc2 = db.collection("models").document("name_map").get()
        if not doc2.exists:
            logger.error("name_map not found in Firestore!")
            return False

        rows = doc2.to_dict()["rows"]
        with open(name_map_path, "w", newline="") as f:
            if rows:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
        logger.info("✅ name_map.csv downloaded from Firestore")

        return True

    except Exception as exc:
        logger.error("Failed to download model files: %s", exc)
        return False
