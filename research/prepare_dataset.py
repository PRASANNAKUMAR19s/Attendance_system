"""
Dataset Preparation Script
Split dataset into train/test folders
"""

import os
import shutil
from pathlib import Path
import random

# Configuration
DATASET_DIR = Path(__file__).parent.parent / "dataset"
TRAIN_DIR = DATASET_DIR / "train"
TEST_DIR = DATASET_DIR / "test"
TRAIN_SPLIT = 0.8  # 80% training, 20% testing

def prepare_dataset():
    """Split dataset into train/test folders"""
    
    # Create directories
    TRAIN_DIR.mkdir(parents=True, exist_ok=True)
    TEST_DIR.mkdir(parents=True, exist_ok=True)
    
    print("Starting dataset preparation...")
    print(f"Source: {DATASET_DIR}")
    print(f"Train: {TRAIN_DIR}")
    print(f"Test: {TEST_DIR}")
    print()
    
    total_images = 0
    train_images = 0
    test_images = 0
    
    # Iterate through student folders
    for student_folder in DATASET_DIR.iterdir():
        if not student_folder.is_dir() or student_folder.name in ['train', 'test']:
            continue
        
        student_id = student_folder.name
        print(f"Processing: {student_id}")
        
        # Get all images
        images = [f for f in student_folder.iterdir() if f.is_file()]
        
        if not images:
            print(f"  ⚠️  No images found")
            continue
        
        # Shuffle and split
        random.shuffle(images)
        split_index = int(len(images) * TRAIN_SPLIT)
        train_images_list = images[:split_index]
        test_images_list = images[split_index:]
        
        # Create student directories
        train_student_dir = TRAIN_DIR / student_id
        test_student_dir = TEST_DIR / student_id
        train_student_dir.mkdir(parents=True, exist_ok=True)
        test_student_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy training images
        for img in train_images_list:
            shutil.copy2(img, train_student_dir / img.name)
            train_images += 1
        
        # Copy test images
        for img in test_images_list:
            shutil.copy2(img, test_student_dir / img.name)
            test_images += 1
        
        total_images += len(images)
        print(f"  ✅ {len(train_images_list)} train | {len(test_images_list)} test")
    
    print()
    print("=" * 50)
    print("Dataset Preparation Complete!")
    print("=" * 50)
    print(f"Total Images: {total_images}")
    print(f"Training Images: {train_images} ({train_images/total_images*100:.1f}%)")
    print(f"Test Images: {test_images} ({test_images/total_images*100:.1f}%)")
    print()
    print(f"✅ Train folder: {TRAIN_DIR}")
    print(f"✅ Test folder: {TEST_DIR}")

if __name__ == "__main__":
    prepare_dataset()