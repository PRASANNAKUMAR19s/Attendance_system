"""
Check trained model information
"""

import cv2
import os
from pathlib import Path
from config_research import *

def check_model():
    """Check what the model knows"""
    print("Checking LBPH Model...")
    print(f"Model path: {LBPH_TRAINER_PATH}")
    print(f"Model exists: {os.path.exists(str(LBPH_TRAINER_PATH))}")
    
    lbph = cv2.face.LBPHFaceRecognizer_create()
    if os.path.exists(str(LBPH_TRAINER_PATH)):
        lbph.read(str(LBPH_TRAINER_PATH))
        print("✅ Model loaded successfully!")
        
        # Get model info
        print(f"\nModel parameters:")
        print(f"  Radius: {lbph.getRadius()}")
        print(f"  Neighbors: {lbph.getNeighbors()}")
        print(f"  Grid X: {lbph.getGridX()}")
        print(f"  Grid Y: {lbph.getGridY()}")
    else:
        print("❌ Model not found!")
    
    # Check training data structure
    print(f"\n\nChecking dataset structure...")
    train_path = DATA_DIR / "train"
    if train_path.exists():
        print(f"Train folder: {train_path}")
        for student_id in os.listdir(train_path):
            student_dir = train_path / student_id
            if student_dir.is_dir():
                image_count = len([f for f in student_dir.iterdir() if f.is_file()])
                print(f"  {student_id}: {image_count} images")
    else:
        print(f"❌ Train folder not found: {train_path}")

if __name__ == "__main__":
    check_model()