"""
Evaluation Metrics Module
Calculate comprehensive metrics for model evaluation
"""

import cv2
import numpy as np
import os
import json
from pathlib import Path
from sklearn.metrics import confusion_matrix, accuracy_score, precision_score, recall_score, f1_score
import csv
from config_research import *

class EvaluationMetrics:
    def __init__(self, model_path=None):
        self.model_path = model_path or LBPH_TRAINER_PATH
        self.lbph = cv2.face.LBPHFaceRecognizer_create()
        self.student_id_map = {}
        self.reverse_map = {}
        self.load_student_mapping()
        
        if os.path.exists(str(self.model_path)):
            self.lbph.read(str(self.model_path))
        self.results = {}
    
    def load_student_mapping(self):
        """Load student ID mapping from file"""
        mapping_file = RESULTS_DIR / "student_mapping.json"
        if mapping_file.exists():
            with open(mapping_file, 'r') as f:
                self.student_id_map = json.load(f)
                self.reverse_map = {v: k for k, v in self.student_id_map.items()}
            print(f"✅ Loaded student mapping: {mapping_file}")
        else:
            print(f"⚠️  Student mapping not found: {mapping_file}")
    
    def get_numeric_id(self, student_name):
        """Get numeric ID for student name"""
        return self.student_id_map.get(student_name, -1)
        
    def calculate_metrics(self, true_labels, predicted_labels):
        """Calculate comprehensive evaluation metrics"""
        metrics = {
            'accuracy': accuracy_score(true_labels, predicted_labels),
            'precision': precision_score(true_labels, predicted_labels, average='weighted', zero_division=0),
            'recall': recall_score(true_labels, predicted_labels, average='weighted', zero_division=0),
            'f1': f1_score(true_labels, predicted_labels, average='weighted', zero_division=0),
            'confusion_matrix': confusion_matrix(true_labels, predicted_labels)
        }
        return metrics
    
    def evaluate_on_dataset(self, test_dir):
        """Evaluate model on a test dataset"""
        true_labels = []
        predicted_labels = []
        
        for student_id in os.listdir(test_dir):
            student_path = os.path.join(test_dir, student_id)
            if not os.path.isdir(student_path):
                continue
            
            numeric_id = self.get_numeric_id(student_id)
            if numeric_id == -1:
                print(f"⚠️  Unknown student: {student_id}")
                continue
            
            images_processed = 0
            for image_file in os.listdir(student_path):
                image_path = os.path.join(student_path, image_file)
                img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
                
                if img is not None:
                    faces = cv2.CascadeClassifier(str(HAARCASCADE_PATH)).detectMultiScale(img)
                    
                    if len(faces) > 0:
                        label, confidence = self.lbph.predict(img)
                        true_labels.append(numeric_id)
                        predicted_labels.append(label)
                        images_processed += 1
            
            if images_processed > 0:
                print(f"✅ {student_id}: {images_processed} images processed")
        
        if true_labels:
            metrics = self.calculate_metrics(true_labels, predicted_labels)
            return metrics
        return None
    
    def save_results(self, metrics, filename='evaluation_results.csv'):
        """Save metrics to CSV"""
        output_path = RESULTS_DIR / filename
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Metric', 'Value'])
            for key, value in metrics.items():
                if key != 'confusion_matrix':
                    writer.writerow([key, f"{value:.4f}"])
        
        print(f"Results saved to {output_path}")

def main():
    evaluator = EvaluationMetrics()
    
    # Evaluate on test set
    test_path = DATA_DIR / "test"
    if test_path.exists():
        print(f"\n📊 Evaluating on: {test_path}\n")
        metrics = evaluator.evaluate_on_dataset(str(test_path))
        if metrics:
            print("\n=== Evaluation Results ===")
            print(f"Accuracy: {metrics['accuracy']:.4f}")
            print(f"Precision: {metrics['precision']:.4f}")
            print(f"Recall: {metrics['recall']:.4f}")
            print(f"F1-Score: {metrics['f1']:.4f}")
            evaluator.save_results(metrics)
        else:
            print("❌ No evaluation results found.")
    else:
        print(f"❌ Test dataset not found at {test_path}")

if __name__ == "__main__":
    main()