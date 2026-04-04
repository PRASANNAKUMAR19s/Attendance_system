# Research Pipeline for Attendance System

## Overview
This research module provides comprehensive evaluation, comparison, and analysis of face recognition models for the attendance system.

## Files

### `config_research.py`
Configuration and parameters for research models and experiments.

### `evaluation_metrics.py`
Calculate comprehensive metrics:
- Accuracy, Precision, Recall, F1-score
- Confusion Matrix
- Per-student performance analysis

### `model_comparison.py`
Compare multiple face recognition models:
- LBPH (Local Binary Patterns Histograms)
- EigenFaces
- Simple CNN
- Performance comparison tables

### `robustness_testing.py`
Test models under real-world conditions:
- Low light conditions
- Rotation/angle variations
- Occlusion (masks, glasses)
- Different distances
- Multiple faces in frame

### `generate_graphs.py`
Create publication-quality visualizations:
- Model comparison bar charts
- Accuracy trends
- Speed vs Accuracy trade-off graphs
- Confusion matrices as heatmaps

### `dataset_generator.py`
Generate synthetic test datasets:
- Lighting variations
- Angle/rotation variations
- Blur and occlusion
- Distance variations

## How to Run

```bash
# 1. Generate synthetic datasets
python research/dataset_generator.py

# 2. Evaluate current LBPH model
python research/evaluation_metrics.py

# 3. Compare multiple models
python research/model_comparison.py

# 4. Test robustness
python research/robustness_testing.py

# 5. Generate visualizations
python research/generate_graphs.py
```

## Expected Outputs
- Evaluation metrics in CSV format
- Comparison tables
- Publication-ready graphs in PNG format
- Research report draft

## Output Files
- `research/results/` - All results and graphs
- `research/reports/` - Generated reports