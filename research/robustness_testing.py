"""
Robustness Testing Module
Test models under various real-world conditions
"""

import cv2
import numpy as np
import os
import csv
from pathlib import Path
from config_research import *

class RobustnessTesting:
    def __init__(self):
        self.lbph = cv2.face.LBPHFaceRecognizer_create()
        if os.path.exists(str(LBPH_TRAINER_PATH)):
            self.lbph.read(str(LBPH_TRAINER_PATH))
        self.results = []
    
    def apply_brightness(self, img, brightness_factor):
        """Adjust image brightness"""
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[:, :, 2] = hsv[:, :, 2] * brightness_factor
        hsv[:, :, 2][hsv[:, :, 2] > 255] = 255
        return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
    
    def rotate_image(self, img, angle):
        """Rotate image by specified angle"""
        h, w = img.shape[:2]
        center = (w // 2, h // 2)
        matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        return cv2.warpAffine(img, matrix, (w, h))
    
    def apply_occlusion(self, img, occlusion_type='mask'):
        """Apply occlusion to image"""
        h, w = img.shape[:2]
        img_copy = img.copy()
        
        if occlusion_type == 'mask':
            # Mask lower half of face
            img_copy[h//2:, :] = 0
        elif occlusion_type == 'glasses':
            # Simulate glasses
            img_copy[h//3:h//2, w//4:3*w//4] = 0
        
        return img_copy
    
    def test_condition(self, img, label, condition_name):
        """Test image under specific condition"""
        try:
            pred_label, confidence = self.lbph.predict(img)
            is_correct = (pred_label == label)
            
            return {
                'condition': condition_name,
                'true_label': label,
                'predicted_label': pred_label,
                'confidence': confidence,
                'correct': is_correct
            }
        except:
            return None
    
    def run_robustness_tests(self, test_images, test_labels):
        """Run all robustness tests"""
        print("Running Robustness Tests...")
        
        for img, label in zip(test_images, test_labels):
            # Test normal image
            result = self.test_condition(img, label, 'normal')
            if result:
                self.results.append(result)
            
            # Test low light
            low_light_img = cv2.convertScaleAbs(img, alpha=0.5, beta=0)
            result = self.test_condition(low_light_img, label, 'low_light')
            if result:
                self.results.append(result)
            
            # Test rotated
            rotated_img = self.rotate_image(img, 15)
            result = self.test_condition(rotated_img, label, 'rotated_15')
            if result:
                self.results.append(result)
            
            # Test with occlusion
            occluded_img = self.apply_occlusion(img, 'mask')
            result = self.test_condition(occluded_img, label, 'occluded')
            if result:
                self.results.append(result)
    
    def save_results(self, filename='robustness_results.csv'):
        """Save robustness test results"""
        output_path = RESULTS_DIR / filename
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Condition', 'True Label', 'Predicted Label', 'Confidence', 'Correct'])
            for result in self.results:
                writer.writerow([
                    result['condition'],
                    result['true_label'],
                    result['predicted_label'],
                    f"{result['confidence']:.2f}",
                    'Yes' if result['correct'] else 'No'
                ])
        
        print(f"Results saved to {output_path}")
        
        # Calculate statistics by condition
        print("\n=== Robustness Test Results ===")
        conditions = set(r['condition'] for r in self.results)
        for condition in conditions:
            condition_results = [r for r in self.results if r['condition'] == condition]
            correct_count = sum(1 for r in condition_results if r['correct'])
            accuracy = correct_count / len(condition_results) if condition_results else 0
            print(f"{condition}: {accuracy:.2%} accuracy ({correct_count}/{len(condition_results)})")

def main():
    # Load test data
    test_images = []
    test_labels = []
    
    test_path = DATA_DIR / "test"
    if test_path.exists():
        for student_id in os.listdir(test_path):
            student_dir = test_path / student_id
            if student_dir.is_dir():
                for image_file in os.listdir(student_dir):
                    image_path = student_dir / image_file
                    img = cv2.imread(str(image_path))
                    if img is not None:
                        test_images.append(img)
                        test_labels.append(int(student_id))
    
    if test_images:
        tester = RobustnessTesting()
        tester.run_robustness_tests(test_images, test_labels)
        tester.save_results()

if __name__ == "__main__":
    main()