"""
STEP 1 — Dataset Collector
===========================
This script opens your webcam and captures 50 face images
for each student. Images are saved in the /dataset/ folder.

HOW TO RUN:
    python 1_dataset_collector.py

INSTRUCTIONS:
    - Enter the student's Roll Number when prompted
    - Enter the student's Name when prompted
    - Look at the camera — it will auto-capture 50 photos
    - Press 'q' to quit early
"""

import cv2
import os
import csv

# ── Paths ──────────────────────────────────────────────────────────────────────
CASCADE_PATH  = "haarcascade/haarcascade_frontalface_default.xml"
DATASET_DIR   = "dataset"
STUDENTS_FILE = "students.csv"

# ── Download Haar Cascade if missing ──────────────────────────────────────────
def ensure_cascade():
    if not os.path.exists(CASCADE_PATH):
        print("[INFO] Downloading Haar Cascade XML...")
        import urllib.request
        url = (
            "https://raw.githubusercontent.com/opencv/opencv/master/"
            "data/haarcascades/haarcascade_frontalface_default.xml"
        )
        urllib.request.urlretrieve(url, CASCADE_PATH)
        print("[INFO] Downloaded successfully.")

# ── Save student info to CSV ───────────────────────────────────────────────────
def save_student_info(reg_no, name):
    file_exists = os.path.isfile(STUDENTS_FILE)
    with open(STUDENTS_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["RollNo", "Name"])
        writer.writerow([reg_no, name])

# ── Main Dataset Collection ───────────────────────────────────────────────────
def collect_dataset():
    ensure_cascade()

    reg_no = input("\nEnter Student Registration Number : ").strip()
    name   = input("Enter Student Name                : ").strip()

    if not reg_no or not name:
        print("[ERROR] Registration number and name cannot be empty.")
        return

    # Save student info
    save_student_info(reg_no, name)

    face_cascade = cv2.CascadeClassifier(CASCADE_PATH)
    cam          = cv2.VideoCapture(0)

    if not cam.isOpened():
        print("[ERROR] Cannot open webcam. Check camera connection.")
        return

    print(f"\n[INFO] Collecting images for {name} (Registration: {reg_no})")
    print("[INFO] Look at the camera. Capturing 50 images...")
    print("[INFO] Press 'q' to quit early.\n")

    count = 0
    total = 50

    while True:
        ret, frame = cam.read()
        if not ret:
            print("[ERROR] Failed to read from camera.")
            break

        gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(
            gray, scaleFactor=1.3, minNeighbors=5, minSize=(60, 60)
        )

        for (x, y, w, h) in faces:
            count += 1
            face_img = gray[y:y+h, x:x+w]
            filename = f"{DATASET_DIR}/User.{reg_no}.{count}.jpg"
            cv2.imwrite(filename, face_img)

            # Draw box and counter
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(
                frame,
                f"Capturing: {count}/{total}",
                (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2,
            )

        cv2.putText(
            frame,
            f"Student: {name}  |  Registration: {reg_no}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 0),
            2,
        )
        cv2.imshow("Dataset Collector — Press Q to quit", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            print("[INFO] Quit by user.")
            break

        if count >= total:
            print(f"[SUCCESS] {total} images captured for {name}.")
            break

    cam.release()
    cv2.destroyAllWindows()

    if count < total:
        print(f"[WARNING] Only {count} images captured. Re-run for better accuracy.")
    else:
        print(f"\n[DONE] Dataset saved in /{DATASET_DIR}/ folder.")
        print("[NEXT] Run:  python 2_train_model.py\n")


if __name__ == "__main__":
    collect_dataset()
