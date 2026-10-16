"""
UCI Diabetes 130-US Hospitals Dataset Download Script

Downloads the UCI Diabetes 130-US hospitals (1999-2008) dataset for training
the readmission prediction model.

Features:
- Downloads from UCI ML Repository using official ucimlrepo package
- Validates CSV structure
- Retry logic with exponential backoff (3 attempts)
- Stores in backend/data/datasets/ directory

Requirements: 9.3
"""

import logging
import sys
import time
import subprocess
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
UCI_DATASET_ID = 296  # Diabetes 130-US hospitals dataset ID
DATA_DIR = Path(__file__).parent.parent / "data" / "datasets"
OUTPUT_CSV = DATA_DIR / "diabetic_data.csv"

# Expected key columns for validation (based on UCI features, not IDs)
EXPECTED_KEY_COLUMNS = [
    'race', 'gender', 'age',
    'time_in_hospital', 'num_medications', 'number_diagnoses',
    'readmitted'
]

# Retry configuration
MAX_RETRIES = 3
INITIAL_BACKOFF = 2  # seconds


def ensure_ucimlrepo_installed() -> bool:
    """
    Ensure ucimlrepo package is installed.
    
    Returns:
        True if package is available, False otherwise
    """
    try:
        import ucimlrepo
        logger.info("✓ ucimlrepo package is already installed")
        return True
    except ImportError:
        logger.info("ucimlrepo package not found, attempting to install...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "ucimlrepo", "--quiet"
            ])
            logger.info("✓ Successfully installed ucimlrepo package")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install ucimlrepo: {e}")
            return False


def download_dataset_with_retry(dataset_id: int, max_retries: int = MAX_RETRIES) -> Optional[Tuple[pd.DataFrame, pd.DataFrame]]:
    """
    Download dataset using UCI ML Repository package with retry logic.
    
    Args:
        dataset_id: UCI dataset ID
        max_retries: Maximum number of retry attempts
        
    Returns:
        Tuple of (features_df, targets_df) if successful, None otherwise
    """
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Attempt {attempt}/{max_retries}: Fetching dataset ID {dataset_id} from UCI repository")
            
            # Import here to allow for installation first
            from ucimlrepo import fetch_ucirepo
            
            # Fetch dataset
            dataset = fetch_ucirepo(id=dataset_id)
            
            # Extract features and targets
            X = dataset.data.features
            y = dataset.data.targets
            
            logger.info(f"Successfully downloaded dataset")
            logger.info(f"  - Features shape: {X.shape}")
            logger.info(f"  - Targets shape: {y.shape}")
            
            return X, y
            
        except Exception as e:
            logger.error(f"Error on attempt {attempt}: {e}")
            if attempt < max_retries:
                backoff = INITIAL_BACKOFF ** attempt
                logger.info(f"Retrying in {backoff} seconds...")
                time.sleep(backoff)
            else:
                logger.error(f"Failed after {max_retries} attempts")
                return None
    
    return None


def combine_and_save_dataset(X: pd.DataFrame, y: pd.DataFrame, output_path: Path) -> bool:
    """
    Combine features and targets into single CSV file.
    
    Args:
        X: Features dataframe
        y: Targets dataframe
        output_path: Path to save combined CSV
        
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info("Combining features and targets...")
        
        # Combine dataframes
        df = pd.concat([X, y], axis=1)
        
        logger.info(f"Combined dataset shape: {df.shape}")
        
        # Save to CSV
        logger.info(f"Saving to {output_path}")
        df.to_csv(output_path, index=False)
        
        file_size_mb = output_path.stat().st_size / (1024 * 1024)
        logger.info(f"✓ Dataset saved successfully ({file_size_mb:.2f} MB)")
        
        return True
        
    except Exception as e:
        logger.error(f"Error saving dataset: {e}")
        return False


def validate_csv_structure(csv_path: Path) -> bool:
    """
    Validate CSV structure and content.
    
    Args:
        csv_path: Path to CSV file
        
    Returns:
        True if validation passed, False otherwise
    """
    try:
        logger.info(f"Validating CSV structure: {csv_path}")
        
        # Read CSV
        logger.info("Loading dataset for validation...")
        df = pd.read_csv(csv_path)
        
        logger.info(f"Dataset loaded successfully")
        logger.info(f"  - Total rows: {len(df):,}")
        logger.info(f"  - Total columns: {len(df.columns)}")
        logger.info(f"  - Memory usage: {df.memory_usage(deep=True).sum() / (1024 * 1024):.2f} MB")
        
        # Check for expected key columns
        df_columns_lower = [col.lower() for col in df.columns]
        expected_columns_lower = [col.lower() for col in EXPECTED_KEY_COLUMNS]
        
        missing_columns = []
        for expected_col in expected_columns_lower:
            if expected_col not in df_columns_lower:
                missing_columns.append(expected_col)
        
        if missing_columns:
            logger.error(f"Missing required columns: {missing_columns}")
            return False
        else:
            logger.info("✓ All required columns present")
        
        # Check for readmitted column (target variable)
        if 'readmitted' in df.columns:
            readmitted_dist = df['readmitted'].value_counts()
            logger.info(f"Readmitted distribution:\n{readmitted_dist}")
        else:
            logger.error("'readmitted' column not found - this is the target variable!")
            return False
        
        # Check data quality
        total_missing = df.isnull().sum().sum()
        total_cells = df.shape[0] * df.shape[1]
        missing_pct = (total_missing / total_cells * 100)
        
        logger.info(f"Data quality:")
        logger.info(f"  - Total missing values: {total_missing:,} ({missing_pct:.2f}%)")
        
        # Warn about columns with high missing values
        missing_pct_per_col = (df.isnull().sum() / len(df) * 100).round(2)
        high_missing = missing_pct_per_col[missing_pct_per_col > 50]
        
        if not high_missing.empty:
            logger.warning(f"Columns with >50% missing values: {len(high_missing)}")
            for col, pct in high_missing.items():
                logger.warning(f"  - {col}: {pct}% missing")
        
        # Validate row count (expected ~100k rows)
        if len(df) < 50000:
            logger.warning(f"Dataset has fewer rows than expected ({len(df)} vs ~100k)")
        
        logger.info("✓ CSV validation completed successfully")
        return True
        
    except pd.errors.EmptyDataError:
        logger.error("CSV file is empty")
        return False
    except pd.errors.ParserError as e:
        logger.error(f"CSV parsing error: {e}")
        return False
    except Exception as e:
        logger.error(f"Error validating CSV: {e}")
        return False


def main():
    """Main execution function."""
    logger.info("="*60)
    logger.info("UCI Diabetes Dataset Download Script")
    logger.info("="*60)
    
    # Create data directory
    logger.info(f"Creating data directory: {DATA_DIR}")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Check if dataset already exists
    if OUTPUT_CSV.exists():
        logger.info(f"Dataset already exists at {OUTPUT_CSV}")
        
        # Validate existing dataset
        if validate_csv_structure(OUTPUT_CSV):
            logger.info("✓ Existing dataset is valid")
            logger.info("="*60)
            logger.info("Dataset is ready for use!")
            logger.info(f"Dataset location: {OUTPUT_CSV}")
            logger.info("="*60)
            return 0
        else:
            logger.warning("Existing dataset validation failed, re-downloading...")
            OUTPUT_CSV.unlink()
    
    # Ensure ucimlrepo package is installed
    if not ensure_ucimlrepo_installed():
        logger.error("✗ Failed to install required package")
        return 1
    
    # Download dataset
    logger.info(f"Downloading UCI dataset ID {UCI_DATASET_ID}")
    result = download_dataset_with_retry(UCI_DATASET_ID)
    
    if not result:
        logger.error("✗ Failed to download dataset")
        return 1
    
    X, y = result
    logger.info(f"✓ Download completed successfully")
    
    # Combine and save dataset
    if not combine_and_save_dataset(X, y, OUTPUT_CSV):
        logger.error("✗ Failed to save dataset")
        return 1
    
    # Validate saved CSV
    if not validate_csv_structure(OUTPUT_CSV):
        logger.error("✗ CSV validation failed")
        return 1
    
    logger.info("✓ CSV validation passed")
    
    logger.info("="*60)
    logger.info("Dataset download and setup completed successfully!")
    logger.info(f"Dataset location: {OUTPUT_CSV}")
    logger.info("="*60)
    
    return 0


if __name__ == "__main__":
    exit(main())
