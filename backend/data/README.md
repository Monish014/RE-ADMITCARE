# Data Directory

This directory contains datasets and trained models for the ReadmitCare platform.

## Directory Structure

```
data/
├── datasets/           # Training and evaluation datasets
│   └── diabetic_data.csv
└── models/            # Trained ML models (created during training)
    ├── xgboost_ensemble/
    └── baseline_logistic.pkl
```

## Datasets

### diabetic_data.csv

**Source**: UCI Machine Learning Repository  
**Dataset ID**: 296  
**Name**: Diabetes 130-US Hospitals for Years 1999-2008

**Description**: 
The dataset represents ten years (1999-2008) of clinical care at 130 US hospitals and integrated delivery networks. It contains 101,766 hospital records of patients diagnosed with diabetes who underwent laboratory tests, received medications, and stayed 1-14 days.

**Key Statistics**:
- Total rows: 101,766
- Total columns: 48
- File size: ~16 MB
- Target variable: `readmitted` (NO, <30, >30)

**Citation**:
Clore, J., Cios, K., DeShazo, J., & Strack, B. (2014). Diabetes 130-US Hospitals for Years 1999-2008 [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5230J

**License**: Creative Commons Attribution 4.0 International (CC BY 4.0)

## Downloading the Dataset

To download the dataset, run:

```bash
python scripts/download_uci_dataset.py
```

The script will:
1. Install the `ucimlrepo` package if not already installed
2. Download the dataset from UCI ML Repository
3. Validate the CSV structure
4. Save to `data/datasets/diabetic_data.csv`

The script includes retry logic with exponential backoff (3 attempts) to handle network failures.

## Models Directory

The `models/` directory will be populated during model training. It stores:
- Trained XGBoost ensemble models (15 models for uncertainty quantification)
- Baseline logistic regression model
- Model metadata and version information
- Feature preprocessing artifacts

See the ML pipeline documentation for details on model training and deployment.
