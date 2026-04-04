"""
Graph Generation Module
Create publication-quality visualizations
"""

import matplotlib.pyplot as plt
import numpy as np
import csv
import os
from pathlib import Path
from config_research import *

class GraphGenerator:
    def __init__(self):
        plt.style.use('seaborn-v0_8-darkgrid')
        self.dpi = DPI
    
    def plot_model_comparison(self, comparison_file):
        """Plot model comparison bar chart"""
        models = []
        accuracies = []
        speeds = []
        
        file_path = RESULTS_DIR / comparison_file
        if not file_path.exists():
            print(f"File not found: {file_path}")
            return
        
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                models.append(row['Model'])
                accuracies.append(float(row['Accuracy']))
                speeds.append(float(row['Speed (s/image)']))
        
        # Create figure with two subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        
        # Accuracy comparison
        ax1.bar(models, accuracies, color='skyblue')
        ax1.set_ylabel('Accuracy', fontsize=12)
        ax1.set_title('Model Accuracy Comparison', fontsize=14, fontweight='bold')
        ax1.set_ylim([0, 1])
        ax1.grid(axis='y', alpha=0.3)
        
        # Speed comparison
        ax2.bar(models, speeds, color='lightcoral')
        ax2.set_ylabel('Time per Image (seconds)', fontsize=12)
        ax2.set_title('Model Speed Comparison', fontsize=14, fontweight='bold')
        ax2.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        output_path = RESULTS_DIR / 'model_comparison_chart.png'
        plt.savefig(output_path, dpi=self.dpi, bbox_inches='tight')
        print(f"Chart saved: {output_path}")
        plt.close()
    
    def plot_robustness_results(self, robustness_file):
        """Plot robustness test results"""
        conditions = []
        accuracies = []
        
        file_path = RESULTS_DIR / robustness_file
        if not file_path.exists():
            print(f"File not found: {file_path}")
            return
        
        condition_dict = {}
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                condition = row['Condition']
                is_correct = row['Correct'] == 'Yes'
                
                if condition not in condition_dict:
                    condition_dict[condition] = {'correct': 0, 'total': 0}
                
                condition_dict[condition]['total'] += 1
                if is_correct:
                    condition_dict[condition]['correct'] += 1
        
        for condition, stats in sorted(condition_dict.items()):
            conditions.append(condition)
            accuracies.append(stats['correct'] / stats['total'] if stats['total'] > 0 else 0)
        
        # Create bar chart
        plt.figure(figsize=(10, 6))
        plt.bar(conditions, accuracies, color='lightgreen')
        plt.ylabel('Accuracy', fontsize=12)
        plt.title('Robustness Test Results', fontsize=14, fontweight='bold')
        plt.ylim([0, 1])
        plt.xticks(rotation=45, ha='right')
        plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        
        output_path = RESULTS_DIR / 'robustness_chart.png'
        plt.savefig(output_path, dpi=self.dpi, bbox_inches='tight')
        print(f"Chart saved: {output_path}")
        plt.close()

def main():
    generator = GraphGenerator()
    
    # Generate model comparison chart
    comparison_file = 'model_comparison.csv'
    if (RESULTS_DIR / comparison_file).exists():
        generator.plot_model_comparison(comparison_file)
    
    # Generate robustness chart
    robustness_file = 'robustness_results.csv'
    if (RESULTS_DIR / robustness_file).exists():
        generator.plot_robustness_results(robustness_file)

if __name__ == "__main__":
    main()