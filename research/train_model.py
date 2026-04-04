"""
Train LBPH Face Recognizer Model
"""

import cv2
import os
import numpy as np
import json
from pathlib import Path
from config_research import *

def train_model():
    """Train LBPH model on the training dataset"""
    
    print("Starting Model Training...\n")
    
    # Initialize LBPH
    lbph = cv2.face.LBPHFaceRecognizer_create()
    face_cascade = cv2.CascadeClassifier(str(HAARCASCADE_PATH))
    
    train_path = DATA_DIR / "train"
    if not train_path.exists():
        print(f"❌ Train folder not found: {train_path}")
        return
    
    images = []
    labels = []
    label_map = {}  # Maps numeric ID to student name
    
    print(f"Loading images from: {train_path}\n")
    
    for numeric_id, student_id in enumerate(sorted(os.listdir(train_path))):
        student_path = train_path / student_id
        if not student_path.is_dir():
            continue
        
        label_map[student_id] = numeric_id  # Store as name -> ID
        images_count = 0
        
        for image_file in os.listdir(student_path):
            image_path = student_path / image_file
            img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
            
            if img is not None:
                faces = face_cascade.detectMultiScale(img, scaleFactor=1.3, minNeighbors=5, minSize=(30, 30))
                
                if len(faces) > 0:
                    # Use the first face in the image
                    x, y, w, h = faces[0]
                    face_roi = img[y:y+h, x:x+w]
                    images.append(face_roi)
                    labels.append(numeric_id)
                    images_count += 1
        
        print(f"✅ {student_id} (ID: {numeric_id}): {images_count} face images")
    
    if len(images) == 0:
        print("❌ No face images found!")
        return
    
    print(f"\n📊 Total images for training: {len(images)}")
    print(f"📊 Unique students: {len(set(labels))}")
    
    # Train the model
    print("\n🔄 Training LBPH model...")
    lbph.train(images, np.array(labels))
    
    # Save the model
    TRAINER_DIR.mkdir(parents=True, exist_ok=True)
    lbph.write(str(LBPH_TRAINER_PATH))
    
    print(f"✅ Model trained and saved to: {LBPH_TRAINER_PATH}")
    
    # Save label map (student name -> numeric ID)
    mapping_file = RESULTS_DIR / "student_mapping.json"
    with open(mapping_file, 'w') as f:
        json.dump(label_map, f, indent=2)
    
    print(f"✅ Label mapping saved to: {mapping_file}")
    print("\n=== Label Mapping ===")
    for student_name, numeric_id in label_map.items():
        print(f"  {numeric_id}: {student_name}")

if __name__ == "__main__":
    train_model()