"""
Test script to verify the downloaded UCI diabetes dataset.

This script performs basic checks to ensure the dataset is suitable
for training the readmission prediction model.
"""

import sys
from pathlib import Path

import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from download_uci_dataset import OUTPUT_CSV, EXPECTED_KEY_COLUMNS


def test_dataset():
    """Run dataset tests."""
    print("Testing UCI Diabetes Dataset")
    print("=" * 60)
    
    # Test 1: File exists
    print("\n1. Checking file exists...")
    if not OUTPUT_CSV.exists():
        print(f"   ✗ FAIL: Dataset not found at {OUTPUT_CSV}")
        print(f"   Run: python scripts/download_uci_dataset.py")
        return False
    print(f"   ✓ PASS: File exists at {OUTPUT_CSV}")
    
    # Test 2: File is not empty
    print("\n2. Checking file size...")
    file_size = OUTPUT_CSV.stat().st_size
    if file_size < 1024 * 1024:  # < 1 MB
        print(f"   ✗ FAIL: File too small ({file_size} bytes)")
        return False
    print(f"   ✓ PASS: File size is {file_size / (1024 * 1024):.2f} MB")
    
    # Test 3: Can be loaded as CSV
    print("\n3. Checking CSV loading...")
    try:
        df = pd.read_csv(OUTPUT_CSV, nrows=10)
    except Exception as e:
        print(f"   ✗ FAIL: Cannot load CSV: {e}")
        return False
    print(f"   ✓ PASS: CSV loads successfully")
    
    # Test 4: Has expected columns
    print("\n4. Checking required columns...")
    df_full = pd.read_csv(OUTPUT_CSV)
    missing_cols = []
    for col in EXPECTED_KEY_COLUMNS:
        if col not in df_full.columns:
            missing_cols.append(col)
    
    if missing_cols:
        print(f"   ✗ FAIL: Missing columns: {missing_cols}")
        return False
    print(f"   ✓ PASS: All required columns present")
    
    # Test 5: Has sufficient rows
    print("\n5. Checking row count...")
    if len(df_full) < 50000:
        print(f"   ✗ FAIL: Too few rows ({len(df_full)})")
        return False
    print(f"   ✓ PASS: Dataset has {len(df_full):,} rows")
    
    # Test 6: Target variable exists and has expected values
    print("\n6. Checking target variable...")
    if 'readmitted' not in df_full.columns:
        print(f"   ✗ FAIL: 'readmitted' column not found")
        return False
    
    unique_values = set(df_full['readmitted'].unique())
    expected_values = {'NO', '<30', '>30'}
    
    if not unique_values == expected_values:
        print(f"   ✗ FAIL: Unexpected readmitted values: {unique_values}")
        print(f"   Expected: {expected_values}")
        return False
    
    distribution = df_full['readmitted'].value_counts()
    print(f"   ✓ PASS: Target variable valid")
    print(f"   Distribution:")
    for value, count in distribution.items():
        pct = count / len(df_full) * 100
        print(f"     - {value}: {count:,} ({pct:.1f}%)")
    
    # Test 7: No completely empty columns
    print("\n7. Checking for empty columns...")
    empty_cols = df_full.columns[df_full.isnull().all()].tolist()
    if empty_cols:
        print(f"   ✗ FAIL: Empty columns found: {empty_cols}")
        return False
    print(f"   ✓ PASS: No completely empty columns")
    
    # Test 8: Data types are reasonable
    print("\n8. Checking data types...")
    numeric_cols = df_full.select_dtypes(include=['int64', 'float64']).columns
    categorical_cols = df_full.select_dtypes(include=['object']).columns
    
    print(f"   - Numeric columns: {len(numeric_cols)}")
    print(f"   - Categorical columns: {len(categorical_cols)}")
    print(f"   ✓ PASS: Data types loaded correctly")
    
    print("\n" + "=" * 60)
    print("All tests passed! Dataset is ready for model training.")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    success = test_dataset()
    sys.exit(0 if success else 1)
