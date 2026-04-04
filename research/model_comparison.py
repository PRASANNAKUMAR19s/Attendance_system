"""
Model Comparison Module
Compare multiple face recognition approaches
"""

import cv2
import numpy as np
import os
import time
import csv
from pathlib import Path
from config_research import *

class ModelComparison:
    def __init__(self):
        self.results = {}
        self.lbph = cv2.face.LBPHFaceRecognizer_create()
        self.eigenfaces = cv2.face.EigenFaceRecognizer_create()
        
        # Load trained models if available
        if os.path.exists(str(LBPH_TRAINER_PATH)):
            self.lbph.read(str(LBPH_TRAINER_PATH))
    
    def test_lbph_model(self, test_images, test_labels):
        """Test LBPH model"""
        print("Testing LBPH Model...")
        correct = 0
        start_time = time.time()
        
        for img, label in zip(test_images, test_labels):
            pred_label, confidence = self.lbph.predict(img)
            if pred_label == label:
                correct += 1
        
        elapsed = time.time() - start_time
        accuracy = correct / len(test_images) if test_images else 0
        
        return {
            'model': 'LBPH',
            'accuracy': accuracy,
            'speed': elapsed / len(test_images) if test_images else 0,
            'total_time': elapsed
        }
    
    def test_eigenfaces_model(self, test_images, test_labels):
        """Test EigenFaces model"""
        print("Testing EigenFaces Model...")
        correct = 0
        start_time = time.time()
        
        for img, label in zip(test_images, test_labels):
            pred_label, confidence = self.eigenfaces.predict(img)
            if pred_label == label:
                correct += 1
        
        elapsed = time.time() - start_time
        accuracy = correct / len(test_images) if test_images else 0
        
        return {
            'model': 'EigenFaces',
            'accuracy': accuracy,
            'speed': elapsed / len(test_images) if test_images else 0,
            'total_time': elapsed
        }
    
    def compare_models(self, test_images, test_labels):
        """Compare all models"""
        results = []
        
        results.append(self.test_lbph_model(test_images, test_labels))
        results.append(self.test_eigenfaces_model(test_images, test_labels))
        
        return results
    
    def save_comparison(self, results, filename='model_comparison.csv'):
        """Save comparison results"""
        output_path = RESULTS_DIR / filename
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Model', 'Accuracy', 'Speed (s/image)', 'Total Time (s)'])
            for result in results:
                writer.writerow([
                    result['model'],
                    f"{result['accuracy']:.4f}",
                    f"{result['speed']:.6f}",
                    f"{result['total_time']:.4f}"
                ])
        
        print(f"\nComparison saved to {output_path}")
        
        # Print comparison table
        print("\n=== Model Comparison ===")
        for result in results:
            print(f"\n{result['model']}:")
            print(f"  Accuracy: {result['accuracy']:.4f}")
            print(f"  Speed: {result['speed']:.6f} s/image")
            print(f"  Total Time: {result['total_time']:.4f} s")

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
                    img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
                    if img is not None:
                        test_images.append(img)
                        test_labels.append(int(student_id))
    
    if test_images:
        comparison = ModelComparison()
        results = comparison.compare_models(test_images, test_labels)
        comparison.save_comparison(results)

if __name__ == "__main__":
    main()