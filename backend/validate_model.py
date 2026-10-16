"""
Model Validation Script

Validates a trained XGBoost model on the test set and generates a comprehensive
validation report with performance metrics. Checks that the model meets minimum
performance thresholds (e.g., AUROC >= 0.80).

Requirements:
- Section 9: Machine Learning Risk Prediction Model
- 5.3: Validate model performance on test set

Features:
- Loads trained model and preprocessor from pickle
- Splits data into train/val/test (60/20/20)
- Evaluates model on test set
- Computes metrics: accuracy, precision, recall, F1, AUROC, confusion matrix
- Validates against thresholds: AUROC >= 0.80, Accuracy >= 0.75
- Generates calibration curves
- Tests prediction latency
- Outputs JSON validation report
- Provides pass/fail validation status
"""

import logging
import sys
import json
import time
import pickle
from pathlib import Path
from typing import Tuple, Dict, Any

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report,
    roc_curve, auc, brier_score_loss
)
import xgboost as xgb

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
BACKEND_DIR = Path(__file__).parent
DATA_CSV = BACKEND_DIR / "data" / "datasets" / "diabetic_data.csv"
MODEL_OUTPUT = BACKEND_DIR / "app" / "models" / "trained_model.pkl"
VALIDATION_REPORT = BACKEND_DIR / "model_validation.json"

# Model parameters
RANDOM_STATE = 42
TEST_SIZE = 0.2  # 20% for test
VAL_SIZE = 0.25  # 25% of remaining 80% = 20% overall

# Features to use (must match training script)
FEATURE_COLUMNS = [
    'race', 'gender', 'age', 'time_in_hospital', 'num_medications',
    'number_diagnoses', 'number_outpatient', 'number_inpatient',
    'number_emergency', 'diabetic_med_changed', 'A1Cresult', 'max_glu_serum',
    'metformin', 'repaglinide', 'nateglinide', 'chlorpropamide',
    'glimepiride', 'acetohexamide', 'glipizide', 'glyburide', 'tolbutamide',
    'pioglitazone', 'rosiglitazone', 'acarbose', 'miglitol', 'troglitazone',
    'tolazamide', 'examide', 'citoglipton', 'insulin', 'glyburide-metformin',
    'glipizide-metformin', 'metformin-rosiglitazone', 'metformin-pioglitazone',
    'change', 'diabetesMed'
]

# Performance thresholds (from Requirement 9.4, 9.5)
THRESHOLDS = {
    'accuracy_min': 0.75,     # Requirement 9.4
    'auc_roc_min': 0.80,      # Requirement 9.5
}

# Prediction latency threshold (from Requirement 9.12)
LATENCY_THRESHOLD_MS = 500


def load_and_prepare_data() -> Tuple[pd.DataFrame, pd.Series]:
    """
    Load and prepare dataset from CSV (same as training script).
    
    Returns:
        Tuple of (features, target)
    """
    logger.info(f"Loading dataset from {DATA_CSV}")
    
    if not DATA_CSV.exists():
        raise FileNotFoundError(
            f"Dataset not found at {DATA_CSV}\n"
            f"Run: python backend/scripts/download_uci_dataset.py"
        )
    
    # Load CSV
    df = pd.read_csv(DATA_CSV)
    logger.info(f"  - Loaded {len(df):,} rows, {len(df.columns)} columns")
    
    # Check for target column
    if 'readmitted' not in df.columns:
        raise ValueError("'readmitted' column not found in dataset")
    
    # Separate features and target
    target = df['readmitted']
    
    # Remove target and ID columns
    features = df.drop(columns=['readmitted'], errors='ignore')
    features = features.drop(columns=['encounter_id', 'patient_nbr'], errors='ignore')
    
    # Select feature columns that exist
    available_features = [col for col in FEATURE_COLUMNS if col in features.columns]
    logger.info(f"  - Using {len(available_features)}/{len(FEATURE_COLUMNS)} available features")
    
    features = features[available_features]
    
    # Handle missing values (same as training)
    logger.info("Handling missing values...")
    initial_missing = features.isnull().sum().sum()
    
    # Fill numeric columns with median
    numeric_cols = features.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if features[col].isnull().any():
            features[col].fillna(features[col].median(), inplace=True)
    
    # Fill categorical columns with mode
    categorical_cols = features.select_dtypes(include=['object']).columns
    for col in categorical_cols:
        if features[col].isnull().any():
            features[col].fillna(features[col].mode()[0], inplace=True)
    
    final_missing = features.isnull().sum().sum()
    logger.info(f"  - Filled {initial_missing} missing values -> {final_missing} remaining")
    
    # Convert age strings to numeric if needed
    if 'age' in features.columns:
        age_col = features['age']
        if age_col.dtype == 'object':
            features['age'] = age_col.str.extract(r'(\d+)').astype(float)
            logger.info("  - Converted age groups to numeric")
    
    # Convert to binary classification
    logger.info("Converting to binary classification (readmitted vs not)...")
    target = (target != 'NO').astype(int)
    logger.info(f"  - Class 0 (Not readmitted): {(target == 0).sum():,}")
    logger.info(f"  - Class 1 (Readmitted): {(target == 1).sum():,}")
    
    return features, target


def split_data(
    X: pd.DataFrame, y: pd.Series
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, np.ndarray, np.ndarray, np.ndarray]:
    """
    Split data into train/val/test (60/20/20).
    
    Args:
        X: Features
        y: Target
        
    Returns:
        Tuple of (X_train, X_val, X_test, y_train, y_val, y_test)
    """
    logger.info("Splitting data into train/val/test (60/20/20)...")
    
    # First split: 80% train+val, 20% test
    X_temp, X_test, y_temp, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )
    
    # Second split: 75% train (of 80%), 25% val (of 80%)
    X_train, X_val, y_train, y_val = train_test_split(
        X_temp, y_temp, test_size=VAL_SIZE, random_state=RANDOM_STATE, stratify=y_temp
    )
    
    logger.info(f"  - Train: {len(X_train):,} samples ({len(X_train)/len(X)*100:.1f}%)")
    logger.info(f"  - Val:   {len(X_val):,} samples ({len(X_val)/len(X)*100:.1f}%)")
    logger.info(f"  - Test:  {len(X_test):,} samples ({len(X_test)/len(X)*100:.1f}%)")
    
    return X_train, X_val, X_test, y_train, y_val, y_test


def load_model_and_preprocessor() -> Tuple[xgb.XGBClassifier, Any]:
    """
    Load trained model and preprocessor from pickle.
    
    Returns:
        Tuple of (model, preprocessor)
    """
    logger.info(f"Loading model from {MODEL_OUTPUT}")
    
    if not MODEL_OUTPUT.exists():
        raise FileNotFoundError(
            f"Trained model not found at {MODEL_OUTPUT}\n"
            f"Run: python backend/train_model.py"
        )
    
    with open(MODEL_OUTPUT, 'rb') as f:
        model_package = pickle.load(f)
    
    model = model_package['model']
    preprocessor = model_package['preprocessor']
    
    logger.info(f"  - Model loaded successfully")
    logger.info(f"  - Model version: {model_package.get('model_version', 'unknown')}")
    
    return model, preprocessor


def evaluate_model_on_test_set(
    model: xgb.XGBClassifier,
    X_test: np.ndarray,
    y_test: np.ndarray
) -> Dict[str, Any]:
    """
    Evaluate model on test set and compute all metrics.
    
    Args:
        model: Trained XGBoost model
        X_test: Test features
        y_test: Test target
        
    Returns:
        Dictionary of metrics
    """
    logger.info("Evaluating model on test set...")
    
    # Make predictions
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    
    # Compute basic metrics
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    
    # Compute AUC-ROC
    try:
        auc_roc = roc_auc_score(y_test, y_pred_proba)
    except Exception as e:
        logger.warning(f"Could not compute AUC-ROC: {e}")
        auc_roc = 0.0
    
    # Compute confusion matrix
    tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()
    
    # Compute ROC curve
    try:
        fpr, tpr, thresholds = roc_curve(y_test, y_pred_proba)
    except:
        fpr, tpr, thresholds = [], [], []
    
    # Compute Brier score (calibration metric)
    try:
        brier_score = brier_score_loss(y_test, y_pred_proba)
    except:
        brier_score = None
    
    # Specificity and sensitivity
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
    sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0
    
    metrics = {
        'accuracy': float(accuracy),
        'precision': float(precision),
        'recall': float(recall),
        'f1_score': float(f1),
        'auc_roc': float(auc_roc),
        'sensitivity': float(sensitivity),
        'specificity': float(specificity),
        'brier_score': float(brier_score) if brier_score is not None else None,
        'confusion_matrix': {
            'true_negatives': int(tn),
            'false_positives': int(fp),
            'false_negatives': int(fn),
            'true_positives': int(tp),
        },
        'roc_curve': {
            'fpr': [float(x) for x in fpr],
            'tpr': [float(x) for x in tpr],
        },
        'test_set_size': len(y_test),
        'positive_samples': int(np.sum(y_test)),
        'negative_samples': int(np.sum(y_test == 0)),
    }
    
    logger.info(f"\n  TEST SET METRICS:")
    logger.info(f"    - Accuracy:    {accuracy:.4f}")
    logger.info(f"    - Precision:   {precision:.4f}")
    logger.info(f"    - Recall:      {recall:.4f}")
    logger.info(f"    - F1-Score:    {f1:.4f}")
    logger.info(f"    - AUC-ROC:     {auc_roc:.4f}")
    logger.info(f"    - Sensitivity: {sensitivity:.4f}")
    logger.info(f"    - Specificity: {specificity:.4f}")
    if brier_score is not None:
        logger.info(f"    - Brier Score: {brier_score:.4f}")
    logger.info(f"\n  CONFUSION MATRIX:")
    logger.info(f"    - True Negatives:  {tn:,}")
    logger.info(f"    - False Positives: {fp:,}")
    logger.info(f"    - False Negatives: {fn:,}")
    logger.info(f"    - True Positives:  {tp:,}")
    
    return metrics


def test_prediction_latency(
    model: xgb.XGBClassifier,
    X_test: np.ndarray,
    num_samples: int = 100
) -> Dict[str, Any]:
    """
    Test model prediction latency.
    
    Args:
        model: Trained XGBoost model
        X_test: Test features
        num_samples: Number of samples to test
        
    Returns:
        Dictionary with latency metrics
    """
    logger.info(f"Testing prediction latency with {num_samples} samples...")
    
    # Sample test data
    if len(X_test) > num_samples:
        indices = np.random.choice(len(X_test), num_samples, replace=False)
        X_sample = X_test[indices]
    else:
        X_sample = X_test
    
    # Measure prediction time
    start_time = time.perf_counter()
    predictions = model.predict_proba(X_sample)
    end_time = time.perf_counter()
    
    total_time_ms = (end_time - start_time) * 1000
    avg_time_ms = total_time_ms / len(X_sample)
    max_time_ms = None  # Would need to time individual predictions for this
    
    latency_metrics = {
        'total_time_ms': float(total_time_ms),
        'average_time_per_prediction_ms': float(avg_time_ms),
        'num_samples_tested': len(X_sample),
        'meets_requirement': avg_time_ms < LATENCY_THRESHOLD_MS,
    }
    
    logger.info(f"    - Total time: {total_time_ms:.2f}ms for {len(X_sample)} samples")
    logger.info(f"    - Avg per prediction: {avg_time_ms:.4f}ms")
    logger.info(f"    - Threshold: {LATENCY_THRESHOLD_MS}ms")
    
    if latency_metrics['meets_requirement']:
        logger.info(f"    ✓ Latency requirement met")
    else:
        logger.warning(f"    ✗ Latency above requirement")
    
    return latency_metrics


def validate_against_thresholds(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate that model meets minimum performance thresholds.
    
    Args:
        metrics: Dictionary of computed metrics
        
    Returns:
        Dictionary with validation results
    """
    logger.info("Validating against performance thresholds...")
    
    validation_results = {}
    all_passed = True
    
    # Check accuracy threshold (Requirement 9.4)
    accuracy = metrics['accuracy']
    accuracy_threshold = THRESHOLDS['accuracy_min']
    accuracy_passed = accuracy >= accuracy_threshold
    validation_results['accuracy'] = {
        'value': float(accuracy),
        'threshold': float(accuracy_threshold),
        'passed': accuracy_passed,
        'requirement': 'Requirement 9.4: Minimum 75% accuracy on test set',
    }
    if accuracy_passed:
        logger.info(f"  ✓ Accuracy {accuracy:.4f} >= {accuracy_threshold}")
    else:
        logger.warning(f"  ✗ Accuracy {accuracy:.4f} < {accuracy_threshold}")
        all_passed = False
    
    # Check AUC-ROC threshold (Requirement 9.5)
    auc_roc = metrics['auc_roc']
    auc_threshold = THRESHOLDS['auc_roc_min']
    auc_passed = auc_roc >= auc_threshold
    validation_results['auc_roc'] = {
        'value': float(auc_roc),
        'threshold': float(auc_threshold),
        'passed': auc_passed,
        'requirement': 'Requirement 9.5: Minimum AUC-ROC of 0.80',
    }
    if auc_passed:
        logger.info(f"  ✓ AUC-ROC {auc_roc:.4f} >= {auc_threshold}")
    else:
        logger.warning(f"  ✗ AUC-ROC {auc_roc:.4f} < {auc_threshold}")
        all_passed = False
    
    validation_results['overall_status'] = 'PASS' if all_passed else 'FAIL'
    
    return validation_results


def generate_validation_report(
    metrics: Dict[str, Any],
    latency_metrics: Dict[str, Any],
    validation_results: Dict[str, Any],
    model_version: str = '1.0.0'
) -> Dict[str, Any]:
    """
    Generate comprehensive validation report.
    
    Args:
        metrics: Performance metrics from test set evaluation
        latency_metrics: Latency test results
        validation_results: Threshold validation results
        model_version: Version of the model
        
    Returns:
        Complete validation report dictionary
    """
    from datetime import datetime
    
    report = {
        'validation_timestamp': datetime.utcnow().isoformat(),
        'model_version': model_version,
        'test_set_metrics': metrics,
        'latency_metrics': latency_metrics,
        'threshold_validation': validation_results,
        'overall_validation_status': validation_results['overall_status'],
        'requirements_met': {
            'requirement_9_4_accuracy': validation_results['accuracy']['passed'],
            'requirement_9_5_auc_roc': validation_results['auc_roc']['passed'],
            'requirement_9_12_latency': latency_metrics['meets_requirement'],
        },
        'summary': {
            'total_checks': 3,
            'checks_passed': sum([
                validation_results['accuracy']['passed'],
                validation_results['auc_roc']['passed'],
                latency_metrics['meets_requirement'],
            ]),
        }
    }
    
    report['summary']['all_checks_passed'] = report['summary']['checks_passed'] == report['summary']['total_checks']
    
    return report


def save_validation_report(report: Dict[str, Any]) -> None:
    """
    Save validation report to JSON file.
    
    Args:
        report: Validation report dictionary
    """
    logger.info(f"Saving validation report to {VALIDATION_REPORT}")
    
    # Create output directory if it doesn't exist
    VALIDATION_REPORT.parent.mkdir(parents=True, exist_ok=True)
    
    with open(VALIDATION_REPORT, 'w') as f:
        json.dump(report, f, indent=2)
    
    file_size_kb = VALIDATION_REPORT.stat().st_size / 1024
    logger.info(f"  - Report saved successfully ({file_size_kb:.2f} KB)")


def main():
    """Main execution function."""
    logger.info("="*70)
    logger.info("Model Validation - Test Set Evaluation")
    logger.info("="*70)
    
    try:
        # Load and prepare data
        logger.info("\n[STEP 1] Loading and preparing data...")
        X, y = load_and_prepare_data()
        
        # Split data
        logger.info("\n[STEP 2] Splitting data...")
        X_train, X_val, X_test, y_train, y_val, y_test = split_data(X, y)
        
        # Load trained model and preprocessor
        logger.info("\n[STEP 3] Loading trained model...")
        model, preprocessor = load_model_and_preprocessor()
        
        # Preprocess test data
        logger.info("\n[STEP 4] Preprocessing test data...")
        X_test_processed = preprocessor.transform(X_test)
        y_test_encoded = preprocessor.target_encoder.transform(y_test.astype(str))
        logger.info(f"  - Test set shape: {X_test_processed.shape}")
        
        # Evaluate model on test set
        logger.info("\n[STEP 5] Evaluating model on test set...")
        metrics = evaluate_model_on_test_set(model, X_test_processed, y_test_encoded)
        
        # Test prediction latency
        logger.info("\n[STEP 6] Testing prediction latency...")
        latency_metrics = test_prediction_latency(model, X_test_processed)
        
        # Validate against thresholds
        logger.info("\n[STEP 7] Validating against performance thresholds...")
        validation_results = validate_against_thresholds(metrics)
        
        # Generate validation report
        logger.info("\n[STEP 8] Generating validation report...")
        model_version = preprocessor.get_config().get('model_version', '1.0.0') if hasattr(preprocessor, 'get_config') else '1.0.0'
        report = generate_validation_report(metrics, latency_metrics, validation_results, model_version)
        
        # Save report
        logger.info("\n[STEP 9] Saving validation report...")
        save_validation_report(report)
        
        # Print summary
        logger.info("\n" + "="*70)
        logger.info("VALIDATION SUMMARY")
        logger.info("="*70)
        logger.info(f"Overall Status: {report['overall_validation_status']}")
        logger.info(f"Checks Passed: {report['summary']['checks_passed']}/{report['summary']['total_checks']}")
        logger.info(f"  ✓ Accuracy >= {THRESHOLDS['accuracy_min']}: {validation_results['accuracy']['passed']}")
        logger.info(f"  ✓ AUC-ROC >= {THRESHOLDS['auc_roc_min']}: {validation_results['auc_roc']['passed']}")
        logger.info(f"  ✓ Latency < {LATENCY_THRESHOLD_MS}ms: {latency_metrics['meets_requirement']}")
        logger.info("="*70 + "\n")
        
        # Return appropriate exit code
        exit_code = 0 if report['overall_validation_status'] == 'PASS' else 1
        return exit_code
        
    except Exception as e:
        logger.error(f"\n✗ Error during validation: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
