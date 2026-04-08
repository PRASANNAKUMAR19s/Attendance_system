"""
Step 0: Prepare Dataset
Splits raw student image folders from dataset/ into train (80%) and test (20%) subsets.

Usage:
    python research/prepare_dataset.py
Dataset Preparation Script
Split dataset into train/test folders
"""

import os
import shutil
import random

DATASET_DIR = os.path.join(os.path.dirname(__file__), '..', 'dataset')
TRAIN_DIR = os.path.join(DATASET_DIR, 'train')
TEST_DIR = os.path.join(DATASET_DIR, 'test')

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.pgm'}
TRAIN_RATIO = 0.8
RANDOM_SEED = 42


def is_image(filename):
    return os.path.splitext(filename.lower())[1] in IMAGE_EXTENSIONS


def prepare_split():
    dataset_dir = os.path.normpath(DATASET_DIR)
    train_dir = os.path.normpath(TRAIN_DIR)
    test_dir = os.path.normpath(TEST_DIR)

    # Collect student folders (skip train/test subdirs themselves)
    skip = {os.path.normpath(d) for d in (train_dir, test_dir)}
    student_folders = [
        entry.name
        for entry in os.scandir(dataset_dir)
        if entry.is_dir() and os.path.normpath(entry.path) not in skip
    ]

    if not student_folders:
        print("No student folders found in dataset/. Nothing to do.")
        return

    student_folders.sort()
    random.seed(RANDOM_SEED)

    total_train = 0
    total_test = 0

    print(f"{'Student':<30} {'Total':>7} {'Train':>7} {'Test':>7}")
    print("-" * 55)

    for student in student_folders:
        src_folder = os.path.join(dataset_dir, student)
        images = sorted(f for f in os.listdir(src_folder) if is_image(f))

        if not images:
            print(f"{student:<30} {'0':>7} {'0':>7} {'0':>7}  (no images, skipped)")
            continue

        random.shuffle(images)
        if len(images) >= 2:
            # Ensure at least one image in both train and test sets.
            split_idx = max(1, min(len(images) - 1, int(len(images) * TRAIN_RATIO)))
        else:
            split_idx = len(images)  # single image: all goes to train, test stays empty
        train_images = images[:split_idx]
        test_images = images[split_idx:]

        for subset, imgs in (('train', train_images), ('test', test_images)):
            dest = os.path.join(dataset_dir, subset, student)
            os.makedirs(dest, exist_ok=True)
            for img in imgs:
                # Copy (not move) so that the original dataset/ images remain
                # available for the main attendance system scripts.
                shutil.copy2(os.path.join(src_folder, img), os.path.join(dest, img))

        total_train += len(train_images)
        total_test += len(test_images)
        print(f"{student:<30} {len(images):>7} {len(train_images):>7} {len(test_images):>7}")

    print("-" * 55)
    print(f"{'TOTAL':<30} {total_train + total_test:>7} {total_train:>7} {total_test:>7}")
    print(f"\nTrain folder : {train_dir}")
    print(f"Test folder  : {test_dir}")


if __name__ == '__main__':
    prepare_split()
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
