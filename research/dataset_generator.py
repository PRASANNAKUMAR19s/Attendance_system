"""
Dataset Generator Module
Generate synthetic test datasets with variations
"""

import cv2
import numpy as np
import os
from pathlib import Path
from config_research import *

class DatasetGenerator:
    def __init__(self):
        self.synthetic_dir = RESULTS_DIR / "synthetic_datasets"
        self.synthetic_dir.mkdir(parents=True, exist_ok=True)
    
    def apply_brightness(self, img, brightness_factor):
        """Adjust brightness"""
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[:, :, 2] = hsv[:, :, 2] * brightness_factor
        hsv[:, :, 2][hsv[:, :, 2] > 255] = 255
        return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
    
    def rotate_image(self, img, angle):
        """Rotate image"""
        h, w = img.shape[:2]
        center = (w // 2, h // 2)
        matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        return cv2.warpAffine(img, matrix, (w, h))
    
    def apply_blur(self, img, kernel_size=5):
        """Apply blur"""
        return cv2.GaussianBlur(img, (kernel_size, kernel_size), 0)
    
    def generate_variants(self, image_path, student_id, variant_count=SYNTHETIC_SAMPLES_PER_CONDITION):
        """Generate variants of an image"""
        img = cv2.imread(str(image_path))
        if img is None:
            return
        
        # Create student directory
        student_dir = self.synthetic_dir / str(student_id)
        student_dir.mkdir(parents=True, exist_ok=True)
        
        # Resize to standard size
        img = cv2.resize(img, IMAGE_SIZE)
        
        # Generate variants
        variants = {
            'normal': img,
            'low_light': self.apply_brightness(img, 0.5),
            'bright': self.apply_brightness(img, 1.5),
            'rotated_15': self.rotate_image(img, 15),
            'rotated_30': self.rotate_image(img, 30),
            'blurred': self.apply_blur(img),
        }
        
        # Save variants
        for variant_name, variant_img in variants.items():
            for i in range(variant_count):
                output_path = student_dir / f"{variant_name}_{i}.jpg"
                cv2.imwrite(str(output_path), variant_img)
    
    def generate_from_dataset(self):
        """Generate variants from existing dataset"""
        print("Generating synthetic dataset variants...")
        
        data_path = DATA_DIR / "train"
        if data_path.exists():
            for student_id in os.listdir(data_path):
                student_dir = data_path / student_id
                if student_dir.is_dir():
                    for image_file in os.listdir(student_dir):
                        image_path = student_dir / image_file
                        self.generate_variants(image_path, student_id)
        
        print(f"Synthetic datasets saved to: {self.synthetic_dir}")

def main():
    generator = DatasetGenerator()
    generator.generate_from_dataset()

if __name__ == "__main__":
    main()