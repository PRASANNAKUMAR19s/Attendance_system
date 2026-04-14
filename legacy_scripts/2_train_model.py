import cv2
import numpy as np
import os
import csv
from PIL import Image

DATASET_DIR  = "dataset"
TRAINER_DIR  = "trainer"
TRAINER_FILE = "trainer/trainer.yml"
NAME_MAP     = "name_map.csv"

def get_images_and_labels():
    face_samples = []
    ids          = []
    name_to_id   = {}
    current_id   = 1

    student_folders = [
        f for f in os.listdir(DATASET_DIR)
        if os.path.isdir(os.path.join(DATASET_DIR, f))
    ]

    if not student_folders:
        print("[ERROR] No student folders found in /dataset/")
        return [], []

    for student_name in student_folders:
        folder_path = os.path.join(DATASET_DIR, student_name)

        if student_name not in name_to_id:
            name_to_id[student_name] = current_id
            current_id += 1

        student_id = name_to_id[student_name]

        for img_file in os.listdir(folder_path):
            if not img_file.lower().endswith((".jpg", ".jpeg", ".png")):
                continue
            img_path = os.path.join(folder_path, img_file)
            pil_img  = Image.open(img_path).convert("L")
            img_arr  = np.array(pil_img, dtype=np.uint8)
            face_samples.append(img_arr)
            ids.append(student_id)
            print(f"  [LOADED] {student_name} → {img_file}")

    with open(NAME_MAP, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Name"])
        for name, sid in name_to_id.items():
            writer.writerow([sid, name])

    print(f"\n  [SAVED] Name map → {NAME_MAP}")
    return face_samples, ids

def train_model():
    os.makedirs(TRAINER_DIR, exist_ok=True)
    print("\n[INFO] Loading images from dataset folders...\n")
    faces, ids = get_images_and_labels()

    if not faces:
        return

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    print(f"\n[INFO] Training model on {len(faces)} images...")
    recognizer.train(faces, np.array(ids))
    recognizer.save(TRAINER_FILE)

    print(f"\n[SUCCESS] Model trained!")
    print(f"          Students  : {len(set(ids))}")
    print(f"          Images    : {len(faces)}")
    print(f"          Saved to  : {TRAINER_FILE}")
    print("\n[NEXT] Run:  python 3_face_recognition.py\n")

if __name__ == "__main__":
    train_model()
