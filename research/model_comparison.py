"""
Model Comparison Module
Compare multiple face recognition approaches
"""

import cv2
import numpy as np
import os
import json
import time
import csv
from pathlib import Path
from config_research import *

class ModelComparison:
    def __init__(self):
        self.results = {}
        self.lbph = cv2.face.LBPHFaceRecognizer_create()
        self.eigenfaces = cv2.face.EigenFaceRecognizer_create()
        self.student_id_map = {}
        self.load_student_mapping()
        
        # Load trained models if available
        if os.path.exists(str(LBPH_TRAINER_PATH)):
            self.lbph.read(str(LBPH_TRAINER_PATH))
        
        # Train EigenFaces if we have training data
        self.train_eigenfaces()
    
    def load_student_mapping(self):
        """Load student ID mapping from file"""
        mapping_file = RESULTS_DIR / "student_mapping.json"
        if mapping_file.exists():
            with open(mapping_file, 'r') as f:
                self.student_id_map = json.load(f)
    
    def train_eigenfaces(self):
        """Train EigenFaces model on training data"""
        train_path = DATA_DIR / "train"
        if not train_path.exists():
            return
        
        images = []
        labels = []
        face_cascade = cv2.CascadeClassifier(str(HAARCASCADE_PATH))
        
        # First pass: collect all faces and find common size
        all_faces = []
        for numeric_id, student_id in enumerate(sorted(os.listdir(train_path))):
            student_path = train_path / student_id
            if not student_path.is_dir():
                continue
            
            for image_file in os.listdir(student_path):
                image_path = student_path / image_file
                img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
                
                if img is not None:
                    faces = face_cascade.detectMultiScale(img, scaleFactor=1.3, minNeighbors=5, minSize=(30, 30))
                    if len(faces) > 0:
                        x, y, w, h = faces[0]
                        face_roi = img[y:y+h, x:x+w]
                        all_faces.append((face_roi, numeric_id))
        
        if len(all_faces) < 2:
            print("⚠️  Not enough training samples for EigenFaces")
            return
        
        # Find most common size
        sizes = {}
        for face, _ in all_faces:
            size = face.shape
            sizes[size] = sizes.get(size, 0) + 1
        
        target_size = max(sizes, key=sizes.get)
        print(f"Using target face size: {target_size}")
        
        # Resize all faces to target size and prepare training data
        for face, numeric_id in all_faces:
            if face.shape == target_size:
                images.append(face)
                labels.append(numeric_id)
        
        if len(images) >= 2:
            try:
                self.eigenfaces.train(images, np.array(labels))
                print(f"✅ EigenFaces trained with {len(images)} images")
            except Exception as e:
                print(f"⚠️  EigenFaces training failed: {e}")
    
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
            try:
                pred_label, confidence = self.eigenfaces.predict(img)
                if pred_label == label:
                    correct += 1
            except:
                pass
        
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
    
    comparison = ModelComparison()
    
    test_path = DATA_DIR / "test"
    if test_path.exists():
        face_cascade = cv2.CascadeClassifier(str(HAARCASCADE_PATH))
        
        for student_id in os.listdir(test_path):
            student_dir = test_path / student_id
            if student_dir.is_dir():
                numeric_id = comparison.student_id_map.get(student_id, -1)
                if numeric_id == -1:
                    print(f"⚠️  Unknown student: {student_id}")
                    continue
                
                for image_file in os.listdir(student_dir):
                    image_path = student_dir / image_file
                    img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
                    if img is not None:
                        faces = face_cascade.detectMultiScale(img)
                        if len(faces) > 0:
                            test_images.append(img)
                            test_labels.append(numeric_id)
    
    if test_images:
        results = comparison.compare_models(test_images, test_labels)
        comparison.save_comparison(results)
    else:
        print("❌ No test images found!")

if __name__ == "__main__":
    main()