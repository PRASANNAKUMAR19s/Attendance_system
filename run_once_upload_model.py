# run_once_upload_model.py
import base64
import csv
import firebase_admin
from firebase_admin import credentials, firestore

# Load your local serviceAccountKey.json
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Upload trainer.yml
print("Uploading trainer.yml...")
with open("trainer/trainer.yml", "rb") as f:
    trainer_data = base64.b64encode(f.read()).decode("utf-8")

db.collection("models").document("trainer").set(
    {"data": trainer_data, "updated_at": "2026-04-21"}
)
print("✅ trainer.yml uploaded to Firestore")

# Upload name_map.csv
print("Uploading name_map.csv...")
rows = []
with open("name_map.csv", newline="") as f:
    reader = csv.DictReader(f)
    rows = [dict(row) for row in reader]

db.collection("models").document("name_map").set({"rows": rows})
print("✅ name_map.csv uploaded to Firestore")
print("🎉 Done! Both files are now in Firestore.")
