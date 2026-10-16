#!/usr/bin/env python
"""
Database seed script for ReadmitCare platform

Creates initial:
- Users (admin, doctors, nurses, social workers)
- Wards (Medical, Surgical, ICU)
- Sample patients (50-100 from synthetic or UCI data)
- Encounters with admission/discharge dates
- Model version records

Usage:
    python backend/scripts/seed_db.py
    
Environment variables:
    DATABASE_URL: Database connection string (defaults to SQLite)
    SEED_COUNT: Number of patients to seed (default: 75)
"""

import asyncio
import os
import sys
import logging
import csv
from datetime import datetime, timedelta, date
from pathlib import Path
from uuid import uuid4
from typing import List, Tuple
from decimal import Decimal

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import bcrypt

from app.database import Base, engine, AsyncSessionLocal
from app.models.user import User
from app.models.ward import Ward
from app.models.patient import Patient
from app.models.encounter import Encounter
from app.models.diagnosis import Diagnosis
from app.models.medication import Medication
from app.models.model_version import ModelVersion
from app.models.risk_prediction import RiskPrediction

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Password hashing context
def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')

# Sample data definitions
SAMPLE_DIAGNOSES = [
    ("E11", "Type 2 diabetes mellitus"),
    ("I10", "Essential (primary) hypertension"),
    ("J45", "Asthma"),
    ("K21", "Gastro-esophageal reflux disease"),
    ("M79.3", "Panniculitis, unspecified"),
    ("I50", "Heart failure"),
    ("J44", "Chronic obstructive pulmonary disease"),
    ("E78", "Abdominal and pelvic pain"),
    ("F41", "Anxiety disorders"),
    ("M54", "Dorsalgia (back pain)"),
    ("N39", "Urinary symptoms"),
    ("R06", "Abnormalities of breathing"),
    ("Z79", "Long-term medication use"),
    ("I25", "Ischemic heart disease"),
]

SAMPLE_MEDICATIONS = [
    ("Metformin", "500mg", "twice daily", "oral"),
    ("Lisinopril", "10mg", "once daily", "oral"),
    ("Atorvastatin", "20mg", "once daily at night", "oral"),
    ("Amlodipine", "5mg", "once daily", "oral"),
    ("Omeprazole", "20mg", "once daily", "oral"),
    ("Albuterol", "2 puffs", "as needed", "inhalation"),
    ("Sertraline", "50mg", "once daily", "oral"),
    ("Aspirin", "81mg", "once daily", "oral"),
    ("Insulin Glargine", "10 units", "once daily", "injection"),
    ("Furosemide", "40mg", "once daily", "oral"),
]

DISCHARGE_DISPOSITIONS = [
    "Home",
    "Skilled nursing facility",
    "Long-term care facility",
    "Home with home health care",
    "Against medical advice",
]

FIRST_NAMES = [
    "John", "Mary", "Michael", "Patricia", "Robert", "Linda", "James", "Barbara",
    "William", "Elizabeth", "David", "Jennifer", "Richard", "Maria", "Joseph", "Susan",
    "Thomas", "Jessica", "Charles", "Sarah", "Christopher", "Karen", "Daniel", "Nancy",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
]


async def check_already_seeded(session: AsyncSession) -> bool:
    """Check if database is already seeded."""
    result = await session.execute(select(User).limit(1))
    return result.scalar_one_or_none() is not None


async def create_tables() -> None:
    """Create all database tables."""
    logger.info("Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ Database tables created")


async def seed_users(session: AsyncSession) -> List[User]:
    """Create initial users."""
    logger.info("Seeding users...")
    
    users = [
        User(
            id=uuid4(),
            email="admin@readmitcare.org",
            password_hash=hash_password("Admin@12345"),
            first_name="Admin",
            last_name="User",
            role="admin",
            is_active=True,
        ),
        User(
            id=uuid4(),
            email="dr.smith@readmitcare.org",
            password_hash=hash_password("Doctor@12345"),
            first_name="John",
            last_name="Smith",
            role="doctor",
            is_active=True,
        ),
        User(
            id=uuid4(),
            email="dr.johnson@readmitcare.org",
            password_hash=hash_password("Doctor@12345"),
            first_name="Sarah",
            last_name="Johnson",
            role="doctor",
            is_active=True,
        ),
        User(
            id=uuid4(),
            email="nurse.williams@readmitcare.org",
            password_hash=hash_password("Nurse@12345"),
            first_name="Emily",
            last_name="Williams",
            role="nurse",
            is_active=True,
        ),
        User(
            id=uuid4(),
            email="nurse.brown@readmitcare.org",
            password_hash=hash_password("Nurse@12345"),
            first_name="Michael",
            last_name="Brown",
            role="nurse",
            is_active=True,
        ),
        User(
            id=uuid4(),
            email="nurse.davis@readmitcare.org",
            password_hash=hash_password("Nurse@12345"),
            first_name="Jessica",
            last_name="Davis",
            role="nurse",
            is_active=True,
        ),
        User(
            id=uuid4(),
            email="social.worker@readmitcare.org",
            password_hash=hash_password("Social@12345"),
            first_name="Robert",
            last_name="Miller",
            role="social_worker",
            is_active=True,
        ),
    ]
    
    session.add_all(users)
    await session.flush()
    logger.info(f"✅ Created {len(users)} users")
    return users


async def seed_wards(session: AsyncSession) -> List[Ward]:
    """Create initial wards."""
    logger.info("Seeding wards...")
    
    wards = [
        Ward(
            id=uuid4(),
            name="Medical Ward",
            location="Building A, Floor 2",
            capacity=30,
        ),
        Ward(
            id=uuid4(),
            name="Surgical Ward",
            location="Building B, Floor 1",
            capacity=25,
        ),
        Ward(
            id=uuid4(),
            name="ICU",
            location="Building A, Floor 3",
            capacity=12,
        ),
    ]
    
    session.add_all(wards)
    await session.flush()
    logger.info(f"✅ Created {len(wards)} wards")
    return wards


def load_patient_data_from_csv(csv_path: str, limit: int = 100) -> List[dict]:
    """Load patient data from CSV file."""
    patients_data = []
    csv_file = Path(csv_path)
    
    if not csv_file.exists():
        logger.warning(f"CSV file not found: {csv_path}")
        return []
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if i >= limit:
                    break
                patients_data.append(row)
        logger.info(f"✅ Loaded {len(patients_data)} patients from CSV")
    except Exception as e:
        logger.error(f"Error reading CSV: {e}")
    
    return patients_data


def generate_synthetic_patient(index: int) -> dict:
    """Generate synthetic patient data."""
    return {
        "first_name": FIRST_NAMES[index % len(FIRST_NAMES)],
        "last_name": LAST_NAMES[index % len(LAST_NAMES)],
        "gender": "male" if index % 2 == 0 else "female",
        "age_group": f"[{(index % 8) * 10}-{(index % 8) * 10 + 10})",
        "mrn": f"MRN{str(index).zfill(6)}",
    }


def calculate_age_from_group(age_group: str) -> int:
    """Convert age group string to years (middle of range)."""
    try:
        parts = age_group.strip("[]()").split("-")
        if len(parts) == 2:
            start = int(parts[0])
            end = int(parts[1].rstrip(")"))
            return (start + end) // 2
    except (ValueError, IndexError):
        pass
    return 50  # Default middle age


async def seed_patients(
    session: AsyncSession,
    wards: List[Ward],
    doctors: List[User],
    csv_path: str = None,
    patient_count: int = 75,
) -> List[Patient]:
    """Create sample patients with encounters."""
    logger.info(f"Seeding {patient_count} patients...")
    
    # Try to load from CSV first, fall back to synthetic data
    patients_source = []
    if csv_path:
        patients_source = load_patient_data_from_csv(csv_path, patient_count)
    
    if len(patients_source) < patient_count:
        # Fill remaining with synthetic data
        synthetic_count = patient_count - len(patients_source)
        for i in range(synthetic_count):
            patients_source.append(generate_synthetic_patient(i + len(patients_source)))
    
    patients = []
    now = datetime.utcnow()
    
    for idx, patient_data in enumerate(patients_source[:patient_count]):
        # Extract data with defaults
        first_name = patient_data.get("first_name", FIRST_NAMES[idx % len(FIRST_NAMES)])
        last_name = patient_data.get("last_name", LAST_NAMES[idx % len(LAST_NAMES)])
        gender = patient_data.get("gender", "male" if idx % 2 == 0 else "female")
        mrn = patient_data.get("mrn", f"MRN{str(idx).zfill(6)}")
        
        # Calculate date of birth from age or age group
        age = 50
        if "age_group" in patient_data:
            age = calculate_age_from_group(patient_data["age_group"])
        elif "age" in patient_data:
            try:
                age = int(float(patient_data["age"]))
            except (ValueError, TypeError):
                age = 50
        
        dob = (now - timedelta(days=365 * age + idx)).date()
        
        # Assign to random ward
        ward = wards[idx % len(wards)]
        doctor = doctors[idx % len(doctors)]
        
        patient = Patient(
            id=uuid4(),
            mrn=mrn,
            first_name=first_name,
            last_name=last_name,
            date_of_birth=dob,
            gender=gender.lower() if gender.lower() in ["male", "female", "other", "unknown"] else "unknown",
            phone=f"555-{str(idx).zfill(4)}",
            email=f"{first_name.lower()}.{last_name.lower()}@example.com".replace(" ", ""),
            address=f"{100 + idx} Main St, Hospital City, HC {str(10000 + idx)[:5]}",
            current_ward_id=ward.id,
            primary_provider_id=doctor.id,
        )
        
        session.add(patient)
        patients.append(patient)
    
    await session.flush()
    logger.info(f"✅ Created {len(patients)} patients")
    return patients


async def seed_encounters(
    session: AsyncSession,
    patients: List[Patient],
    doctors: List[User],
) -> List[Encounter]:
    """Create sample encounters for patients."""
    logger.info("Seeding encounters...")
    
    encounters = []
    now = datetime.utcnow()
    
    # Create 1-2 encounters per patient
    for idx, patient in enumerate(patients):
        num_encounters = 1 + (idx % 2)  # 1 or 2 encounters
        
        for enc_idx in range(num_encounters):
            # Discharge date varies: some recent, some older
            days_ago = 7 + (idx % 30)  # 7-37 days ago
            admission_date = now - timedelta(days=days_ago + 5)
            discharge_date = now - timedelta(days=days_ago)
            
            encounter = Encounter(
                id=uuid4(),
                patient_id=patient.id,
                encounter_type="inpatient",
                admission_date=admission_date,
                discharge_date=discharge_date if enc_idx == 0 or idx % 3 != 0 else None,  # Some ongoing
                admitting_provider_id=doctors[idx % len(doctors)].id,
                discharging_provider_id=doctors[(idx + 1) % len(doctors)].id if discharge_date else None,
                discharge_disposition=DISCHARGE_DISPOSITIONS[idx % len(DISCHARGE_DISPOSITIONS)] if discharge_date else None,
            )
            
            session.add(encounter)
            encounters.append(encounter)
    
    await session.flush()
    logger.info(f"✅ Created {len(encounters)} encounters")
    return encounters


async def seed_diagnoses(
    session: AsyncSession,
    encounters: List[Encounter],
) -> int:
    """Add diagnoses to encounters."""
    logger.info("Seeding diagnoses...")
    
    diagnoses_created = 0
    
    for idx, encounter in enumerate(encounters):
        # Add 2-4 diagnoses per encounter
        num_diagnoses = 2 + (idx % 3)
        
        for diag_idx in range(num_diagnoses):
            icd10_code, description = SAMPLE_DIAGNOSES[(idx + diag_idx) % len(SAMPLE_DIAGNOSES)]
            
            diagnosis = Diagnosis(
                id=uuid4(),
                patient_id=encounter.patient_id,
                encounter_id=encounter.id,
                icd10_code=icd10_code,
                description=description,
                is_primary=(diag_idx == 0),  # First diagnosis is primary
                diagnosed_at=encounter.admission_date,
            )
            
            session.add(diagnosis)
            diagnoses_created += 1
    
    await session.flush()
    logger.info(f"✅ Created {diagnoses_created} diagnoses")
    return diagnoses_created


async def seed_medications(
    session: AsyncSession,
    encounters: List[Encounter],
    doctors: List[User],
) -> int:
    """Add medications to patients from encounters."""
    logger.info("Seeding medications...")
    
    medications_created = 0
    
    for idx, encounter in enumerate(encounters):
        # Add 3-6 medications per encounter
        num_medications = 3 + (idx % 4)
        
        for med_idx in range(num_medications):
            med_name, dosage, frequency, route = SAMPLE_MEDICATIONS[(idx + med_idx) % len(SAMPLE_MEDICATIONS)]
            
            medication = Medication(
                id=uuid4(),
                patient_id=encounter.patient_id,
                encounter_id=encounter.id,
                name=med_name,
                dosage=dosage,
                frequency=frequency,
                route=route,
                start_date=encounter.admission_date,
                end_date=encounter.discharge_date,
                prescribing_provider_id=doctors[idx % len(doctors)].id,
            )
            
            session.add(medication)
            medications_created += 1
    
    await session.flush()
    logger.info(f"✅ Created {medications_created} medications")
    return medications_created


async def seed_model_version(session: AsyncSession) -> ModelVersion:
    """Create initial ML model version."""
    logger.info("Seeding model version...")
    
    model_version = ModelVersion(
        id=uuid4(),
        version_name="1.0.0",
        model_type="xgboost",
        hyperparameters={
            "n_estimators": 100,
            "max_depth": 6,
            "learning_rate": 0.1,
            "objective": "binary:logistic",
        },
        metrics={
            "accuracy": 0.782,
            "auc_roc": 0.832,
            "precision": 0.756,
            "recall": 0.723,
            "f1_score": 0.739,
        },
        trained_at=datetime.utcnow(),
        is_active=True,
    )
    
    session.add(model_version)
    await session.flush()
    logger.info("✅ Created model version")
    return model_version


async def seed_risk_predictions(
    session: AsyncSession,
    encounters: List[Encounter],
    model_version: ModelVersion,
) -> int:
    """Create risk predictions for encounters."""
    logger.info("Seeding risk predictions...")
    
    predictions_created = 0
    
    for idx, encounter in enumerate(encounters):
        # Generate risk score based on patient index and diagnoses count
        base_score = 30 + (idx % 50)
        risk_score = Decimal(base_score + (idx % 30))
        
        # Determine risk band
        if float(risk_score) >= 70:
            risk_band = "high"
        elif float(risk_score) >= 40:
            risk_band = "medium"
        else:
            risk_band = "low"
        
        prediction = RiskPrediction(
            id=uuid4(),
            patient_id=encounter.patient_id,
            encounter_id=encounter.id,
            risk_score=risk_score,
            confidence_lower=Decimal(max(0, float(risk_score) - 15)),
            confidence_upper=Decimal(min(100, float(risk_score) + 15)),
            risk_band=risk_band,
            feature_contributions={
                "age": 0.15,
                "comorbidities": 0.25,
                "medications_count": 0.12,
                "previous_admissions": 0.18,
                "discharge_disposition": 0.10,
                "length_of_stay": 0.12,
                "follow_up_scheduled": 0.08,
            },
            model_version_id=model_version.id,
        )
        
        session.add(prediction)
        predictions_created += 1
    
    await session.flush()
    logger.info(f"✅ Created {predictions_created} risk predictions")
    return predictions_created


async def seed_database() -> None:
    """Main seeding function."""
    logger.info("=" * 60)
    logger.info("ReadmitCare Database Seeding Started")
    logger.info("=" * 60)
    
    # Create tables
    await create_tables()
    
    async with AsyncSessionLocal() as session:
        # Check if already seeded
        if await check_already_seeded(session):
            logger.warning("⚠️  Database already seeded. Skipping...")
            return
        
        try:
            # Seed core data
            users = await seed_users(session)
            wards = await seed_wards(session)
            
            # Get patient count from environment
            patient_count = int(os.getenv("SEED_COUNT", "75"))
            
            # Try to load from CSV
            csv_path = Path(__file__).parent.parent / "data" / "datasets" / "diabetic_data.csv"
            patients = await seed_patients(session, wards, [u for u in users if u.role == "doctor"], str(csv_path), patient_count)
            
            # Seed encounters and related data
            encounters = await seed_encounters(session, patients, [u for u in users if u.role == "doctor"])
            diag_count = await seed_diagnoses(session, encounters)
            med_count = await seed_medications(session, encounters, [u for u in users if u.role == "doctor"])
            
            # Seed ML model version and predictions
            model_version = await seed_model_version(session)
            pred_count = await seed_risk_predictions(session, encounters, model_version)
            
            # Commit all changes
            await session.commit()
            
            # Print summary
            logger.info("=" * 60)
            logger.info("✅ Database Seeding Completed Successfully!")
            logger.info("=" * 60)
            logger.info(f"Users: {len(users)}")
            logger.info(f"  - 1 Admin")
            logger.info(f"  - 2 Doctors")
            logger.info(f"  - 3 Nurses")
            logger.info(f"  - 1 Social Worker")
            logger.info(f"Wards: {len(wards)} (Medical, Surgical, ICU)")
            logger.info(f"Patients: {len(patients)}")
            logger.info(f"Encounters: {len(encounters)}")
            logger.info(f"Diagnoses: {diag_count}")
            logger.info(f"Medications: {med_count}")
            logger.info(f"Risk Predictions: {pred_count}")
            logger.info("=" * 60)
            logger.info("Sample Login Credentials:")
            logger.info("  Admin:     admin@readmitcare.org / Admin@12345")
            logger.info("  Doctor:    dr.smith@readmitcare.org / Doctor@12345")
            logger.info("  Nurse:     nurse.williams@readmitcare.org / Nurse@12345")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"❌ Error during seeding: {e}", exc_info=True)
            await session.rollback()
            raise
        finally:
            await session.close()


def main():
    """Entry point."""
    try:
        asyncio.run(seed_database())
    except Exception as e:
        logger.error(f"❌ Seeding failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
