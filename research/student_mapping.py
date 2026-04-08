"""
Create student ID mapping
Maps student folder names to numeric IDs used in training
"""

import json
import os
from pathlib import Path
from config_research import *

def create_student_mapping():
    """Create mapping of student names to numeric IDs"""
    
    mapping = {}
    train_path = DATA_DIR / "train"
    
    # Get sorted list of student folders
    student_folders = sorted([d for d in os.listdir(train_path) if (train_path / d).is_dir()])
    
    print("Creating Student ID Mapping...")
    print("=" * 50)
    
    for numeric_id, student_name in enumerate(student_folders):
        mapping[student_name] = numeric_id
        print(f"{numeric_id}: {student_name}")
    
    # Save mapping to JSON
    mapping_file = RESULTS_DIR / "student_mapping.json"
    with open(mapping_file, 'w') as f:
        json.dump(mapping, f, indent=2)
    
    print("=" * 50)
    print(f"✅ Mapping saved to: {mapping_file}")
    return mapping

if __name__ == "__main__":
    create_student_mapping()