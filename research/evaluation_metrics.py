"""
Evaluation Metrics Module
Calculate comprehensive metrics for model evaluation
"""

import cv2
import numpy as np
import os
from pathlib import Path
from sklearn.metrics import confusion_matrix, accuracy_score, precision_score, recall_score, f1_score
import csv
from config_research import *

class EvaluationMetrics:
    def __init__(self, model_path=None):
        self.model_path = model_path or LBPH_TRAINER_PATH
        self.lbph = cv2.face.LBPHFaceRecognizer_create()
        if os.path.exists(str(self.model_path)):
            self.lbph.read(str(self.model_path))
        self.results = {}
        
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
                
            for image_file in os.listdir(student_path):
                image_path = os.path.join(student_path, image_file)
                img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
                
                if img is not None:
                    faces = cv2.CascadeClassifier(str(HAARCASCADE_PATH)).detectMultiScale(img)
                    
                    if len(faces) > 0:
                        label, confidence = self.lbph.predict(img)
                        true_labels.append(int(student_id))
                        predicted_labels.append(label)
        
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
        metrics = evaluator.evaluate_on_dataset(str(test_path))
        if metrics:
            print("\n=== Evaluation Results ===")
            print(f"Accuracy: {metrics['accuracy']:.4f}")
            print(f"Precision: {metrics['precision']:.4f}")
            print(f"Recall: {metrics['recall']:.4f}")
            print(f"F1-Score: {metrics['f1']:.4f}")
            evaluator.save_results(metrics)

if __name__ == "__main__":
    main()