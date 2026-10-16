"""
Synthetic Data Generation Script

Generates realistic synthetic patient data using Faker for training the readmission 
prediction model when the UCI dataset is unavailable.

Features:
- Generates 100+ synthetic patients with realistic demographics
- Creates encounter data with admission/discharge dates
- Generates plausible diagnoses, medications, and lab results
- Calculates synthetic readmission outcomes with ~25% readmission rate
- Outputs to CSV format compatible with training pipeline
- Supports reproducible generation with seed parameter

Requirements: 9.3 (Fallback data for ML model training)
"""

import logging
import sys
from pathlib import Path
from typing import Optional, Tuple, List
from datetime import datetime, timedelta
import random
import uuid

import pandas as pd
import numpy as np

try:
    from faker import Faker
except ImportError:
    print("Error: faker package is not installed.")
    print("Install it with: pip install faker")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
DATA_DIR = Path(__file__).parent.parent / "data" / "datasets"
OUTPUT_CSV = DATA_DIR / "synthetic_diabetic_data.csv"
NUM_PATIENTS = 150  # Generate 150 synthetic patients
READMISSION_RATE = 0.25  # Target ~25% readmission rate


class SyntheticDataGenerator:
    """Generate realistic synthetic patient data for readmission prediction."""
    
    # Common diabetes-related diagnoses (ICD-10 codes approximated as strings)
    DIAGNOSES = [
        'E11', 'E10', 'E13', 'I10', 'I50',  # Diabetes, Hypertension, Heart Failure
        'N18', 'J45', 'F41', 'E66', 'I25',  # CKD, Asthma, Anxiety, Obesity, CAD
        'J44', 'E78', 'M79', 'K21', 'E03',  # COPD, Hyperlipidemia, Muscle problems, GERD, Hypothyroidism
    ]
    
    # Common medications
    MEDICATIONS = [
        'Metformin', 'Insulin', 'Lisinopril', 'Atorvastatin', 'Amlodipine',
        'Metoprolol', 'Furosemide', 'Omeprazole', 'Albuterol', 'Levothyroxine',
        'Warfarin', 'Clopidogrel', 'Aspirin', 'Losartan', 'Hydrochlorothiazide',
        'Glipizide', 'Pioglitazone', 'Sitagliptin', 'Gabapentin', 'Sertraline',
    ]
    
    # Race categories (approximating UCI dataset)
    RACES = ['Caucasian', 'African American', 'Hispanic', 'Asian', 'Other']
    
    # Gender values
    GENDERS = ['M', 'F']
    
    # Admission sources
    ADMISSION_SOURCES = [
        'Emergency', 'Physician Referral', 'Routine/Scheduled',
        'Transfer from another healthcare facility'
    ]
    
    # Discharge dispositions
    DISCHARGE_DISPOSITIONS = [
        'Discharged to home', 'Discharged to skilled nursing facility',
        'Discharged to home health service', 'Discharged/transferred to another facility',
        'Discharged against medical advice'
    ]
    
    # Reasons for readmission (if readmitted)
    READMISSION_REASONS = [
        'Diabetes complications', 'Heart failure exacerbation',
        'Infection/sepsis', 'Medication non-compliance',
        'Acute illness', 'Chronic disease management',
        'Surgical complication', 'Fall/injury', 'Other'
    ]
    
    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the synthetic data generator.
        
        Args:
            seed: Random seed for reproducibility
        """
        self.fake = Faker()
        if seed:
            Faker.seed(seed)
            random.seed(seed)
            np.random.seed(seed)
            self.seed = seed
        else:
            self.seed = None
        
        logger.info(f"Initialized SyntheticDataGenerator (seed={self.seed})")
    
    def generate_patient_demographics(self) -> dict:
        """
        Generate realistic patient demographics.
        
        Returns:
            Dictionary with demographic fields
        """
        age = int(np.random.beta(2, 2) * 70 + 18)  # Biased towards 40-60
        dob = self.fake.date_of_birth(
            minimum_age=max(18, age - 2),
            maximum_age=age
        )
        
        return {
            'patient_id': str(uuid.uuid4()),
            'age': age,
            'gender': random.choice(self.GENDERS),
            'race': random.choice(self.RACES),
            'date_of_birth': dob.isoformat(),
            'weight_kg': int(np.random.normal(85, 25)),  # Realistic weight distribution
            'height_cm': int(np.random.normal(170, 10)),  # Realistic height distribution
        }
    
    def calculate_bmi(self, weight_kg: int, height_cm: int) -> float:
        """Calculate BMI from weight and height."""
        height_m = height_cm / 100
        return round(weight_kg / (height_m ** 2), 1)
    
    def generate_encounter_data(self, patient_id: str, admission_date: datetime) -> dict:
        """
        Generate encounter (admission/discharge) data.
        
        Args:
            patient_id: Patient UUID
            admission_date: Date of admission
            
        Returns:
            Dictionary with encounter fields
        """
        # Length of stay: 2-30 days (skewed towards shorter stays)
        los = int(np.random.exponential(4) + 1)
        los = min(max(los, 2), 30)
        
        discharge_date = admission_date + timedelta(days=los)
        
        return {
            'encounter_id': str(uuid.uuid4()),
            'patient_id': patient_id,
            'admission_source': random.choice(self.ADMISSION_SOURCES),
            'admission_date': admission_date.isoformat(),
            'discharge_date': discharge_date.isoformat(),
            'time_in_hospital': los,
            'discharge_disposition': random.choice(self.DISCHARGE_DISPOSITIONS),
        }
    
    def generate_diagnoses(self) -> List[str]:
        """
        Generate realistic diagnosis list.
        
        Returns:
            List of diagnosis codes (1-5 diagnoses)
        """
        num_diagnoses = int(np.random.exponential(1.5) + 1)
        num_diagnoses = min(max(num_diagnoses, 1), 5)
        return random.sample(self.DIAGNOSES, min(num_diagnoses, len(self.DIAGNOSES)))
    
    def generate_medications(self) -> List[str]:
        """
        Generate realistic medication list.
        
        Returns:
            List of medications (2-15 medications, polypharmacy common in readmission)
        """
        num_medications = int(np.random.exponential(2.5) + 2)
        num_medications = min(max(num_medications, 2), 15)
        return random.sample(self.MEDICATIONS, min(num_medications, len(self.MEDICATIONS)))
    
    def generate_lab_values(self) -> dict:
        """
        Generate realistic lab results.
        
        Returns:
            Dictionary with lab values
        """
        # HbA1c (glycated hemoglobin) - 4-14%
        hba1c = round(np.random.normal(8, 2), 1)
        hba1c = min(max(hba1c, 4), 14)
        
        # Creatinine - 0.5-3.0 (abnormal if > 1.2)
        creatinine = round(np.random.normal(1.2, 0.5), 2)
        creatinine = min(max(creatinine, 0.5), 3.0)
        
        # BUN - 7-20 mg/dL normal
        bun = int(np.random.normal(18, 5))
        bun = min(max(bun, 7), 50)
        
        # Glucose - 70-100 normal fasting
        glucose = int(np.random.normal(140, 40))
        glucose = min(max(glucose, 70), 300)
        
        # Potassium - 3.5-5.0 normal
        potassium = round(np.random.normal(4.2, 0.4), 1)
        potassium = min(max(potassium, 3.0), 6.0)
        
        return {
            'hba1c': hba1c,
            'creatinine': creatinine,
            'bun': bun,
            'glucose': glucose,
            'potassium': potassium,
        }
    
    def should_readmit(self, los: int, num_medications: int, num_diagnoses: int, age: int) -> bool:
        """
        Determine if patient should be readmitted based on risk factors.
        Uses a logistic model to create realistic readmission patterns with ~25% rate.
        
        Args:
            los: Length of stay
            num_medications: Number of medications
            num_diagnoses: Number of diagnoses
            age: Patient age
            
        Returns:
            True if patient should be readmitted, False otherwise
        """
        # Logistic regression style scoring with calibrated weights
        # Baseline risk
        risk_score = 0.2
        
        # Length of stay factor (longer stay = higher risk)
        # Normalized by dividing by 10
        risk_score += (los / 10) * 0.15
        
        # Polypharmacy factor (5-10 meds = moderate risk, 10+ = high risk)
        if num_medications >= 5:
            risk_score += 0.15
        if num_medications >= 10:
            risk_score += 0.15
        
        # Comorbidity factor
        if num_diagnoses >= 2:
            risk_score += 0.1
        if num_diagnoses >= 4:
            risk_score += 0.1
        
        # Age factor (older age = higher risk)
        if age >= 60:
            risk_score += 0.08
        if age >= 70:
            risk_score += 0.08
        if age >= 80:
            risk_score += 0.07
        
        # Add some randomness to create natural variation
        risk_score += np.random.normal(0, 0.08)
        
        # Ensure score is between 0 and 1
        risk_score = min(max(risk_score, 0), 1)
        
        # Use risk_score as probability directly (~25% threshold ≈ 0.25)
        # This creates ~25% readmission rate across population
        return random.random() < risk_score
    
    def generate_readmission_data(
        self,
        should_readmit: bool,
        discharge_date: datetime
    ) -> Tuple[bool, Optional[str], Optional[int]]:
        """
        Generate readmission outcome data.
        
        Args:
            should_readmit: Whether patient is at risk for readmission
            discharge_date: Original discharge date
            
        Returns:
            Tuple of (readmitted, readmission_reason, days_to_readmission)
        """
        if should_readmit:
            # ~80% of high-risk patients actually readmit within 90 days
            if random.random() < 0.8:
                # Most readmissions within 30 days, some within 60-90 days
                if random.random() < 0.7:
                    # 70% within 30 days (peak readmission window)
                    days_to_readmit = random.randint(1, 30)
                else:
                    # 30% between 31-90 days
                    days_to_readmit = random.randint(31, 90)
                
                readmission_reason = random.choice(self.READMISSION_REASONS)
                return True, readmission_reason, days_to_readmit
        
        return False, None, None
    
    def generate_patient_record(self, patient_idx: int) -> dict:
        """
        Generate a complete synthetic patient record.
        
        Args:
            patient_idx: Patient index (for generating admission dates)
            
        Returns:
            Dictionary with all patient data
        """
        # Generate demographics
        demographics = self.generate_patient_demographics()
        
        # Admission date: spread over past 2 years (using timezone-aware datetime)
        days_ago = random.randint(30, 730)
        admission_date = datetime.now() - timedelta(days=days_ago)
        
        # Generate encounter
        encounter = self.generate_encounter_data(demographics['patient_id'], admission_date)
        
        # Generate clinical data
        diagnoses = self.generate_diagnoses()
        medications = self.generate_medications()
        lab_values = self.generate_lab_values()
        
        # Determine readmission
        should_readmit_flag = self.should_readmit(
            encounter['time_in_hospital'],
            len(medications),
            len(diagnoses),
            demographics['age']
        )
        
        readmitted, readmission_reason, days_to_readmission = self.generate_readmission_data(
            should_readmit_flag,
            datetime.fromisoformat(encounter['discharge_date'])
        )
        
        # Combine all data into single record
        record = {
            **demographics,
            **encounter,
            'bmi': self.calculate_bmi(demographics['weight_kg'], demographics['height_cm']),
            'number_diagnoses': len(diagnoses),
            'num_medications': len(medications),
            'number_of_previous_admissions': max(0, int(np.random.exponential(1.5))),
            'number_of_previous_emergency_visits': max(0, int(np.random.exponential(1))),
            'number_of_procedures': max(0, int(np.random.exponential(0.5))),
            'hba1c': lab_values['hba1c'],
            'creatinine': lab_values['creatinine'],
            'bun': lab_values['bun'],
            'glucose': lab_values['glucose'],
            'potassium': lab_values['potassium'],
            'readmitted': 1 if readmitted else 0,  # Binary encoding
        }
        
        # Add readmission details only if readmitted
        if readmitted:
            record['readmission_reason'] = readmission_reason
            record['days_to_readmission'] = days_to_readmission
        else:
            record['readmission_reason'] = None
            record['days_to_readmission'] = None
        
        return record
    
    def generate_dataset(self, num_patients: int = NUM_PATIENTS) -> pd.DataFrame:
        """
        Generate complete synthetic dataset.
        
        Args:
            num_patients: Number of patients to generate
            
        Returns:
            DataFrame with synthetic patient data
        """
        logger.info(f"Generating {num_patients} synthetic patient records...")
        
        records = []
        for i in range(num_patients):
            if (i + 1) % 20 == 0:
                logger.info(f"  Generated {i + 1}/{num_patients} records...")
            
            record = self.generate_patient_record(i)
            records.append(record)
        
        df = pd.DataFrame(records)
        
        logger.info(f"✓ Generated {len(df)} records")
        logger.info(f"  - Total columns: {len(df.columns)}")
        logger.info(f"  - Memory usage: {df.memory_usage(deep=True).sum() / (1024 * 1024):.2f} MB")
        
        # Log summary statistics
        logger.info("Summary Statistics:")
        logger.info(f"  - Age: mean={df['age'].mean():.1f}, min={df['age'].min()}, max={df['age'].max()}")
        logger.info(f"  - Time in hospital: mean={df['time_in_hospital'].mean():.1f}, min={df['time_in_hospital'].min()}, max={df['time_in_hospital'].max()}")
        logger.info(f"  - Number of medications: mean={df['num_medications'].mean():.1f}, min={df['num_medications'].min()}, max={df['num_medications'].max()}")
        logger.info(f"  - Number of diagnoses: mean={df['number_diagnoses'].mean():.1f}, min={df['number_diagnoses'].min()}, max={df['number_diagnoses'].max()}")
        logger.info(f"  - HbA1c: mean={df['hba1c'].mean():.1f}, min={df['hba1c'].min():.1f}, max={df['hba1c'].max():.1f}")
        
        # Log readmission rate
        readmission_rate = (df['readmitted'] == 1).sum() / len(df)
        logger.info(f"  - Readmission rate: {readmission_rate*100:.1f}%")
        
        return df
    
    def save_dataset(self, df: pd.DataFrame, output_path: Path) -> bool:
        """
        Save dataset to CSV file.
        
        Args:
            df: DataFrame to save
            output_path: Path to save CSV
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Saving synthetic dataset to {output_path}")
            
            # Create parent directory if needed
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save to CSV
            df.to_csv(output_path, index=False)
            
            file_size_mb = output_path.stat().st_size / (1024 * 1024)
            logger.info(f"✓ Dataset saved successfully ({file_size_mb:.2f} MB)")
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving dataset: {e}")
            return False


def validate_generated_csv(csv_path: Path) -> bool:
    """
    Validate the generated CSV file.
    
    Args:
        csv_path: Path to CSV file
        
    Returns:
        True if validation passed, False otherwise
    """
    try:
        logger.info(f"Validating generated CSV: {csv_path}")
        
        df = pd.read_csv(csv_path)
        
        logger.info(f"CSV loaded successfully")
        logger.info(f"  - Total rows: {len(df):,}")
        logger.info(f"  - Total columns: {len(df.columns)}")
        
        # Check required columns
        required_columns = [
            'age', 'gender', 'race', 'time_in_hospital', 'num_medications',
            'number_diagnoses', 'readmitted'
        ]
        
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            logger.error(f"Missing required columns: {missing}")
            return False
        
        logger.info("✓ All required columns present")
        
        # Check data types and ranges
        if df['readmitted'].isin([0, 1]).all():
            readmit_rate = (df['readmitted'] == 1).sum() / len(df)
            logger.info(f"✓ Readmission column valid (rate: {readmit_rate*100:.1f}%)")
        else:
            logger.error("Invalid readmitted values (should be 0 or 1)")
            return False
        
        if df['age'].min() >= 18 and df['age'].max() <= 120:
            logger.info(f"✓ Age range valid ({df['age'].min()}-{df['age'].max()})")
        else:
            logger.error("Invalid age values")
            return False
        
        logger.info("✓ CSV validation passed")
        return True
        
    except Exception as e:
        logger.error(f"Error validating CSV: {e}")
        return False


def main():
    """Main execution function."""
    logger.info("="*60)
    logger.info("Synthetic Data Generation Script")
    logger.info("="*60)
    
    # Create data directory
    logger.info(f"Creating data directory: {DATA_DIR}")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Initialize generator (with seed for reproducibility)
    generator = SyntheticDataGenerator(seed=42)
    
    # Generate dataset
    df = generator.generate_dataset(num_patients=NUM_PATIENTS)
    
    # Save dataset
    if not generator.save_dataset(df, OUTPUT_CSV):
        logger.error("✗ Failed to save dataset")
        return 1
    
    # Validate saved CSV
    if not validate_generated_csv(OUTPUT_CSV):
        logger.error("✗ CSV validation failed")
        return 1
    
    logger.info("="*60)
    logger.info("✓ Synthetic data generation completed successfully!")
    logger.info(f"Dataset location: {OUTPUT_CSV}")
    logger.info("="*60)
    
    return 0


if __name__ == "__main__":
    exit(main())
