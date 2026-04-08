"""
Debug model predictions
"""

import cv2
import os
from pathlib import Path
from config_research import *

def debug_predictions():
    """Test model predictions on actual images"""
    
    lbph = cv2.face.LBPHFaceRecognizer_create()
    if not os.path.exists(str(LBPH_TRAINER_PATH)):
        print(f"❌ Model not found: {LBPH_TRAINER_PATH}")
        return
    
    lbph.read(str(LBPH_TRAINER_PATH))
    print("✅ Model loaded\n")
    
    test_path = DATA_DIR / "test"
    face_cascade = cv2.CascadeClassifier(str(HAARCASCADE_PATH))
    
    print("Testing predictions on test set...\n")
    
    for student_id in os.listdir(test_path):
        student_path = test_path / student_id
        if not student_path.is_dir():
            continue
        
        print(f"\n{student_id}:")
        for image_file in list(os.listdir(student_path))[:2]:  # Test first 2 images
            image_path = student_path / image_file
            img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
            
            if img is not None:
                faces = face_cascade.detectMultiScale(img)
                print(f"  {image_file}: {len(faces)} faces detected")
                
                if len(faces) > 0:
                    label, confidence = lbph.predict(img)
                    print(f"    → Predicted label: {label}, Confidence: {confidence:.2f}")
                else:
                    print(f"    → No faces detected!")

if __name__ == "__main__":
    debug_predictions()