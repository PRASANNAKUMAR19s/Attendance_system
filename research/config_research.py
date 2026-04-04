"""
Research Configuration
Configuration settings for research models and experiments
"""

import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "dataset"
TRAINER_DIR = PROJECT_ROOT / "trainer"
ATTENDANCE_DIR = PROJECT_ROOT / "attendance"
RESULTS_DIR = PROJECT_ROOT / "research" / "results"
REPORTS_DIR = PROJECT_ROOT / "research" / "reports"

# Create directories if they don't exist
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Model paths
LBPH_TRAINER_PATH = TRAINER_DIR / "trainer.yml"
HAARCASCADE_PATH = PROJECT_ROOT / "haarcascade" / "haarcascade_frontalface_default.xml"

# Face recognition parameters
LBPH_NEIGHBORS = 70
LBPH_RADIUS = 1
LBPH_GRID_X = 8
LBPH_GRID_Y = 8

# Evaluation parameters
MIN_CONFIDENCE = 50  # LBPH confidence threshold
EVALUATION_SPLIT = 0.8  # 80/20 train-test split

# Robustness testing parameters
TEST_CONDITIONS = {
    'normal': {'brightness': 1.0, 'rotation': 0},
    'low_light': {'brightness': 0.5, 'rotation': 0},
    'bright': {'brightness': 1.5, 'rotation': 0},
    'rotated_15': {'brightness': 1.0, 'rotation': 15},
    'rotated_30': {'brightness': 1.0, 'rotation': 30},
    'low_light_rotated': {'brightness': 0.5, 'rotation': 15},
}

# Dataset generator parameters
SYNTHETIC_SAMPLES_PER_CONDITION = 5
IMAGE_SIZE = (100, 100)

# Model comparison parameters
MODELS_TO_COMPARE = ['LBPH', 'EigenFaces', 'SimpleCNN']

# Output formats
OUTPUT_FORMAT = 'png'
DPI = 300  # For publication-quality graphs