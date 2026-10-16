"""
XGBoost Ensemble Training Script

Loads the UCI diabetes dataset, preprocesses features, trains an XGBoost
classifier for readmission prediction, and saves the model with performance metrics.

Requirements:
- Section 9: Machine Learning Risk Prediction Model
- 5.2: Create XGBoost ensemble training script

Features:
- Data loading from CSV
- Train/val/test split (60/20/20)
- Feature preprocessing and encoding
- Feature scaling with StandardScaler
- XGBoost classifier training
- Performance metrics logging
- Model serialization to pickle
"""

import logging
import sys
import pickle
from pathlib import Path
from typing import Tuple, Dict, Any

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report
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
METRICS_OUTPUT = BACKEND_DIR / "app" / "models" / "model_metrics.json"

# Model parameters
RANDOM_STATE = 42
TEST_SIZE = 0.2  # 20% for test
VAL_SIZE = 0.25  # 25% of remaining 80% = 20% overall
TRAIN_SIZE = 0.6  # 60% for training

# XGBoost hyperparameters
XGBOOST_PARAMS = {
    'n_estimators': 100,
    'max_depth': 6,
    'learning_rate': 0.1,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'objective': 'binary:logistic',
    'random_state': RANDOM_STATE,
    'n_jobs': -1,
    'eval_metric': 'logloss',
    'verbosity': 1,
}

# Features to use for model (based on UCI diabetes dataset)
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

# Categorical columns to encode
CATEGORICAL_COLUMNS = [
    'race', 'gender', 'age', 'A1Cresult', 'max_glu_serum', 'diabetic_med_changed',
    'change', 'diabetesMed', 'metformin', 'repaglinide', 'nateglinide',
    'chlorpropamide', 'glimepiride', 'acetohexamide', 'glipizide', 'glyburide',
    'tolbutamide', 'pioglitazone', 'rosiglitazone', 'acarbose', 'miglitol',
    'troglitazone', 'tolazamide', 'examide', 'citoglipton', 'insulin',
    'glyburide-metformin', 'glipizide-metformin', 'metformin-rosiglitazone',
    'metformin-pioglitazone'
]


class ModelPreprocessor:
    """Handles data preprocessing and feature scaling."""
    
    def __init__(self):
        self.label_encoders: Dict[str, LabelEncoder] = {}
        self.scaler = StandardScaler()
        self.feature_columns = []
        self.numeric_columns = []
        self.categorical_columns = []
    
    def fit_and_transform(self, X: pd.DataFrame, y: pd.Series) -> Tuple[np.ndarray, np.ndarray]:
        """
        Fit preprocessor and transform training data.
        
        Args:
            X: Training features
            y: Training target
            
        Returns:
            Tuple of (transformed features, transformed target)
        """
        logger.info("Fitting preprocessor on training data...")
        
        # Store columns
        self.feature_columns = X.columns.tolist()
        
        # Identify numeric and categorical columns
        self.numeric_columns = X.select_dtypes(include=[np.number]).columns.tolist()
        self.categorical_columns = X.select_dtypes(include=['object']).columns.tolist()
        
        logger.info(f"  - Numeric columns: {len(self.numeric_columns)}")
        logger.info(f"  - Categorical columns: {len(self.categorical_columns)}")
        
        # Encode categorical features
        X_encoded = X.copy()
        for col in self.categorical_columns:
            le = LabelEncoder()
            X_encoded[col] = le.fit_transform(X[col].astype(str))
            self.label_encoders[col] = le
            logger.info(f"  - Encoded '{col}': {len(le.classes_)} classes")
        
        # Fit scaler on numeric columns
        if self.numeric_columns:
            X_encoded[self.numeric_columns] = self.scaler.fit_transform(
                X_encoded[self.numeric_columns]
            )
            logger.info(f"  - Scaled {len(self.numeric_columns)} numeric columns")
        
        # Encode target variable
        self.target_encoder = LabelEncoder()
        y_encoded = self.target_encoder.fit_transform(y.astype(str))
        logger.info(f"  - Encoded target: {len(self.target_encoder.classes_)} classes")
        
        return X_encoded.values, y_encoded
    
    def transform(self, X: pd.DataFrame) -> np.ndarray:
        """
        Transform data using fitted preprocessor.
        
        Args:
            X: Features to transform
            
        Returns:
            Transformed features
        """
        X_encoded = X.copy()
        
        # Encode categorical features
        for col in self.categorical_columns:
            if col in self.label_encoders:
                le = self.label_encoders[col]
                # Handle unknown categories by using first class
                X_encoded[col] = X[col].map(
                    lambda x: le.transform([str(x)])[0] if str(x) in le.classes_ else 0
                )
        
        # Scale numeric columns
        if self.numeric_columns:
            X_encoded[self.numeric_columns] = self.scaler.transform(
                X_encoded[self.numeric_columns]
            )
        
        return X_encoded.values
    
    def get_config(self) -> Dict[str, Any]:
        """Get preprocessor configuration for serialization."""
        return {
            'feature_columns': self.feature_columns,
            'numeric_columns': self.numeric_columns,
            'categorical_columns': self.categorical_columns,
            'label_encoders': self.label_encoders,
            'scaler': self.scaler,
            'target_encoder': self.target_encoder,
        }


def load_and_prepare_data() -> Tuple[pd.DataFrame, pd.Series]:
    """
    Load and prepare dataset from CSV.
    
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
    
    # Remove target column and ID columns
    features = df.drop(columns=['readmitted'], errors='ignore')
    features = features.drop(columns=['encounter_id', 'patient_nbr'], errors='ignore')
    
    # Select feature columns that exist
    available_features = [col for col in FEATURE_COLUMNS if col in features.columns]
    logger.info(f"  - Using {len(available_features)}/{len(FEATURE_COLUMNS)} available features")
    
    features = features[available_features]
    
    # Handle missing values
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
    
    # Convert age strings to numeric if needed (UCI dataset has age groups)
    if 'age' in features.columns:
        age_col = features['age']
        if age_col.dtype == 'object':
            # Parse age groups like "[70-80)" to numeric
            features['age'] = age_col.str.extract(r'(\d+)').astype(float)
            logger.info("  - Converted age groups to numeric")
    
    # Check target distribution
    logger.info("Target variable distribution:")
    for val, count in target.value_counts().items():
        pct = count / len(target) * 100
        logger.info(f"  - {val}: {count:,} ({pct:.1f}%)")
    
    # Convert multi-class to binary (readmitted vs not readmitted)
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


def train_model(
    X_train: np.ndarray, y_train: np.ndarray,
    X_val: np.ndarray, y_val: np.ndarray
) -> xgb.XGBClassifier:
    """
    Train XGBoost classifier.
    
    Args:
        X_train: Training features
        y_train: Training target
        X_val: Validation features
        y_val: Validation target
        
    Returns:
        Trained XGBoost model
    """
    logger.info("Training XGBoost classifier...")
    logger.info(f"  - Parameters: {XGBOOST_PARAMS}")
    
    model = xgb.XGBClassifier(**XGBOOST_PARAMS)
    
    # Train with early stopping
    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        early_stopping_rounds=10,
        verbose=False
    )
    
    best_iteration = model.best_iteration
    logger.info(f"  - Training completed at iteration {best_iteration}")
    
    return model


def evaluate_model(
    model: xgb.XGBClassifier,
    X_train: np.ndarray, y_train: np.ndarray,
    X_val: np.ndarray, y_val: np.ndarray,
    X_test: np.ndarray, y_test: np.ndarray
) -> Dict[str, Any]:
    """
    Evaluate model on train/val/test sets.
    
    Args:
        model: Trained XGBoost model
        X_train, y_train: Training data
        X_val, y_val: Validation data
        X_test, y_test: Test data
        
    Returns:
        Dictionary of metrics
    """
    logger.info("Evaluating model performance...")
    
    metrics = {}
    
    for dataset_name, X, y in [
        ('train', X_train, y_train),
        ('val', X_val, y_val),
        ('test', X_test, y_test)
    ]:
        y_pred = model.predict(X)
        y_pred_proba = model.predict_proba(X)[:, 1]
        
        accuracy = accuracy_score(y, y_pred)
        precision = precision_score(y, y_pred, zero_division=0)
        recall = recall_score(y, y_pred, zero_division=0)
        f1 = f1_score(y, y_pred, zero_division=0)
        
        # AUC-ROC
        try:
            auc_roc = roc_auc_score(y, y_pred_proba)
        except Exception as e:
            logger.warning(f"Could not compute AUC-ROC for {dataset_name}: {e}")
            auc_roc = 0.0
        
        # Confusion matrix
        tn, fp, fn, tp = confusion_matrix(y, y_pred).ravel()
        
        metrics[dataset_name] = {
            'accuracy': float(accuracy),
            'precision': float(precision),
            'recall': float(recall),
            'f1': float(f1),
            'auc_roc': float(auc_roc),
            'true_negatives': int(tn),
            'false_positives': int(fp),
            'false_negatives': int(fn),
            'true_positives': int(tp),
        }
        
        logger.info(f"\n  {dataset_name.upper()} Set Metrics:")
        logger.info(f"    - Accuracy:  {accuracy:.4f}")
        logger.info(f"    - Precision: {precision:.4f}")
        logger.info(f"    - Recall:    {recall:.4f}")
        logger.info(f"    - F1-Score:  {f1:.4f}")
        logger.info(f"    - AUC-ROC:   {auc_roc:.4f}")
        logger.info(f"    - Confusion Matrix:")
        logger.info(f"      - True Negatives:  {tn}")
        logger.info(f"      - False Positives: {fp}")
        logger.info(f"      - False Negatives: {fn}")
        logger.info(f"      - True Positives:  {tp}")
    
    return metrics


def save_model(
    model: xgb.XGBClassifier,
    preprocessor: ModelPreprocessor,
    metrics: Dict[str, Any]
) -> None:
    """
    Save model and preprocessor to pickle file.
    
    Args:
        model: Trained XGBoost model
        preprocessor: Fitted preprocessor
        metrics: Performance metrics
    """
    logger.info(f"Saving model to {MODEL_OUTPUT}")
    
    # Create output directory
    MODEL_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    
    # Create model package
    model_package = {
        'model': model,
        'preprocessor': preprocessor,
        'metrics': metrics,
        'model_version': '1.0.0',
        'feature_columns': preprocessor.feature_columns,
    }
    
    # Save to pickle
    with open(MODEL_OUTPUT, 'wb') as f:
        pickle.dump(model_package, f)
    
    file_size_mb = MODEL_OUTPUT.stat().st_size / (1024 * 1024)
    logger.info(f"  - Model saved successfully ({file_size_mb:.2f} MB)")
    
    # Save metrics to JSON for reference
    import json
    METRICS_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(METRICS_OUTPUT, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"  - Metrics saved to {METRICS_OUTPUT}")


def main():
    """Main execution function."""
    logger.info("="*70)
    logger.info("XGBoost Readmission Prediction Model Training")
    logger.info("="*70)
    
    try:
        # Load and prepare data
        logger.info("\n[STEP 1] Loading and preparing data...")
        X, y = load_and_prepare_data()
        
        # Split data
        logger.info("\n[STEP 2] Splitting data...")
        X_train, X_val, X_test, y_train, y_val, y_test = split_data(X, y)
        
        # Initialize preprocessor and fit on training data
        logger.info("\n[STEP 3] Preprocessing features...")
        preprocessor = ModelPreprocessor()
        X_train_processed, y_train_encoded = preprocessor.fit_and_transform(X_train, y_train)
        X_val_processed = preprocessor.transform(X_val)
        X_test_processed = preprocessor.transform(X_test)
        y_val_encoded = preprocessor.target_encoder.transform(y_val.astype(str))
        y_test_encoded = preprocessor.target_encoder.transform(y_test.astype(str))
        
        # Train model
        logger.info("\n[STEP 4] Training XGBoost model...")
        model = train_model(X_train_processed, y_train_encoded, X_val_processed, y_val_encoded)
        
        # Evaluate model
        logger.info("\n[STEP 5] Evaluating model performance...")
        metrics = evaluate_model(
            model,
            X_train_processed, y_train_encoded,
            X_val_processed, y_val_encoded,
            X_test_processed, y_test_encoded
        )
        
        # Check if requirements are met
        logger.info("\n[STEP 6] Checking performance requirements...")
        test_accuracy = metrics['test']['accuracy']
        test_auc = metrics['test']['auc_roc']
        
        min_accuracy = 0.75
        min_auc = 0.80
        
        if test_accuracy >= min_accuracy:
            logger.info(f"  ✓ Accuracy requirement met: {test_accuracy:.4f} >= {min_accuracy}")
        else:
            logger.warning(f"  ✗ Accuracy below requirement: {test_accuracy:.4f} < {min_accuracy}")
        
        if test_auc >= min_auc:
            logger.info(f"  ✓ AUC-ROC requirement met: {test_auc:.4f} >= {min_auc}")
        else:
            logger.warning(f"  ✗ AUC-ROC below requirement: {test_auc:.4f} < {min_auc}")
        
        # Save model
        logger.info("\n[STEP 7] Saving model...")
        save_model(model, preprocessor, metrics)
        
        logger.info("\n" + "="*70)
        logger.info("✓ Model training completed successfully!")
        logger.info("="*70)
        
        return 0
        
    except Exception as e:
        logger.error(f"\n✗ Error during training: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
