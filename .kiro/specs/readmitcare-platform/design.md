# Technical Design Document: ReadmitCare Platform

## 1. Introduction

ReadmitCare is a comprehensive hospital discharge-planning platform that integrates machine learning-based risk prediction, care coordination, and patient engagement to reduce hospital readmission rates. This document provides the detailed technical architecture, database schema, API specifications, ML pipeline design, frontend structure, and infrastructure requirements.

### 1.1 Architecture Overview

The system follows a modern three-tier architecture:

- **Frontend**: React 18 + TypeScript + Vite single-page application
- **Backend**: FastAPI (Python 3.11) RESTful API with async support
- **Database**: PostgreSQL 13+ (with SQLite fallback for development)
- **ML Service**: XGBoost-based risk prediction with SHAP explainability
- **Infrastructure**: Docker Compose for local development, Kubernetes-ready for production

```mermaid
graph TB
    subgraph "Frontend Layer"
        A[React 18 SPA<br/>TypeScript + Vite]
    end
    
    subgraph "Backend Layer"
        B[FastAPI API<br/>Python 3.11]
        C[APScheduler<br/>Background Jobs]
        D[ML Pipeline<br/>XGBoost + SHAP]
    end
    
    subgraph "Data Layer"
        E[(PostgreSQL<br/>Primary DB)]
        F[(SQLite<br/>Dev/Test)]
    end
    
    subgraph "External Systems"
        G[FHIR R4 API]
        H[HL7 v2.x]
    end
    
    A -->|REST API<br/>JWT Auth| B
    B --> E
    B --> F
    B --> D
    C --> B
    C --> E
    G --> B
    H --> B
    B -->|Webhook| G
    
    style A fill:#0F2A43,color:#fff
    style B fill:#0E9F8E,color:#fff
    style D fill:#E4572E,color:#fff
    style E fill:#0F2A43,color:#fff
```

### 1.2 Technology Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|----------|
| Frontend | React | 18.x | UI framework |
| Frontend | TypeScript | 5.x | Type safety |
| Frontend | Vite | 5.x | Build tool |
| Frontend | TanStack Query | 5.x | Server state management |
| Frontend | Tailwind CSS | 3.x | Styling |
| Frontend | Recharts | 2.x | Data visualization |
| Frontend | dnd-kit | 6.x | Drag-and-drop (Kanban) |
| Backend | Python | 3.11 | Runtime |
| Backend | FastAPI | 0.115.x | Web framework |
| Backend | SQLAlchemy | 2.x | ORM |
| Backend | Pydantic | 2.x | Validation |
| Backend | Alembic | 1.x | Migrations |
| Backend | APScheduler | 3.x | Background jobs |
| Backend | PyJWT | 2.x | JWT handling |
| Backend | bcrypt | 4.x | Password hashing |
| ML | XGBoost | 2.x | Primary model |
| ML | scikit-learn | 1.x | Baseline & preprocessing |
| ML | SHAP | 0.45.x | Explainability |
| Database | PostgreSQL | 13+ | Primary database |
| Database | SQLite | 3.x | Dev/test database |
| Infrastructure | Docker | 24+ | Containerization |
| Infrastructure | Docker Compose | 2.x | Orchestration |

## 2. Database Design

### 2.1 Entity-Relationship Diagram

```mermaid
erDiagram
    users ||--o{ patients : manages
    users ||--o{ encounters : records
    users ||--o{ interventions : creates
    users ||--o{ follow_up_contacts : performs
    users ||--o{ notifications : receives
    users ||--o{ audit_logs : generates
    users }o--|| wards : "assigned_to"
    
    wards ||--o{ patients : "admitted_to"
    
    patients ||--o{ encounters : has
    patients ||--o{ diagnoses : has
    patients ||--o{ medications : prescribed
    patients ||--o{ lab_results : has
    patients ||--o{ social_screenings : completes
    patients ||--o{ risk_predictions : receives
    patients ||--o{ interventions : receives
    patients ||--o{ follow_up_contacts : receives
    patients ||--o{ outcomes : has
    patients ||--o{ notifications : receives
    
    encounters ||--o{ diagnoses : contains
    encounters ||--o{ medications : includes
    encounters ||--o{ lab_results : includes
    encounters ||--o{ risk_predictions : generates
    
    risk_predictions }o--|| model_versions : "generated_by"
    
    model_versions ||--o{ risk_predictions : generates
    
    users {
        uuid id PK
        string email UK
        string password_hash
        string first_name
        string last_name
        enum role
        uuid ward_id FK
        boolean is_active
        timestamp last_login
        timestamp created_at
        timestamp updated_at
    }

    wards {
        uuid id PK
        string name
        string location
        int capacity
        timestamp created_at
        timestamp updated_at
    }
    
    patients {
        uuid id PK
        string mrn UK
        string first_name
        string last_name
        date date_of_birth
        enum gender
        string phone
        string email
        text address
        uuid current_ward_id FK
        uuid primary_provider_id FK
        timestamp created_at
        timestamp updated_at
    }
    
    encounters {
        uuid id PK
        uuid patient_id FK
        enum encounter_type
        timestamp admission_date
        timestamp discharge_date
        uuid admitting_provider_id FK
        uuid discharging_provider_id FK
        string discharge_disposition
        timestamp created_at
        timestamp updated_at
    }
    
    diagnoses {
        uuid id PK
        uuid patient_id FK
        uuid encounter_id FK
        string icd10_code
        string description
        boolean is_primary
        timestamp diagnosed_at
        timestamp created_at
    }
    
    medications {
        uuid id PK
        uuid patient_id FK
        uuid encounter_id FK
        string name
        string dosage
        string frequency
        string route
        timestamp start_date
        timestamp end_date
        uuid prescribing_provider_id FK
        timestamp created_at
        timestamp updated_at
    }
    
    lab_results {
        uuid id PK
        uuid patient_id FK
        uuid encounter_id FK
        string test_name
        string test_code
        string result_value
        string unit
        string reference_range
        string flag
        timestamp result_date
        timestamp created_at
    }
    
    social_screenings {
        uuid id PK
        uuid patient_id FK
        uuid encounter_id FK
        int housing_stability_score
        int food_security_score
        int transportation_access_score
        int social_support_score
        text notes
        uuid screened_by_id FK
        timestamp screened_at
        timestamp created_at
    }

    risk_predictions {
        uuid id PK
        uuid patient_id FK
        uuid encounter_id FK
        float risk_score
        float confidence_lower
        float confidence_upper
        string risk_band
        jsonb feature_contributions
        uuid model_version_id FK
        timestamp predicted_at
        timestamp created_at
    }
    
    interventions {
        uuid id PK
        uuid patient_id FK
        uuid encounter_id FK
        string intervention_type
        string description
        enum status
        uuid assigned_to_id FK
        timestamp due_date
        timestamp completed_at
        text outcome_notes
        timestamp created_at
        timestamp updated_at
    }
    
    follow_up_contacts {
        uuid id PK
        uuid patient_id FK
        uuid encounter_id FK
        enum contact_method
        enum contact_outcome
        text notes
        uuid contacted_by_id FK
        timestamp contact_date
        timestamp next_contact_date
        timestamp created_at
    }
    
    outcomes {
        uuid id PK
        uuid patient_id FK
        uuid encounter_id FK
        boolean readmitted
        timestamp readmission_date
        uuid readmission_encounter_id FK
        int days_to_readmission
        string readmission_reason
        timestamp outcome_date
        timestamp created_at
    }
    
    model_versions {
        uuid id PK
        string version_name UK
        string model_type
        jsonb hyperparameters
        jsonb metrics
        timestamp trained_at
        boolean is_active
        timestamp created_at
    }
    
    notifications {
        uuid id PK
        uuid user_id FK
        uuid patient_id FK
        string notification_type
        string title
        text message
        enum priority
        boolean is_read
        timestamp read_at
        jsonb metadata
        timestamp created_at
    }
    
    audit_logs {
        uuid id PK
        uuid user_id FK
        string action
        string resource_type
        uuid resource_id
        jsonb changes
        string ip_address
        string user_agent
        timestamp created_at
    }
```

### 2.2 Detailed Table Specifications

#### 2.2.1 users Table

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('nurse', 'doctor', 'social_worker', 'admin')),
    ward_id UUID REFERENCES wards(id) ON DELETE SET NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_ward_id ON users(ward_id);
```


#### 2.2.2 wards Table

```sql
CREATE TABLE wards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    location VARCHAR(200),
    capacity INTEGER NOT NULL CHECK (capacity > 0),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX idx_wards_name ON wards(name);
```

#### 2.2.3 patients Table

```sql
CREATE TABLE patients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mrn VARCHAR(50) NOT NULL UNIQUE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE NOT NULL,
    gender VARCHAR(20) CHECK (gender IN ('male', 'female', 'other', 'unknown')),
    phone VARCHAR(20),
    email VARCHAR(255),
    address TEXT,
    current_ward_id UUID REFERENCES wards(id) ON DELETE SET NULL,
    primary_provider_id UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_dob_past CHECK (date_of_birth < CURRENT_DATE)
);

CREATE INDEX idx_patients_mrn ON patients(mrn);
CREATE INDEX idx_patients_current_ward_id ON patients(current_ward_id);
CREATE INDEX idx_patients_primary_provider_id ON patients(primary_provider_id);
CREATE INDEX idx_patients_last_name ON patients(last_name);
```

#### 2.2.4 encounters Table

```sql
CREATE TABLE encounters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    encounter_type VARCHAR(50) NOT NULL CHECK (encounter_type IN ('inpatient', 'outpatient', 'emergency', 'observation')),
    admission_date TIMESTAMP WITH TIME ZONE NOT NULL,
    discharge_date TIMESTAMP WITH TIME ZONE,
    admitting_provider_id UUID REFERENCES users(id) ON DELETE SET NULL,
    discharging_provider_id UUID REFERENCES users(id) ON DELETE SET NULL,
    discharge_disposition VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_discharge_after_admission CHECK (discharge_date IS NULL OR discharge_date >= admission_date)
);

CREATE INDEX idx_encounters_patient_id ON encounters(patient_id);
CREATE INDEX idx_encounters_admission_date ON encounters(admission_date);
CREATE INDEX idx_encounters_discharge_date ON encounters(discharge_date);
CREATE INDEX idx_encounters_encounter_type ON encounters(encounter_type);
```

#### 2.2.5 diagnoses Table

```sql
CREATE TABLE diagnoses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    encounter_id UUID REFERENCES encounters(id) ON DELETE CASCADE,
    icd10_code VARCHAR(10) NOT NULL,
    description TEXT NOT NULL,
    is_primary BOOLEAN NOT NULL DEFAULT false,
    diagnosed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_diagnoses_patient_id ON diagnoses(patient_id);
CREATE INDEX idx_diagnoses_encounter_id ON diagnoses(encounter_id);
CREATE INDEX idx_diagnoses_icd10_code ON diagnoses(icd10_code);
CREATE INDEX idx_diagnoses_is_primary ON diagnoses(is_primary);
```


#### 2.2.6 medications Table

```sql
CREATE TABLE medications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    encounter_id UUID REFERENCES encounters(id) ON DELETE SET NULL,
    name VARCHAR(200) NOT NULL,
    dosage VARCHAR(100) NOT NULL,
    frequency VARCHAR(100) NOT NULL,
    route VARCHAR(50) CHECK (route IN ('oral', 'IV', 'topical', 'injection', 'inhalation', 'other')),
    start_date TIMESTAMP WITH TIME ZONE NOT NULL,
    end_date TIMESTAMP WITH TIME ZONE,
    prescribing_provider_id UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_end_after_start CHECK (end_date IS NULL OR end_date >= start_date)
);

CREATE INDEX idx_medications_patient_id ON medications(patient_id);
CREATE INDEX idx_medications_encounter_id ON medications(encounter_id);
CREATE INDEX idx_medications_start_date ON medications(start_date);
CREATE INDEX idx_medications_end_date ON medications(end_date);
```

#### 2.2.7 lab_results Table

```sql
CREATE TABLE lab_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    encounter_id UUID REFERENCES encounters(id) ON DELETE SET NULL,
    test_name VARCHAR(200) NOT NULL,
    test_code VARCHAR(50),
    result_value VARCHAR(100) NOT NULL,
    unit VARCHAR(50),
    reference_range VARCHAR(100),
    flag VARCHAR(20) CHECK (flag IN ('normal', 'high', 'low', 'critical', NULL)),
    result_date TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_lab_results_patient_id ON lab_results(patient_id);
CREATE INDEX idx_lab_results_encounter_id ON lab_results(encounter_id);
CREATE INDEX idx_lab_results_test_code ON lab_results(test_code);
CREATE INDEX idx_lab_results_result_date ON lab_results(result_date);
CREATE INDEX idx_lab_results_flag ON lab_results(flag);
```

#### 2.2.8 social_screenings Table

```sql
CREATE TABLE social_screenings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    encounter_id UUID REFERENCES encounters(id) ON DELETE SET NULL,
    housing_stability_score INTEGER CHECK (housing_stability_score BETWEEN 1 AND 5),
    food_security_score INTEGER CHECK (food_security_score BETWEEN 1 AND 5),
    transportation_access_score INTEGER CHECK (transportation_access_score BETWEEN 1 AND 5),
    social_support_score INTEGER CHECK (social_support_score BETWEEN 1 AND 5),
    notes TEXT,
    screened_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
    screened_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_social_screenings_patient_id ON social_screenings(patient_id);
CREATE INDEX idx_social_screenings_encounter_id ON social_screenings(encounter_id);
CREATE INDEX idx_social_screenings_screened_at ON social_screenings(screened_at);
```

#### 2.2.9 risk_predictions Table

```sql
CREATE TABLE risk_predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    encounter_id UUID NOT NULL REFERENCES encounters(id) ON DELETE CASCADE,
    risk_score DECIMAL(5,2) NOT NULL CHECK (risk_score BETWEEN 0 AND 100),
    confidence_lower DECIMAL(5,2) CHECK (confidence_lower BETWEEN 0 AND 100),
    confidence_upper DECIMAL(5,2) CHECK (confidence_upper BETWEEN 0 AND 100),
    risk_band VARCHAR(20) NOT NULL CHECK (risk_band IN ('low', 'medium', 'high')),
    feature_contributions JSONB,
    model_version_id UUID NOT NULL REFERENCES model_versions(id) ON DELETE RESTRICT,
    predicted_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_risk_predictions_patient_id ON risk_predictions(patient_id);
CREATE INDEX idx_risk_predictions_encounter_id ON risk_predictions(encounter_id);
CREATE INDEX idx_risk_predictions_risk_score ON risk_predictions(risk_score DESC);
CREATE INDEX idx_risk_predictions_risk_band ON risk_predictions(risk_band);
CREATE INDEX idx_risk_predictions_predicted_at ON risk_predictions(predicted_at DESC);
CREATE INDEX idx_risk_predictions_model_version_id ON risk_predictions(model_version_id);
```


#### 2.2.10 interventions Table

```sql
CREATE TABLE interventions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    encounter_id UUID REFERENCES encounters(id) ON DELETE SET NULL,
    intervention_type VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    status VARCHAR(50) NOT NULL CHECK (status IN ('pending', 'in_progress', 'completed', 'cancelled')),
    assigned_to_id UUID REFERENCES users(id) ON DELETE SET NULL,
    due_date TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    outcome_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_interventions_patient_id ON interventions(patient_id);
CREATE INDEX idx_interventions_encounter_id ON interventions(encounter_id);
CREATE INDEX idx_interventions_status ON interventions(status);
CREATE INDEX idx_interventions_assigned_to_id ON interventions(assigned_to_id);
CREATE INDEX idx_interventions_due_date ON interventions(due_date);
```

#### 2.2.11 follow_up_contacts Table

```sql
CREATE TABLE follow_up_contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    encounter_id UUID REFERENCES encounters(id) ON DELETE SET NULL,
    contact_method VARCHAR(50) NOT NULL CHECK (contact_method IN ('phone', 'email', 'sms', 'in_person', 'video')),
    contact_outcome VARCHAR(100) NOT NULL CHECK (contact_outcome IN ('successful', 'no_answer', 'left_message', 'wrong_number', 'refused')),
    notes TEXT,
    contacted_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
    contact_date TIMESTAMP WITH TIME ZONE NOT NULL,
    next_contact_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_follow_up_contacts_patient_id ON follow_up_contacts(patient_id);
CREATE INDEX idx_follow_up_contacts_encounter_id ON follow_up_contacts(encounter_id);
CREATE INDEX idx_follow_up_contacts_contact_date ON follow_up_contacts(contact_date DESC);
CREATE INDEX idx_follow_up_contacts_next_contact_date ON follow_up_contacts(next_contact_date);
```

#### 2.2.12 outcomes Table

```sql
CREATE TABLE outcomes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    encounter_id UUID NOT NULL REFERENCES encounters(id) ON DELETE CASCADE,
    readmitted BOOLEAN NOT NULL,
    readmission_date TIMESTAMP WITH TIME ZONE,
    readmission_encounter_id UUID REFERENCES encounters(id) ON DELETE SET NULL,
    days_to_readmission INTEGER,
    readmission_reason TEXT,
    outcome_date TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_readmission_consistency CHECK (
        (readmitted = false AND readmission_date IS NULL AND days_to_readmission IS NULL) OR
        (readmitted = true AND readmission_date IS NOT NULL AND days_to_readmission IS NOT NULL)
    )
);

CREATE INDEX idx_outcomes_patient_id ON outcomes(patient_id);
CREATE INDEX idx_outcomes_encounter_id ON outcomes(encounter_id);
CREATE INDEX idx_outcomes_readmitted ON outcomes(readmitted);
CREATE INDEX idx_outcomes_outcome_date ON outcomes(outcome_date DESC);
CREATE UNIQUE INDEX idx_outcomes_encounter_unique ON outcomes(encounter_id);
```

#### 2.2.13 model_versions Table

```sql
CREATE TABLE model_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version_name VARCHAR(50) NOT NULL UNIQUE,
    model_type VARCHAR(50) NOT NULL,
    hyperparameters JSONB,
    metrics JSONB,
    trained_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_model_versions_is_active ON model_versions(is_active);
CREATE INDEX idx_model_versions_trained_at ON model_versions(trained_at DESC);
```


#### 2.2.14 notifications Table

```sql
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    patient_id UUID REFERENCES patients(id) ON DELETE CASCADE,
    notification_type VARCHAR(100) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    priority VARCHAR(20) NOT NULL CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    is_read BOOLEAN NOT NULL DEFAULT false,
    read_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_patient_id ON notifications(patient_id);
CREATE INDEX idx_notifications_is_read ON notifications(is_read);
CREATE INDEX idx_notifications_created_at ON notifications(created_at DESC);
CREATE INDEX idx_notifications_priority ON notifications(priority);
```

#### 2.2.15 audit_logs Table

```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id UUID,
    changes JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_resource_type ON audit_logs(resource_type);
CREATE INDEX idx_audit_logs_resource_id ON audit_logs(resource_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at DESC);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
```

### 2.3 Database Connection Strategy

The application supports both PostgreSQL (production) and SQLite (development/testing) through a configurable DATABASE_URL environment variable:

```python
# PostgreSQL (Production)
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/readmitcare

# SQLite (Development)
DATABASE_URL=sqlite+aiosqlite:///./readmitcare.db
```

SQLAlchemy 2.x async engine configuration:

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

engine = create_async_engine(
    DATABASE_URL,
    echo=True if DEBUG else False,
    pool_pre_ping=True,  # Verify connections before use
    pool_size=20,        # PostgreSQL only
    max_overflow=10      # PostgreSQL only
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)
```

## 3. Backend Architecture

### 3.1 Project Structure

```
backend/
├── alembic/                    # Database migrations
│   ├── versions/
│   └── env.py
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Configuration management
│   ├── database.py             # Database connection
│   ├── dependencies.py         # Dependency injection
│   ├── api/
│   │   ├── __init__.py
│   │   ├── auth.py             # POST /api/auth/login, /register, /refresh
│   │   ├── dashboard.py        # GET /api/dashboard/stats, /metrics
│   │   ├── patients.py         # CRUD /api/patients/*
│   │   ├── encounters.py       # CRUD /api/encounters/*
│   │   ├── intake.py           # POST /api/intake/admission, /discharge
│   │   ├── prediction.py       # POST /api/prediction/generate, GET /score/:patient_id
│   │   ├── interventions.py    # CRUD /api/interventions/*
│   │   ├── outcomes.py         # CRUD /api/outcomes/*
│   │   ├── monitoring.py       # GET /api/monitoring/calibration, /drift
│   │   ├── fairness.py         # GET /api/fairness/metrics
│   │   ├── model.py            # GET /api/model/versions, POST /activate
│   │   ├── careplan.py         # GET /api/careplan/:encounter_id
│   │   ├── notifications.py    # GET /api/notifications, PUT /mark-read
│   │   └── audit.py            # GET /api/audit/logs
│   ├── models/                 # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── ward.py
│   │   ├── patient.py
│   │   ├── encounter.py
│   │   ├── diagnosis.py
│   │   ├── medication.py
│   │   ├── lab_result.py
│   │   ├── social_screening.py
│   │   ├── risk_prediction.py
│   │   ├── intervention.py
│   │   ├── follow_up_contact.py
│   │   ├── outcome.py
│   │   ├── model_version.py
│   │   ├── notification.py
│   │   └── audit_log.py
│   ├── schemas/                # Pydantic models for validation
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── patient.py
│   │   ├── encounter.py
│   │   ├── risk_prediction.py
│   │   └── ...
│   ├── services/               # Business logic layer
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── patient_service.py
│   │   ├── risk_service.py
│   │   ├── notification_service.py
│   │   └── audit_service.py
│   ├── ml/                     # ML pipeline
│   │   ├── __init__.py
│   │   ├── predictor.py        # Main prediction interface
│   │   ├── model_loader.py     # Load trained models
│   │   ├── feature_engineer.py # Feature extraction
│   │   ├── explainer.py        # SHAP explanations
│   │   └── monitor.py          # Model monitoring
│   ├── jobs/                   # Background jobs
│   │   ├── __init__.py
│   │   ├── scheduler.py        # APScheduler setup
│   │   ├── rescore_job.py      # Nightly re-scoring
│   │   └── overdue_check_job.py # Hourly overdue checks
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── security.py         # Password hashing, JWT
│   │   ├── fhir_parser.py      # FHIR R4 parsing
│   │   └── csv_importer.py     # Bulk CSV upload
│   └── middleware/
│       ├── __init__.py
│       ├── auth_middleware.py
│       ├── audit_middleware.py
│       └── error_handler.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_patients.py
│   ├── test_risk_prediction.py
│   └── ...
├── data/
│   ├── models/                 # Trained ML models
│   │   ├── xgboost_ensemble/
│   │   └── baseline_logistic.pkl
│   └── datasets/               # Training/seed data
├── requirements.txt
├── pyproject.toml
├── Dockerfile
└── README.md
```


### 3.2 API Endpoint Specifications

#### 3.2.1 Authentication Endpoints

**POST /api/auth/register**
- **Description**: Register a new user
- **Request Body**: `{ email, password, first_name, last_name, role, ward_id }`
- **Response**: `{ id, email, first_name, last_name, role, access_token }`
- **Status Codes**: 201 (Created), 400 (Validation Error), 409 (Email Exists)

**POST /api/auth/login**
- **Description**: Authenticate user and receive JWT token
- **Request Body**: `{ email, password }`
- **Response**: `{ access_token, refresh_token, user: { id, email, first_name, last_name, role } }`
- **Status Codes**: 200 (OK), 401 (Invalid Credentials), 429 (Rate Limited)

**POST /api/auth/refresh**
- **Description**: Refresh expired JWT token
- **Request Body**: `{ refresh_token }`
- **Response**: `{ access_token, refresh_token }`
- **Status Codes**: 200 (OK), 401 (Invalid Token)

#### 3.2.2 Dashboard Endpoints

**GET /api/dashboard/stats**
- **Description**: Get summary statistics for dashboard
- **Query Params**: `ward_id` (optional, filter by ward)
- **Response**: 
  ```json
  {
    "total_patients": 150,
    "active_encounters": 45,
    "high_risk_count": 12,
    "overdue_interventions": 8,
    "readmission_rate_30d": 0.145
  }
  ```
- **Auth**: Required (any role)
- **Status Codes**: 200 (OK)

**GET /api/dashboard/metrics**
- **Description**: Time-series metrics for charts
- **Query Params**: `start_date`, `end_date`, `metric` (admissions|discharges|risk_scores)
- **Response**: `{ data: [{ date, value }] }`
- **Status Codes**: 200 (OK)

#### 3.2.3 Patient Endpoints

**GET /api/patients**
- **Description**: List patients with pagination and filtering
- **Query Params**: `page=1`, `limit=20`, `search`, `ward_id`, `risk_band` (low|medium|high)
- **Response**: 
  ```json
  {
    "items": [
      {
        "id": "uuid",
        "mrn": "MRN123456",
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": "1965-03-15",
        "gender": "male",
        "current_ward": { "id": "uuid", "name": "Ward A" },
        "current_risk_score": 68.5,
        "current_risk_band": "medium"
      }
    ],
    "total": 150,
    "page": 1,
    "limit": 20
  }
  ```
- **Status Codes**: 200 (OK)

**POST /api/patients**
- **Description**: Create new patient
- **Request Body**: `{ mrn, first_name, last_name, date_of_birth, gender, phone, email, address, current_ward_id, primary_provider_id }`
- **Response**: Created patient object
- **Status Codes**: 201 (Created), 400 (Validation Error), 409 (MRN Exists)

**GET /api/patients/:id**
- **Description**: Get patient details with recent encounters, risk predictions
- **Response**: 
  ```json
  {
    "id": "uuid",
    "mrn": "MRN123456",
    "first_name": "John",
    "last_name": "Doe",
    "...": "...",
    "current_encounter": { "id": "uuid", "admission_date": "2024-01-15T08:00:00Z", "..." },
    "recent_predictions": [
      {
        "id": "uuid",
        "risk_score": 68.5,
        "risk_band": "medium",
        "predicted_at": "2024-01-15T10:00:00Z",
        "feature_contributions": [
          { "feature": "age", "contribution": 12.3, "direction": "increase" }
        ]
      }
    ],
    "active_interventions": []
  }
  ```
- **Status Codes**: 200 (OK), 404 (Not Found)

**PUT /api/patients/:id**
- **Description**: Update patient information
- **Request Body**: Partial patient object
- **Response**: Updated patient object
- **Status Codes**: 200 (OK), 400 (Validation Error), 404 (Not Found)

#### 3.2.4 Encounter Endpoints

**POST /api/encounters**
- **Description**: Create new encounter (admission)
- **Request Body**: `{ patient_id, encounter_type, admission_date, admitting_provider_id }`
- **Response**: Created encounter object
- **Status Codes**: 201 (Created), 400 (Validation Error)

**PUT /api/encounters/:id/discharge**
- **Description**: Record patient discharge
- **Request Body**: `{ discharge_date, discharging_provider_id, discharge_disposition }`
- **Response**: Updated encounter with auto-generated risk prediction
- **Status Codes**: 200 (OK), 400 (Validation Error), 404 (Not Found)

**GET /api/encounters/:id**
- **Description**: Get encounter details with diagnoses, medications, labs
- **Response**: Complete encounter object with related data
- **Status Codes**: 200 (OK), 404 (Not Found)

#### 3.2.5 Intake Endpoints

**POST /api/intake/admission**
- **Description**: Process complete patient admission with diagnoses, medications
- **Request Body**:
  ```json
  {
    "patient": { "mrn": "MRN123", "..." },
    "encounter": { "encounter_type": "inpatient", "admission_date": "...", "..." },
    "diagnoses": [
      { "icd10_code": "I50.9", "description": "Heart failure", "is_primary": true }
    ],
    "medications": [
      { "name": "Lisinopril", "dosage": "10mg", "frequency": "daily", "..." }
    ],
    "lab_results": [],
    "social_screening": { "housing_stability_score": 4, "..." }
  }
  ```
- **Response**: Created patient and encounter with IDs
- **Status Codes**: 201 (Created), 400 (Validation Error)

**POST /api/intake/discharge**
- **Description**: Process complete patient discharge with outcome recording
- **Request Body**: `{ encounter_id, discharge_date, discharge_disposition, ... }`
- **Response**: Updated encounter with risk prediction
- **Status Codes**: 200 (OK), 400 (Validation Error), 404 (Not Found)

**POST /api/intake/fhir-bundle**
- **Description**: Ingest FHIR R4 bundle (Patient, Encounter, Condition, MedicationRequest resources)
- **Request Body**: FHIR R4 Bundle JSON
- **Response**: `{ patient_id, encounter_id, created_resources_count }`
- **Status Codes**: 201 (Created), 400 (Invalid FHIR)

**POST /api/intake/csv-bulk**
- **Description**: Bulk upload patients from CSV
- **Request**: Multipart form with CSV file
- **Response**: `{ created_count, failed_count, errors: [] }`
- **Status Codes**: 200 (OK), 400 (Invalid CSV)


#### 3.2.6 Prediction Endpoints

**POST /api/prediction/generate**
- **Description**: Generate risk prediction for encounter
- **Request Body**: `{ encounter_id }`
- **Response**:
  ```json
  {
    "prediction_id": "uuid",
    "encounter_id": "uuid",
    "risk_score": 68.5,
    "risk_band": "medium",
    "confidence_lower": 55.2,
    "confidence_upper": 81.8,
    "feature_contributions": [
      { "feature": "age", "value": 75, "contribution": 12.3, "direction": "increase" },
      { "feature": "prior_admissions_30d", "value": 2, "contribution": 8.7, "direction": "increase" },
      { "feature": "num_diagnoses", "value": 5, "contribution": 6.1, "direction": "increase" }
    ],
    "model_version": "v2.1.0"
  }
  ```
- **Status Codes**: 200 (OK), 404 (Encounter Not Found), 500 (Model Error)

**GET /api/prediction/score/:patient_id**
- **Description**: Get latest risk score for patient
- **Response**: Latest prediction object
- **Status Codes**: 200 (OK), 404 (No Predictions)

**POST /api/prediction/what-if**
- **Description**: Simulate risk score under different scenarios
- **Request Body**: `{ encounter_id, modifications: { num_diagnoses: 3, has_social_support: true } }`
- **Response**: `{ original_score, modified_score, delta }`
- **Status Codes**: 200 (OK)

#### 3.2.7 Intervention Endpoints

**GET /api/interventions**
- **Description**: List interventions with filtering
- **Query Params**: `patient_id`, `status`, `assigned_to_id`, `due_date_from`, `due_date_to`
- **Response**: Paginated list of interventions
- **Status Codes**: 200 (OK)

**POST /api/interventions**
- **Description**: Create new intervention
- **Request Body**: `{ patient_id, encounter_id, intervention_type, description, assigned_to_id, due_date }`
- **Response**: Created intervention
- **Status Codes**: 201 (Created), 400 (Validation Error)

**PUT /api/interventions/:id/complete**
- **Description**: Mark intervention as completed
- **Request Body**: `{ outcome_notes }`
- **Response**: Updated intervention
- **Status Codes**: 200 (OK), 404 (Not Found)

#### 3.2.8 Outcomes Endpoints

**POST /api/outcomes**
- **Description**: Record readmission outcome
- **Request Body**: `{ encounter_id, readmitted, readmission_date?, readmission_encounter_id?, readmission_reason? }`
- **Response**: Created outcome record
- **Status Codes**: 201 (Created), 400 (Validation Error)

**GET /api/outcomes/encounter/:encounter_id**
- **Description**: Get outcome for specific encounter
- **Response**: Outcome object or null
- **Status Codes**: 200 (OK)

#### 3.2.9 Monitoring Endpoints

**GET /api/monitoring/calibration**
- **Description**: Get model calibration metrics by risk band
- **Query Params**: `start_date`, `end_date`
- **Response**:
  ```json
  {
    "calibration_by_band": [
      { "risk_band": "low", "predicted_rate": 0.08, "actual_rate": 0.09, "count": 450 },
      { "risk_band": "medium", "predicted_rate": 0.22, "actual_rate": 0.21, "count": 280 },
      { "risk_band": "high", "predicted_rate": 0.42, "actual_rate": 0.45, "count": 120 }
    ],
    "overall_auroc": 0.78
  }
  ```
- **Status Codes**: 200 (OK)

**GET /api/monitoring/drift**
- **Description**: Get model drift metrics (PSI)
- **Query Params**: `feature`
- **Response**: `{ feature, psi_score, drift_detected, reference_distribution: [], current_distribution: [] }`
- **Status Codes**: 200 (OK)

**GET /api/monitoring/performance**
- **Description**: Rolling AUROC over time
- **Query Params**: `window_days=30`
- **Response**: `{ data: [{ date, auroc, n_predictions }] }`
- **Status Codes**: 200 (OK)

#### 3.2.10 Fairness Endpoints

**GET /api/fairness/metrics**
- **Description**: Fairness metrics across demographic groups
- **Query Params**: `start_date`, `end_date`
- **Response**:
  ```json
  {
    "by_gender": [
      { "group": "male", "avg_risk_score": 32.5, "high_risk_pct": 0.14, "readmission_rate": 0.15 },
      { "group": "female", "avg_risk_score": 31.2, "high_risk_pct": 0.13, "readmission_rate": 0.14 }
    ],
    "by_age_group": [],
    "by_race": [],
    "by_income_band": []
  }
  ```
- **Status Codes**: 200 (OK)

#### 3.2.11 Model Management Endpoints

**GET /api/model/versions**
- **Description**: List model versions with metrics
- **Response**:
  ```json
  {
    "versions": [
      {
        "id": "uuid",
        "version_name": "v2.1.0",
        "model_type": "xgboost_ensemble",
        "is_active": true,
        "metrics": { "auroc": 0.82, "precision": 0.71, "recall": 0.68 },
        "trained_at": "2024-01-10T00:00:00Z"
      }
    ]
  }
  ```
- **Status Codes**: 200 (OK)

**POST /api/model/activate**
- **Description**: Activate a specific model version
- **Request Body**: `{ version_id }`
- **Response**: `{ success: true, active_version: "v2.1.0" }`
- **Auth**: Admin only
- **Status Codes**: 200 (OK), 403 (Forbidden), 404 (Version Not Found)

#### 3.2.12 Care Plan Endpoints

**GET /api/careplan/:encounter_id**
- **Description**: Generate comprehensive care plan summary for encounter
- **Response**:
  ```json
  {
    "patient": { "..." },
    "encounter": { "..." },
    "risk_assessment": { "risk_score": 68.5, "key_factors": [] },
    "diagnoses": [],
    "medications": [],
    "interventions": [],
    "follow_up_plan": { "contacts": [], "next_contact_date": "2024-02-01" }
  }
  ```
- **Status Codes**: 200 (OK), 404 (Encounter Not Found)

#### 3.2.13 Notification Endpoints

**GET /api/notifications**
- **Description**: Get user's notifications
- **Query Params**: `is_read` (true|false), `priority`
- **Response**: Paginated notifications
- **Status Codes**: 200 (OK)

**PUT /api/notifications/:id/mark-read**
- **Description**: Mark notification as read
- **Response**: Updated notification
- **Status Codes**: 200 (OK), 404 (Not Found)

**GET /api/notifications/unread-count**
- **Description**: Get count of unread notifications
- **Response**: `{ count: 5 }`
- **Status Codes**: 200 (OK)

#### 3.2.14 Audit Endpoints

**GET /api/audit/logs**
- **Description**: Search audit logs
- **Query Params**: `user_id`, `action`, `resource_type`, `start_date`, `end_date`, `page`, `limit`
- **Response**: Paginated audit logs
- **Auth**: Admin only
- **Status Codes**: 200 (OK), 403 (Forbidden)


### 3.3 Authentication and Authorization

#### 3.3.1 JWT Token Structure

**Access Token** (8-hour expiration):
```json
{
  "sub": "user-uuid",
  "email": "john.doe@hospital.org",
  "role": "doctor",
  "ward_id": "ward-uuid",
  "exp": 1706112000,
  "iat": 1706083200
}
```

**Refresh Token** (7-day expiration):
```json
{
  "sub": "user-uuid",
  "type": "refresh",
  "exp": 1706688000
}
```

#### 3.3.2 Password Security

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash password using bcrypt with cost factor 12"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)
```

#### 3.3.3 Role-Based Access Control (RBAC)

| Resource | Nurse | Doctor | Social Worker | Admin |
|----------|-------|--------|---------------|-------|
| View Patients | ✓ (ward) | ✓ (ward) | ✓ (ward) | ✓ (all) |
| Create/Edit Patient | ✓ | ✓ | ✗ | ✓ |
| View Risk Predictions | ✓ | ✓ | ✓ | ✓ |
| Generate Predictions | ✗ | ✓ | ✗ | ✓ |
| Create Interventions | ✓ | ✓ | ✓ | ✓ |
| View Outcomes | ✓ | ✓ | ✓ | ✓ |
| Manage Users | ✗ | ✗ | ✗ | ✓ |
| View Audit Logs | ✗ | ✗ | ✗ | ✓ |
| Manage Models | ✗ | ✗ | ✗ | ✓ |

Permission enforcement in FastAPI:

```python
from fastapi import Depends, HTTPException, status
from app.dependencies import get_current_user

def require_role(allowed_roles: list[str]):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker

# Usage in endpoint
@router.post("/api/model/activate")
async def activate_model(
    version_id: UUID,
    current_user: User = Depends(require_role(["admin"]))
):
    pass
```

### 3.4 Background Jobs (APScheduler)

#### 3.4.1 Nightly Re-scoring Job

**Schedule**: Daily at 2:00 AM
**Purpose**: Re-calculate risk scores for active encounters with new model predictions

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

async def rescore_active_encounters():
    """Re-score all encounters discharged within last 30 days"""
    async with AsyncSessionLocal() as session:
        # Get encounters from last 30 days
        encounters = await session.execute(
            select(Encounter).where(
                Encounter.discharge_date >= datetime.utcnow() - timedelta(days=30),
                Encounter.discharge_date.isnot(None)
            )
        )
        
        for encounter in encounters.scalars():
            # Generate new prediction
            await prediction_service.generate_prediction(encounter.id)
            
        logger.info(f"Re-scored {len(encounters)} encounters")

scheduler = AsyncIOScheduler()
scheduler.add_job(
    rescore_active_encounters,
    CronTrigger(hour=2, minute=0),
    id="rescore_encounters",
    replace_existing=True
)
```

#### 3.4.2 Hourly Overdue Check Job

**Schedule**: Every hour
**Purpose**: Check for overdue interventions and create notifications

```python
async def check_overdue_interventions():
    """Find overdue interventions and notify assigned users"""
    async with AsyncSessionLocal() as session:
        # Get overdue interventions
        overdue = await session.execute(
            select(Intervention).where(
                Intervention.status.in_(["pending", "in_progress"]),
                Intervention.due_date < datetime.utcnow()
            )
        )
        
        for intervention in overdue.scalars():
            # Create notification
            await notification_service.create_notification(
                user_id=intervention.assigned_to_id,
                patient_id=intervention.patient_id,
                notification_type="overdue_intervention",
                title="Overdue Intervention",
                message=f"Intervention '{intervention.intervention_type}' is overdue",
                priority="high"
            )

scheduler.add_job(
    check_overdue_interventions,
    CronTrigger(hour="*", minute=0),  # Every hour
    id="check_overdue",
    replace_existing=True
)
```

### 3.5 Data Flow Diagram

```mermaid
sequenceDiagram
    participant F as Frontend
    participant A as API
    participant D as Database
    participant M as ML Service
    participant J as Background Jobs
    
    Note over F,J: Patient Discharge Flow
    
    F->>A: POST /api/encounters/{id}/discharge
    A->>D: Update encounter.discharge_date
    A->>M: Request risk prediction
    M->>M: Extract features
    M->>M: Load XGBoost ensemble
    M->>M: Generate 15 predictions
    M->>M: Calculate mean + CI
    M->>M: Run SHAP explainer
    M-->>A: Return risk_score, contributions
    A->>D: Insert risk_prediction record
    A->>D: Check if risk_score >= 60
    alt High Risk
        A->>D: Create high-risk notification
    end
    A-->>F: Return discharge data + risk
    
    Note over J: Nightly at 2 AM
    J->>D: Query encounters from last 30 days
    loop For each encounter
        J->>M: Request fresh prediction
        M-->>J: Return new risk_score
        J->>D: Insert new risk_prediction
    end
```

## 4. Machine Learning Pipeline

### 4.1 Model Architecture

**Primary Model**: XGBoost Gradient Boosting
**Baseline**: Logistic Regression
**Ensemble Strategy**: Bootstrap aggregation with 15 models for uncertainty quantification

#### 4.1.1 Feature Engineering

**Input Features** (total: ~35 features):

1. **Demographics** (4 features)
   - age (years)
   - gender (one-hot encoded)
   - race (one-hot encoded, optional)

2. **Clinical History** (10 features)
   - num_prior_admissions_30d
   - num_prior_admissions_90d
   - num_prior_admissions_365d
   - days_since_last_admission
   - num_diagnoses
   - num_chronic_conditions
   - num_medications
   - length_of_stay_days
   - has_primary_care_physician (boolean)
   - num_ed_visits_90d

3. **Diagnoses** (8 features, based on ICD-10 categories)
   - has_cardiovascular_disease
   - has_diabetes
   - has_respiratory_disease
   - has_renal_disease
   - has_mental_health_condition
   - has_cancer
   - has_infection
   - charlson_comorbidity_index

4. **Lab Results** (6 features)
   - has_abnormal_labs (boolean)
   - num_abnormal_labs
   - has_critical_labs (boolean)
   - creatinine_last (mg/dL, imputed median)
   - hemoglobin_last (g/dL, imputed median)
   - sodium_last (mEq/L, imputed median)

5. **Social Determinants** (4 features)
   - housing_stability_score (1-5)
   - food_security_score (1-5)
   - transportation_access_score (1-5)
   - social_support_score (1-5)

6. **Discharge Planning** (3 features)
   - discharge_to_home (vs facility, boolean)
   - has_follow_up_scheduled (boolean)
   - days_to_follow_up


**Feature Preprocessing**:

```python
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer

class FeatureEngineer:
    def __init__(self):
        self.numeric_imputer = SimpleImputer(strategy='median')
        self.scaler = StandardScaler()
        self.categorical_encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
        
    def extract_features(self, encounter: Encounter, patient: Patient, 
                        diagnoses: list[Diagnosis], medications: list[Medication],
                        lab_results: list[LabResult], social_screening: SocialScreening) -> pd.DataFrame:
        """Extract and engineer features from database records"""
        
        features = {}
        
        # Demographics
        features['age'] = (datetime.utcnow() - patient.date_of_birth).days / 365.25
        features['gender_male'] = int(patient.gender == 'male')
        features['gender_female'] = int(patient.gender == 'female')
        
        # Clinical history (requires queries for prior encounters)
        features['num_prior_admissions_30d'] = self._count_prior_admissions(patient.id, days=30)
        features['num_prior_admissions_90d'] = self._count_prior_admissions(patient.id, days=90)
        features['num_prior_admissions_365d'] = self._count_prior_admissions(patient.id, days=365)
        
        # Diagnoses
        features['num_diagnoses'] = len(diagnoses)
        features['has_cardiovascular_disease'] = self._has_icd10_category(diagnoses, 'I')
        features['has_diabetes'] = self._has_icd10_category(diagnoses, 'E11')
        features['charlson_comorbidity_index'] = self._calculate_charlson(diagnoses)
        
        # Medications
        features['num_medications'] = len(medications)
        
        # Length of stay
        if encounter.discharge_date:
            los = (encounter.discharge_date - encounter.admission_date).days
        else:
            los = (datetime.utcnow() - encounter.admission_date).days
        features['length_of_stay_days'] = los
        
        # Lab results
        features['has_abnormal_labs'] = any(lr.flag in ['high', 'low', 'critical'] for lr in lab_results)
        features['num_abnormal_labs'] = sum(1 for lr in lab_results if lr.flag in ['high', 'low', 'critical'])
        
        # Social determinants
        if social_screening:
            features['housing_stability_score'] = social_screening.housing_stability_score
            features['food_security_score'] = social_screening.food_security_score
            features['transportation_access_score'] = social_screening.transportation_access_score
            features['social_support_score'] = social_screening.social_support_score
        else:
            # Impute median if missing
            features['housing_stability_score'] = 3
            features['food_security_score'] = 3
            features['transportation_access_score'] = 3
            features['social_support_score'] = 3
        
        return pd.DataFrame([features])
```

#### 4.1.2 XGBoost Ensemble Configuration

```python
import xgboost as xgb

# Hyperparameters for each model in ensemble
XGBOOST_PARAMS = {
    'objective': 'binary:logistic',
    'eval_metric': 'auc',
    'max_depth': 6,
    'learning_rate': 0.05,
    'n_estimators': 200,
    'min_child_weight': 5,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'gamma': 0.1,
    'reg_alpha': 0.1,
    'reg_lambda': 1.0,
    'random_state': 42,
    'scale_pos_weight': 3  # Handle class imbalance
}

class EnsemblePredictor:
    def __init__(self, n_models=15):
        self.n_models = n_models
        self.models = []
        self.load_models()
        
    def load_models(self):
        """Load pre-trained models from disk"""
        for i in range(self.n_models):
            model_path = f"data/models/xgboost_ensemble/model_{i}.json"
            model = xgb.XGBClassifier()
            model.load_model(model_path)
            self.models.append(model)
    
    def predict_proba(self, X: pd.DataFrame) -> tuple[float, float, float]:
        """
        Predict with uncertainty quantification
        Returns: (mean_probability, lower_CI, upper_CI)
        """
        predictions = np.array([model.predict_proba(X)[:, 1] for model in self.models])
        
        mean_prob = np.mean(predictions, axis=0)[0]
        lower_ci = np.percentile(predictions, 2.5, axis=0)[0]
        upper_ci = np.percentile(predictions, 97.5, axis=0)[0]
        
        return mean_prob * 100, lower_ci * 100, upper_ci * 100
```

#### 4.1.3 Risk Band Thresholds

```python
def assign_risk_band(risk_score: float) -> str:
    """
    Assign risk band based on score percentiles:
    - High: top 15% (risk_score >= 60)
    - Medium: next 25% (40 <= risk_score < 60)
    - Low: bottom 60% (risk_score < 40)
    """
    if risk_score >= 60:
        return "high"
    elif risk_score >= 40:
        return "medium"
    else:
        return "low"
```

### 4.2 SHAP Explainability

```python
import shap

class SHAPExplainer:
    def __init__(self, model: xgb.XGBClassifier, X_background: pd.DataFrame):
        """Initialize SHAP explainer with background dataset for TreeExplainer"""
        self.explainer = shap.TreeExplainer(model, X_background)
        self.feature_names = X_background.columns.tolist()
    
    def explain_prediction(self, X: pd.DataFrame, top_k=8) -> list[dict]:
        """
        Generate SHAP explanation for single prediction
        Returns top_k feature contributions
        """
        shap_values = self.explainer.shap_values(X)
        
        # Get base value (average prediction)
        base_value = self.explainer.expected_value
        
        # Create contribution list
        contributions = []
        for feature_name, shap_value, feature_value in zip(
            self.feature_names, shap_values[0], X.iloc[0]
        ):
            contributions.append({
                'feature': feature_name,
                'value': float(feature_value),
                'contribution': float(shap_value * 100),  # Convert to percentage points
                'direction': 'increase' if shap_value > 0 else 'decrease'
            })
        
        # Sort by absolute contribution and return top_k
        contributions.sort(key=lambda x: abs(x['contribution']), reverse=True)
        return contributions[:top_k]
```

**Example SHAP Output**:

```json
{
  "feature_contributions": [
    {
      "feature": "num_prior_admissions_90d",
      "value": 3,
      "contribution": 12.5,
      "direction": "increase"
    },
    {
      "feature": "age",
      "value": 78,
      "contribution": 8.3,
      "direction": "increase"
    },
    {
      "feature": "charlson_comorbidity_index",
      "value": 6,
      "contribution": 7.2,
      "direction": "increase"
    },
    {
      "feature": "length_of_stay_days",
      "value": 9,
      "contribution": 5.1,
      "direction": "increase"
    },
    {
      "feature": "social_support_score",
      "value": 2,
      "contribution": -4.8,
      "direction": "decrease"
    },
    {
      "feature": "has_follow_up_scheduled",
      "value": 0,
      "contribution": 4.2,
      "direction": "increase"
    }
  ]
}
```

### 4.3 What-If Scenario Modeling

```python
async def predict_what_if(encounter_id: UUID, modifications: dict) -> dict:
    """
    Simulate risk score under modified conditions
    
    Args:
        encounter_id: Encounter to base prediction on
        modifications: Dict of feature names to new values
        
    Returns:
        {
            'original_score': 68.5,
            'modified_score': 52.3,
            'delta': -16.2,
            'changed_features': ['social_support_score', 'has_follow_up_scheduled']
        }
    """
    # Extract original features
    original_features = await feature_engineer.extract_features(encounter_id)
    original_score, _, _ = ensemble_predictor.predict_proba(original_features)
    
    # Apply modifications
    modified_features = original_features.copy()
    for feature_name, new_value in modifications.items():
        if feature_name in modified_features.columns:
            modified_features[feature_name] = new_value
    
    # Predict with modified features
    modified_score, _, _ = ensemble_predictor.predict_proba(modified_features)
    
    return {
        'original_score': round(original_score, 1),
        'modified_score': round(modified_score, 1),
        'delta': round(modified_score - original_score, 1),
        'changed_features': list(modifications.keys())
    }
```

### 4.4 Model Monitoring

#### 4.4.1 Calibration by Risk Band

```python
async def calculate_calibration_metrics(start_date: datetime, end_date: datetime) -> dict:
    """
    Calculate calibration metrics by risk band
    Compares predicted readmission rates vs actual rates
    """
    async with AsyncSessionLocal() as session:
        # Query predictions with outcomes
        query = select(
            RiskPrediction.risk_band,
            RiskPrediction.risk_score,
            Outcome.readmitted
        ).join(
            Outcome, RiskPrediction.encounter_id == Outcome.encounter_id
        ).where(
            RiskPrediction.predicted_at >= start_date,
            RiskPrediction.predicted_at <= end_date,
            Outcome.outcome_date.isnot(None)  # Only completed follow-ups
        )
        
        results = await session.execute(query)
        
        # Group by risk band
        bands = {'low': [], 'medium': [], 'high': []}
        for risk_band, risk_score, readmitted in results:
            bands[risk_band].append({
                'predicted': risk_score / 100,
                'actual': int(readmitted)
            })
        
        # Calculate metrics per band
        calibration = []
        for band, predictions in bands.items():
            if predictions:
                predicted_rate = np.mean([p['predicted'] for p in predictions])
                actual_rate = np.mean([p['actual'] for p in predictions])
                calibration.append({
                    'risk_band': band,
                    'predicted_rate': round(predicted_rate, 3),
                    'actual_rate': round(actual_rate, 3),
                    'count': len(predictions)
                })
        
        return {'calibration_by_band': calibration}
```


#### 4.4.2 Rolling AUROC

```python
async def calculate_rolling_auroc(window_days: int = 30) -> list[dict]:
    """
    Calculate AUROC over rolling time windows
    """
    async with AsyncSessionLocal() as session:
        # Get predictions with outcomes from last 365 days
        cutoff_date = datetime.utcnow() - timedelta(days=365)
        
        query = select(
            RiskPrediction.predicted_at,
            RiskPrediction.risk_score,
            Outcome.readmitted
        ).join(
            Outcome, RiskPrediction.encounter_id == Outcome.encounter_id
        ).where(
            RiskPrediction.predicted_at >= cutoff_date,
            Outcome.outcome_date.isnot(None)
        ).order_by(RiskPrediction.predicted_at)
        
        results = await session.execute(query)
        data = [(predicted_at, risk_score, readmitted) for predicted_at, risk_score, readmitted in results]
        
        # Calculate rolling AUROC
        rolling_metrics = []
        for i in range(window_days, len(data)):
            window_data = data[i-window_days:i]
            y_true = [d[2] for d in window_data]
            y_score = [d[1] / 100 for d in window_data]
            
            if len(set(y_true)) > 1:  # Need both classes
                auroc = roc_auc_score(y_true, y_score)
                rolling_metrics.append({
                    'date': window_data[-1][0].isoformat(),
                    'auroc': round(auroc, 3),
                    'n_predictions': len(window_data)
                })
        
        return rolling_metrics
```

#### 4.4.3 Population Stability Index (PSI) for Drift Detection

```python
def calculate_psi(reference_dist: np.ndarray, current_dist: np.ndarray, bins=10) -> float:
    """
    Calculate Population Stability Index
    PSI > 0.25 indicates significant drift
    """
    ref_counts, bin_edges = np.histogram(reference_dist, bins=bins)
    curr_counts, _ = np.histogram(current_dist, bins=bin_edges)
    
    ref_pcts = ref_counts / len(reference_dist) + 1e-10
    curr_pcts = curr_counts / len(current_dist) + 1e-10
    
    psi = np.sum((curr_pcts - ref_pcts) * np.log(curr_pcts / ref_pcts))
    return psi

async def detect_feature_drift(feature_name: str) -> dict:
    """
    Detect drift in a specific feature by comparing recent vs baseline distribution
    """
    async with AsyncSessionLocal() as session:
        # Get baseline distribution (first 1000 predictions)
        baseline_query = select(RiskPrediction.feature_contributions).limit(1000)
        baseline_results = await session.execute(baseline_query)
        baseline_values = [
            self._extract_feature_value(fc, feature_name) 
            for fc, in baseline_results 
            if fc is not None
        ]
        
        # Get current distribution (last 1000 predictions)
        current_query = select(RiskPrediction.feature_contributions).order_by(
            RiskPrediction.predicted_at.desc()
        ).limit(1000)
        current_results = await session.execute(current_query)
        current_values = [
            self._extract_feature_value(fc, feature_name) 
            for fc, in current_results 
            if fc is not None
        ]
        
        # Calculate PSI
        psi_score = calculate_psi(
            np.array(baseline_values),
            np.array(current_values)
        )
        
        return {
            'feature': feature_name,
            'psi_score': round(psi_score, 4),
            'drift_detected': psi_score > 0.25,
            'baseline_mean': round(np.mean(baseline_values), 2),
            'current_mean': round(np.mean(current_values), 2)
        }
```

#### 4.4.4 Fairness Metrics

```python
async def calculate_fairness_metrics(start_date: datetime, end_date: datetime) -> dict:
    """
    Calculate fairness metrics across demographic groups
    """
    async with AsyncSessionLocal() as session:
        # Query predictions with patient demographics and outcomes
        query = select(
            Patient.gender,
            func.floor(func.extract('year', func.age(Patient.date_of_birth)) / 10).label('age_group'),
            RiskPrediction.risk_score,
            RiskPrediction.risk_band,
            Outcome.readmitted
        ).join(
            RiskPrediction, Patient.id == RiskPrediction.patient_id
        ).join(
            Outcome, RiskPrediction.encounter_id == Outcome.encounter_id
        ).where(
            RiskPrediction.predicted_at >= start_date,
            RiskPrediction.predicted_at <= end_date,
            Outcome.outcome_date.isnot(None)
        )
        
        results = await session.execute(query)
        
        # Group by demographics
        by_gender = {}
        by_age_group = {}
        
        for gender, age_group, risk_score, risk_band, readmitted in results:
            # Group by gender
            if gender not in by_gender:
                by_gender[gender] = {'scores': [], 'high_risk': 0, 'readmissions': 0, 'total': 0}
            by_gender[gender]['scores'].append(risk_score)
            by_gender[gender]['high_risk'] += int(risk_band == 'high')
            by_gender[gender]['readmissions'] += int(readmitted)
            by_gender[gender]['total'] += 1
            
            # Group by age group
            age_key = f"{int(age_group)*10}-{int(age_group)*10+9}"
            if age_key not in by_age_group:
                by_age_group[age_key] = {'scores': [], 'high_risk': 0, 'readmissions': 0, 'total': 0}
            by_age_group[age_key]['scores'].append(risk_score)
            by_age_group[age_key]['high_risk'] += int(risk_band == 'high')
            by_age_group[age_key]['readmissions'] += int(readmitted)
            by_age_group[age_key]['total'] += 1
        
        # Calculate metrics
        def format_group(groups):
            return [
                {
                    'group': group,
                    'avg_risk_score': round(np.mean(data['scores']), 1),
                    'high_risk_pct': round(data['high_risk'] / data['total'], 3),
                    'readmission_rate': round(data['readmissions'] / data['total'], 3),
                    'count': data['total']
                }
                for group, data in groups.items()
            ]
        
        return {
            'by_gender': format_group(by_gender),
            'by_age_group': format_group(by_age_group)
        }
```

## 5. Frontend Architecture

### 5.1 Project Structure

```
frontend/
├── public/
│   ├── index.html
│   └── favicon.ico
├── src/
│   ├── main.tsx                    # Entry point
│   ├── App.tsx                     # Root component with routing
│   ├── api/
│   │   ├── client.ts               # Axios instance with auth interceptor
│   │   ├── auth.ts                 # Auth API calls
│   │   ├── patients.ts             # Patient API calls
│   │   ├── predictions.ts          # Prediction API calls
│   │   └── ...
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Header.tsx          # App header with user menu
│   │   │   ├── Sidebar.tsx         # Navigation sidebar
│   │   │   ├── Layout.tsx          # Main layout wrapper
│   │   │   └── NotificationBell.tsx
│   │   ├── patients/
│   │   │   ├── PatientCard.tsx
│   │   │   ├── PatientTable.tsx
│   │   │   ├── RiskBadge.tsx
│   │   │   └── PatientFilters.tsx
│   │   ├── predictions/
│   │   │   ├── RiskScoreGauge.tsx
│   │   │   ├── FeatureContributions.tsx
│   │   │   └── WhatIfSimulator.tsx
│   │   ├── interventions/
│   │   │   ├── InterventionCard.tsx
│   │   │   ├── KanbanBoard.tsx     # dnd-kit drag-and-drop
│   │   │   └── KanbanColumn.tsx
│   │   ├── charts/
│   │   │   ├── CalibrationChart.tsx    # Recharts
│   │   │   ├── TrendChart.tsx
│   │   │   ├── BarChart.tsx
│   │   │   └── FairnessChart.tsx
│   │   └── common/
│   │       ├── Button.tsx
│   │       ├── Input.tsx
│   │       ├── Select.tsx
│   │       ├── Modal.tsx
│   │       ├── LoadingSpinner.tsx
│   │       └── ErrorBoundary.tsx
│   ├── pages/
│   │   ├── LoginPage.tsx           # 1. Login
│   │   ├── DashboardPage.tsx       # 2. Dashboard with stats
│   │   ├── PatientsPage.tsx        # 3. Patients list with filters
│   │   ├── PatientDetailPage.tsx   # 4. Patient detail
│   │   ├── NewAdmissionPage.tsx    # 5. New admission form
│   │   ├── DischargePage.tsx       # 5. Discharge form
│   │   ├── TasksPage.tsx           # 6. Tasks Kanban board
│   │   ├── MonitoringPage.tsx      # 7. Model monitoring
│   │   ├── FairnessPage.tsx        # 8. Fairness/Model metrics
│   │   └── AuditPage.tsx           # 9. Audit logs
│   ├── hooks/
│   │   ├── useAuth.ts              # Auth context hook
│   │   ├── usePatients.ts          # TanStack Query for patients
│   │   ├── usePredictions.ts       # TanStack Query for predictions
│   │   └── useNotifications.ts     # Notifications polling
│   ├── stores/
│   │   └── authStore.ts            # Zustand store for auth state
│   ├── types/
│   │   ├── api.ts                  # API response types
│   │   ├── models.ts               # Domain model types
│   │   └── index.ts
│   ├── utils/
│   │   ├── formatters.ts           # Date, number formatting
│   │   ├── validators.ts           # Form validation
│   │   └── constants.ts            # App constants
│   └── styles/
│       ├── index.css               # Tailwind base imports
│       └── theme.css               # Custom CSS variables
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
├── Dockerfile
└── README.md
```


### 5.2 Page Specifications

#### 5.2.1 Login Page

**Route**: `/login`
**Components**: LoginForm, Logo
**Features**:
- Email and password inputs
- "Remember me" checkbox
- "Forgot password" link
- Form validation with error messages
- Loading state during authentication

#### 5.2.2 Dashboard Page

**Route**: `/dashboard`
**Components**: StatCard, TrendChart, RecentPatientsTable, AlertsList
**Features**:
- Summary cards: Total Patients, Active Encounters, High Risk Count, Readmission Rate
- Admissions/Discharges trend chart (last 30 days)
- Recently discharged high-risk patients table (top 10)
- Recent alerts list (unresolved, top 5)
- Ward filter dropdown (if user manages multiple wards)

```tsx
// Example Dashboard Layout
const DashboardPage = () => {
  const { data: stats } = useQuery({
    queryKey: ['dashboard', 'stats'],
    queryFn: () => api.dashboard.getStats()
  });
  
  return (
    <Layout>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <StatCard title="Total Patients" value={stats.total_patients} icon={UsersIcon} />
        <StatCard title="Active Encounters" value={stats.active_encounters} icon={ActivityIcon} />
        <StatCard title="High Risk" value={stats.high_risk_count} icon={AlertTriangleIcon} color="red" />
        <StatCard title="Readmission Rate" value={`${(stats.readmission_rate_30d * 100).toFixed(1)}%`} icon={TrendingUpIcon} />
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title="Admission Trends">
          <TrendChart data={trendData} />
        </Card>
        <Card title="Recent Alerts">
          <AlertsList alerts={recentAlerts} />
        </Card>
      </div>
    </Layout>
  );
};
```

#### 5.2.3 Patients Page

**Route**: `/patients`
**Components**: PatientTable, PatientFilters, Pagination
**Features**:
- Table columns: MRN, Name, Age, Ward, Risk Score, Risk Band, Actions
- Filters: Search (name/MRN), Ward, Risk Band (all|low|medium|high)
- Sorting: Name, Age, Risk Score
- Pagination: 20 per page default
- Row click navigates to patient detail
- Risk score displayed with color coding (red ≥60, yellow 40-59, green <40)

#### 5.2.4 Patient Detail Page

**Route**: `/patients/:id`
**Components**: PatientHeader, RiskScoreGauge, FeatureContributions, EncounterTimeline, InterventionsList, CareplanButton
**Features**:
- Patient demographics header
- Current risk score with gauge visualization
- SHAP feature contributions waterfall chart
- Encounter timeline (admissions/discharges)
- Active interventions list
- "Generate New Prediction" button
- "Create Intervention" button
- Tabs: Overview, Encounters, Medications, Lab Results, Social Screening

#### 5.2.5 New Admission / Discharge Pages

**Route**: `/admission/new`, `/discharge/:encounter_id`
**Components**: MultiStepForm, DiagnosisInput, MedicationInput, LabResultInput, SocialScreeningForm
**Features**:

**Admission Form**:
- Step 1: Patient Demographics (or search existing)
- Step 2: Encounter Details (admission date, ward, admitting provider)
- Step 3: Diagnoses (ICD-10 code search, primary diagnosis flag)
- Step 4: Medications (name, dosage, frequency, route)
- Step 5: Lab Results (test name, value, unit, flag)
- Step 6: Social Screening (housing, food, transportation, social support scores 1-5)
- Form validation at each step
- "Save Draft" and "Submit" buttons

**Discharge Form**:
- Discharge date and time
- Discharging provider
- Discharge disposition (home, facility, other)
- Automatically triggers risk prediction on submit
- Displays risk score result after submission

#### 5.2.6 Tasks Kanban Page

**Route**: `/tasks`
**Components**: KanbanBoard, KanbanColumn, InterventionCard
**Features**:
- Columns: Pending, In Progress, Completed
- Drag-and-drop interventions between columns using dnd-kit
- Filter by assigned user, patient
- Card displays: Patient name, intervention type, due date, priority
- Click card to open detail modal
- "Add Intervention" button opens creation modal

```tsx
// Example Kanban Board
const TasksPage = () => {
  const { data: interventions } = useQuery({
    queryKey: ['interventions'],
    queryFn: () => api.interventions.list()
  });
  
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );
  
  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (over && active.id !== over.id) {
      // Update intervention status based on column
      const newStatus = over.id as 'pending' | 'in_progress' | 'completed';
      updateInterventionStatus.mutate({ id: active.id, status: newStatus });
    }
  };
  
  return (
    <Layout>
      <DndContext sensors={sensors} onDragEnd={handleDragEnd}>
        <div className="flex gap-6">
          <KanbanColumn id="pending" title="Pending" interventions={pendingInterventions} />
          <KanbanColumn id="in_progress" title="In Progress" interventions={inProgressInterventions} />
          <KanbanColumn id="completed" title="Completed" interventions={completedInterventions} />
        </div>
      </DndContext>
    </Layout>
  );
};
```

#### 5.2.7 Monitoring Page

**Route**: `/monitoring`
**Components**: CalibrationChart, ROCCurveChart, DriftTable, PerformanceTimeline
**Features**:
- Calibration plot by risk band (predicted vs actual rates)
- Rolling AUROC chart (last 365 days, 30-day window)
- Drift detection table (PSI scores for key features)
- Performance metrics: AUROC, Precision, Recall, F1
- Date range selector

#### 5.2.8 Fairness / Model Page

**Route**: `/fairness`
**Components**: FairnessMetricsTable, DemographicDistributionChart, DisparityChart, ModelVersionSelector
**Features**:
- Fairness metrics by gender, age group, race (if available)
- Table: Group, Avg Risk Score, High Risk %, Readmission Rate, Count
- Disparity indicators (highlight groups with >10% difference from average)
- Model version selector
- Model metadata: Version, Type, Training Date, Metrics

#### 5.2.9 Audit Page

**Route**: `/audit`
**Components**: AuditLogTable, AuditFilters
**Features**:
- Table columns: Timestamp, User, Action, Resource Type, Resource ID, Details
- Filters: User, Action, Resource Type, Date Range
- Search by resource ID
- Export to CSV
- Admin-only access (403 for other roles)

### 5.3 Color Scheme and Styling

**Primary Colors**:
- Navy: `#0F2A43` (headers, primary buttons)
- Teal: `#0E9F8E` (accents, links, active states)
- Coral: `#E4572E` (alerts, high-risk indicators)

**Risk Score Colors**:
- High (≥60): `#DC2626` (red-600)
- Medium (40-59): `#F59E0B` (amber-500)
- Low (<40): `#10B981` (emerald-500)

**Tailwind Configuration**:

```javascript
// tailwind.config.js
export default {
  content: ['./src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#0F2A43',
          50: '#E6EAF0',
          100: '#CCD5E1',
          900: '#0A1D2E',
        },
        accent: {
          DEFAULT: '#0E9F8E',
          50: '#E6F7F5',
          600: '#0B8072',
        },
        danger: {
          DEFAULT: '#E4572E',
          50: '#FDEEE9',
          600: '#C93D1D',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
};
```

### 5.4 State Management

**Auth State** (Zustand):

```typescript
// stores/authStore.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AuthState {
  user: User | null;
  accessToken: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      isAuthenticated: false,
      login: async (email, password) => {
        const response = await api.auth.login(email, password);
        set({
          user: response.user,
          accessToken: response.access_token,
          isAuthenticated: true,
        });
      },
      logout: () => {
        set({ user: null, accessToken: null, isAuthenticated: false });
      },
    }),
    {
      name: 'auth-storage',
    }
  )
);
```

**Server State** (TanStack Query):

```typescript
// hooks/usePatients.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

export const usePatients = (filters?: PatientFilters) => {
  return useQuery({
    queryKey: ['patients', filters],
    queryFn: () => api.patients.list(filters),
    staleTime: 30000, // 30 seconds
  });
};

export const usePatient = (id: string) => {
  return useQuery({
    queryKey: ['patients', id],
    queryFn: () => api.patients.get(id),
    enabled: !!id,
  });
};

export const useCreatePatient = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: CreatePatientRequest) => api.patients.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['patients'] });
    },
  });
};
```


### 5.5 Component Tree Diagram

```mermaid
graph TB
    App[App.tsx]
    App --> Login[LoginPage]
    App --> Layout[Layout]
    
    Layout --> Header[Header]
    Layout --> Sidebar[Sidebar]
    Layout --> Content[Page Content]
    
    Header --> NotificationBell[NotificationBell]
    Header --> UserMenu[UserMenu]
    
    Content --> Dashboard[DashboardPage]
    Content --> Patients[PatientsPage]
    Content --> PatientDetail[PatientDetailPage]
    Content --> Admission[NewAdmissionPage]
    Content --> Discharge[DischargePage]
    Content --> Tasks[TasksPage]
    Content --> Monitoring[MonitoringPage]
    Content --> Fairness[FairnessPage]
    Content --> Audit[AuditPage]
    
    Dashboard --> StatCard[StatCard x4]
    Dashboard --> TrendChart[TrendChart]
    Dashboard --> AlertsList[AlertsList]
    
    Patients --> PatientFilters[PatientFilters]
    Patients --> PatientTable[PatientTable]
    Patients --> Pagination[Pagination]
    
    PatientDetail --> PatientHeader[PatientHeader]
    PatientDetail --> RiskGauge[RiskScoreGauge]
    PatientDetail --> FeatureContrib[FeatureContributions]
    PatientDetail --> InterventionsList[InterventionsList]
    
    Tasks --> KanbanBoard[KanbanBoard]
    KanbanBoard --> KanbanColumn[KanbanColumn x3]
    KanbanColumn --> InterventionCard[InterventionCard]
    
    Monitoring --> CalibrationChart[CalibrationChart]
    Monitoring --> PerformanceChart[PerformanceChart]
    Monitoring --> DriftTable[DriftTable]
    
    Fairness --> FairnessTable[FairnessMetricsTable]
    Fairness --> DemographicChart[DemographicChart]
    Fairness --> ModelSelector[ModelVersionSelector]
    
    style App fill:#0F2A43,color:#fff
    style Layout fill:#0E9F8E,color:#fff
    style Dashboard fill:#E4572E,color:#fff
```

## 6. Infrastructure and Deployment

### 6.1 Docker Compose Setup

```yaml
# docker-compose.yml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    container_name: readmitcare-db
    environment:
      POSTGRES_DB: readmitcare
      POSTGRES_USER: readmitcare
      POSTGRES_PASSWORD: ${DB_PASSWORD:-dev_password}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U readmitcare"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: readmitcare-backend
    environment:
      DATABASE_URL: postgresql+asyncpg://readmitcare:${DB_PASSWORD:-dev_password}@db:5432/readmitcare
      SECRET_KEY: ${SECRET_KEY:-dev_secret_key_change_in_production}
      ALGORITHM: HS256
      ACCESS_TOKEN_EXPIRE_MINUTES: 480
      DEBUG: ${DEBUG:-true}
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - ./backend:/app
      - ml_models:/app/data/models
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: readmitcare-frontend
    environment:
      VITE_API_BASE_URL: http://localhost:8000
    ports:
      - "5173:5173"
    depends_on:
      - backend
    volumes:
      - ./frontend:/app
      - /app/node_modules
    command: npm run dev -- --host 0.0.0.0

volumes:
  postgres_data:
  ml_models:
```

### 6.2 Backend Dockerfile

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for data
RUN mkdir -p /app/data/models /app/data/datasets

# Expose port
EXPOSE 8000

# Run migrations and start server
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
```

### 6.3 Frontend Dockerfile

```dockerfile
# frontend/Dockerfile
FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./

# Install dependencies
RUN npm ci

# Copy application code
COPY . .

# Expose port
EXPOSE 5173

# Start development server
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
```

### 6.4 Data Preparation Script

```python
# scripts/prepare_data.py
"""
Download UCI diabetes dataset and prepare training data
Falls back to synthetic data if download fails
"""
import pandas as pd
import numpy as np
from pathlib import Path
import urllib.request
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_DIR = Path("backend/data/datasets")
DATA_DIR.mkdir(parents=True, exist_ok=True)

def download_uci_diabetes():
    """Download UCI diabetes dataset"""
    url = "https://archive.ics.uci.edu/ml/machine-learning-databases/00296/dataset_diabetes.zip"
    try:
        logger.info(f"Downloading from {url}")
        urllib.request.urlretrieve(url, DATA_DIR / "diabetes.zip")
        
        # Unzip and process
        import zipfile
        with zipfile.ZipFile(DATA_DIR / "diabetes.zip", 'r') as zip_ref:
            zip_ref.extractall(DATA_DIR)
        
        logger.info("Downloaded UCI diabetes dataset")
        return True
    except Exception as e:
        logger.error(f"Failed to download: {e}")
        return False

def generate_synthetic_data(n_samples=2500):
    """Generate synthetic readmission dataset"""
    logger.info(f"Generating {n_samples} synthetic records")
    
    np.random.seed(42)
    
    data = {
        # Demographics
        'age': np.random.randint(18, 95, n_samples),
        'gender': np.random.choice(['male', 'female'], n_samples),
        
        # Clinical history
        'num_prior_admissions_30d': np.random.poisson(0.5, n_samples),
        'num_prior_admissions_90d': np.random.poisson(1.2, n_samples),
        'num_prior_admissions_365d': np.random.poisson(2.5, n_samples),
        'num_diagnoses': np.random.poisson(3, n_samples),
        'num_medications': np.random.poisson(5, n_samples),
        'length_of_stay_days': np.random.gamma(3, 2, n_samples).astype(int),
        
        # Diagnoses flags
        'has_cardiovascular_disease': np.random.binomial(1, 0.35, n_samples),
        'has_diabetes': np.random.binomial(1, 0.25, n_samples),
        'has_respiratory_disease': np.random.binomial(1, 0.20, n_samples),
        'has_renal_disease': np.random.binomial(1, 0.15, n_samples),
        'charlson_comorbidity_index': np.random.randint(0, 10, n_samples),
        
        # Lab results
        'has_abnormal_labs': np.random.binomial(1, 0.40, n_samples),
        'num_abnormal_labs': np.random.poisson(2, n_samples),
        
        # Social determinants
        'housing_stability_score': np.random.randint(1, 6, n_samples),
        'food_security_score': np.random.randint(1, 6, n_samples),
        'transportation_access_score': np.random.randint(1, 6, n_samples),
        'social_support_score': np.random.randint(1, 6, n_samples),
        
        # Discharge planning
        'discharge_to_home': np.random.binomial(1, 0.75, n_samples),
        'has_follow_up_scheduled': np.random.binomial(1, 0.60, n_samples),
    }
    
    df = pd.DataFrame(data)
    
    # Generate readmission outcome (correlated with features)
    risk_score = (
        df['age'] * 0.3 +
        df['num_prior_admissions_90d'] * 5 +
        df['charlson_comorbidity_index'] * 3 +
        df['length_of_stay_days'] * 1.5 -
        df['social_support_score'] * 2 -
        df['has_follow_up_scheduled'] * 10 +
        np.random.normal(0, 10, n_samples)
    )
    
    # Convert to probability
    prob = 1 / (1 + np.exp(-risk_score / 30))
    df['readmitted'] = np.random.binomial(1, prob)
    
    return df

def main():
    if not download_uci_diabetes():
        logger.warning("Using --synthetic fallback")
        df = generate_synthetic_data()
        
        # Split into train/test (80/20)
        train_size = int(0.8 * len(df))
        train_df = df[:train_size]
        test_df = df[train_size:]
        
        train_df.to_csv(DATA_DIR / "training_data.csv", index=False)
        test_df.to_csv(DATA_DIR / "test_data.csv", index=False)
        
        logger.info(f"Created {len(train_df)} training samples, {len(test_df)} test samples")

if __name__ == "__main__":
    main()
```

### 6.5 Database Seed Script

```python
# scripts/seed_database.py
"""
Seed database with test data:
- 4 users (nurse, doctor, social_worker, admin)
- 2 wards
- ~2000 patient records (test split only)
- Encounters with synthetic social features
- Outcome records for discharges >30 days old
"""
import asyncio
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

from app.database import AsyncSessionLocal
from app.models import User, Ward, Patient, Encounter, Diagnosis, Medication, SocialScreening, Outcome
from app.utils.security import hash_password

async def seed_users(session):
    """Create test users"""
    users_data = [
        {"email": "nurse@hospital.org", "password": "password123", "first_name": "Jane", "last_name": "Nurse", "role": "nurse"},
        {"email": "doctor@hospital.org", "password": "password123", "first_name": "John", "last_name": "Doctor", "role": "doctor"},
        {"email": "social@hospital.org", "password": "password123", "first_name": "Sarah", "last_name": "Social", "role": "social_worker"},
        {"email": "admin@hospital.org", "password": "password123", "first_name": "Admin", "last_name": "User", "role": "admin"},
    ]
    
    for user_data in users_data:
        user = User(
            id=uuid4(),
            email=user_data["email"],
            password_hash=hash_password(user_data["password"]),
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            role=user_data["role"],
            is_active=True
        )
        session.add(user)
    
    await session.commit()
    print(f"Created {len(users_data)} users")

async def seed_wards(session):
    """Create test wards"""
    wards_data = [
        {"name": "Ward A - Cardiology", "location": "Building 1, Floor 3", "capacity": 30},
        {"name": "Ward B - General Medicine", "location": "Building 1, Floor 4", "capacity": 40},
    ]
    
    for ward_data in wards_data:
        ward = Ward(id=uuid4(), **ward_data)
        session.add(ward)
    
    await session.commit()
    print(f"Created {len(wards_data)} wards")

async def seed_patients_from_csv(session, wards, users):
    """Seed patients from test split CSV"""
    csv_path = Path("backend/data/datasets/test_data.csv")
    if not csv_path.exists():
        print("No test data CSV found, skipping patient seed")
        return
    
    df = pd.read_csv(csv_path)
    print(f"Loading {len(df)} patients from CSV")
    
    for idx, row in df.iterrows():
        # Create patient
        patient_id = uuid4()
        patient = Patient(
            id=patient_id,
            mrn=f"MRN{str(idx).zfill(6)}",
            first_name=f"Patient{idx}",
            last_name=f"Test{idx}",
            date_of_birth=datetime.now() - timedelta(days=365 * row['age']),
            gender=row['gender'],
            phone=f"555-{str(idx).zfill(4)}",
            current_ward_id=wards[idx % len(wards)].id,
            primary_provider_id=users[idx % len(users)].id
        )
        session.add(patient)
        
        # Create encounter (discharged 30-90 days ago for outcome tracking)
        days_ago = 30 + (idx % 60)
        admission_date = datetime.now() - timedelta(days=days_ago + int(row['length_of_stay_days']))
        discharge_date = datetime.now() - timedelta(days=days_ago)
        
        encounter_id = uuid4()
        encounter = Encounter(
            id=encounter_id,
            patient_id=patient_id,
            encounter_type='inpatient',
            admission_date=admission_date,
            discharge_date=discharge_date,
            admitting_provider_id=users[0].id,
            discharging_provider_id=users[1].id,
            discharge_disposition='home' if row['discharge_to_home'] == 1 else 'facility'
        )
        session.add(encounter)
        
        # Create social screening
        social = SocialScreening(
            id=uuid4(),
            patient_id=patient_id,
            encounter_id=encounter_id,
            housing_stability_score=int(row['housing_stability_score']),
            food_security_score=int(row['food_security_score']),
            transportation_access_score=int(row['transportation_access_score']),
            social_support_score=int(row['social_support_score']),
            screened_by_id=users[2].id,
            screened_at=admission_date + timedelta(hours=6)
        )
        session.add(social)
        
        # Create outcome for discharges >30 days old
        if days_ago >= 30:
            readmitted = bool(row['readmitted'])
            outcome = Outcome(
                id=uuid4(),
                patient_id=patient_id,
                encounter_id=encounter_id,
                readmitted=readmitted,
                readmission_date=discharge_date + timedelta(days=15) if readmitted else None,
                days_to_readmission=15 if readmitted else None,
                readmission_reason="Complication" if readmitted else None,
                outcome_date=discharge_date + timedelta(days=30)
            )
            session.add(outcome)
        
        if (idx + 1) % 100 == 0:
            await session.commit()
            print(f"Processed {idx + 1} patients")
    
    await session.commit()
    print(f"Seeded {len(df)} patients with encounters and outcomes")

async def main():
    async with AsyncSessionLocal() as session:
        await seed_users(session)
        
        # Get created users and wards
        result = await session.execute(select(User))
        users = list(result.scalars())
        
        await seed_wards(session)
        
        result = await session.execute(select(Ward))
        wards = list(result.scalars())
        
        await seed_patients_from_csv(session, wards, users)

if __name__ == "__main__":
    asyncio.run(main())
```


### 6.6 One-Command Setup

```bash
# setup.sh
#!/bin/bash

set -e

echo "ReadmitCare Platform Setup"
echo "============================"

# Check prerequisites
echo "Checking prerequisites..."
command -v docker >/dev/null 2>&1 || { echo "Docker is required but not installed. Aborting." >&2; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "Docker Compose is required but not installed. Aborting." >&2; exit 1; }

# Prepare data
echo "Preparing training data..."
python scripts/prepare_data.py

# Build and start services
echo "Building Docker containers..."
docker-compose build

echo "Starting services..."
docker-compose up -d

# Wait for database to be ready
echo "Waiting for database to be ready..."
until docker-compose exec -T db pg_isready -U readmitcare; do
  sleep 1
done

# Run migrations
echo "Running database migrations..."
docker-compose exec -T backend alembic upgrade head

# Seed database
echo "Seeding database with test data..."
docker-compose exec -T backend python scripts/seed_database.py

echo ""
echo "✅ Setup complete!"
echo ""
echo "Services are running:"
echo "  - Frontend: http://localhost:5173"
echo "  - Backend API: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo ""
echo "Test accounts:"
echo "  - Nurse: nurse@hospital.org / password123"
echo "  - Doctor: doctor@hospital.org / password123"
echo "  - Social Worker: social@hospital.org / password123"
echo "  - Admin: admin@hospital.org / password123"
echo ""
echo "To view logs: docker-compose logs -f"
echo "To stop: docker-compose down"
```

## 7. Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property Reflection

After reviewing all acceptance criteria, the following redundancies and consolidation opportunities were identified:

**Redundancies Eliminated**:
1. Individual table structure checks (1.1-1.10) → Combined into single schema validation property
2. Multiple password validation checks → Consolidated into single password security property
3. Separate CRUD operation tests → Consolidated into resource operation properties
4. Multiple filtering/pagination tests → Combined into query operation property
5. Individual JWT field checks → Merged into token structure property
6. Separate audit logging triggers → Unified into audit completeness property

**Combined Properties**:
- Foreign key enforcement + cascade behavior → Database referential integrity
- Input validation + sanitization → Input security
- Permission checks across endpoints → RBAC enforcement
- Calibration + AUROC + drift → Model monitoring suite

The consolidated properties below provide comprehensive coverage while avoiding logical redundancy.

### Property 1: Database Referential Integrity

*For any* database operation that creates or modifies records with foreign key relationships, the system SHALL enforce referential integrity constraints and execute appropriate cascade actions (cascade delete for dependent records, set null for optional references) when parent records are modified or deleted.

**Validates: Requirements 1.11**

### Property 2: Password Hash Security

*For any* password provided during user registration or password change, the system SHALL hash it using bcrypt with cost factor ≥12, and the stored hash SHALL be verifiable against the original password but computationally infeasible to reverse.

**Validates: Requirements 2.2**

### Property 3: JWT Token Structure Completeness

*For any* successful authentication, the generated JWT access token SHALL contain all required fields (sub, email, role, ward_id, exp, iat) with valid types and values, and the token SHALL be verifiable using the configured secret key and algorithm.

**Validates: Requirements 2.5**

### Property 4: Role-Based Permission Enforcement

*For any* API request requiring authentication, if the requesting user's role is not in the set of allowed roles for that endpoint, the system SHALL return HTTP 403 Forbidden and SHALL NOT execute the requested operation.

**Validates: Requirements 2.9, 2.10, 2.11, 2.12, 2.13, 4.15**

### Property 5: Pagination Consistency

*For any* paginated list endpoint, given query parameters (page, limit) and a stable dataset, the union of all pages SHALL equal the complete dataset with no duplicates or omissions, and page boundaries SHALL align with the specified limit.

**Validates: Requirements 3.4, 4.4**

### Property 6: Unique Constraint Enforcement

*For any* attempt to create a record with a unique field (user email, patient MRN), if a non-deleted record with that value already exists, the system SHALL reject the operation with HTTP 409 Conflict.

**Validates: Requirements 3.11**

### Property 7: Field Validation Ranges

*For any* numeric field with specified constraints (risk_score 0-100, social screening scores 1-5), if an input value falls outside the valid range, the system SHALL reject the request with HTTP 400 and a descriptive error message identifying the invalid field.

**Validates: Requirements 3.12, 3.13**

### Property 8: State Machine Transition Validity

*For any* resource with defined state transitions (care plan status: draft→active→completed→archived), an update request SHALL succeed only if the transition is allowed by the workflow rules, otherwise returning HTTP 400.

**Validates: Requirements 4.14**

### Property 9: Risk Band Assignment Consistency

*For any* risk prediction with calculated risk_score, the assigned risk_band SHALL match the threshold rules: "high" if risk_score ≥ 60, "medium" if 40 ≤ risk_score < 60, "low" if risk_score < 40.

**Validates: Requirements 5.6**

### Property 10: High-Risk Alert Creation

*For any* risk prediction that results in risk_score ≥ 60, the system SHALL automatically create a notification record with type "high_risk" and priority "high" assigned to the patient's care team.

**Validates: Requirements 5.8**

### Property 11: Alert State Transitions

*For any* alert, the status transitions SHALL follow the sequence: active → acknowledged → resolved, and once an alert is resolved, subsequent status changes SHALL be rejected.

**Validates: Requirements 6.4, 6.6**

### Property 12: Appointment Status Side Effects

*For any* appointment status update to "no_show", the system SHALL automatically create a missed_appointment alert with the patient and appointment details.

**Validates: Requirements 7.6**

### Property 13: Double-Booking Prevention

*For any* new appointment creation request, if an existing non-cancelled appointment for the same patient overlaps in time (±30 minutes), the system SHALL reject the request with HTTP 409.

**Validates: Requirements 7.13**

### Property 14: Audit Log Immutability

*For any* audit log record, once created, all modification attempts (UPDATE or DELETE operations) SHALL be rejected by the database or application layer, ensuring audit trail integrity.

**Validates: Requirements 8.11**

### Property 15: Audit Log Completeness

*For any* operation in the set {patient record access, care plan modification, user authentication, role change, data export}, the system SHALL create a corresponding audit log entry containing user_id, action, resource_type, resource_id, ip_address, user_agent, and timestamp.

**Validates: Requirements 8.3, 8.4**

### Property 16: Model Input Feature Handling

*For any* risk prediction request, if critical features are missing from the input (age, length_of_stay, num_diagnoses), the system SHALL either impute using the configured strategy or return an error listing the missing required features.

**Validates: Requirements 9.6, 9.7**

### Property 17: Model Output Consistency

*For any* risk prediction, the output SHALL include risk_score (0-100), confidence_lower and confidence_upper (forming a valid interval), risk_band, feature_contributions (array of top 8 factors), and model_version, all with correct types and valid ranges.

**Validates: Requirements 9.2, 9.10**

### Property 18: Feature Preprocessing Determinism

*For any* given input feature set, the preprocessing pipeline (scaling, encoding, imputation) SHALL produce the same transformed feature vector when applied multiple times, ensuring prediction reproducibility.

**Validates: Requirements 9.8**

### Property 19: SHAP Contribution Sum

*For any* SHAP explanation, the sum of all feature contributions plus the base value (model's average prediction) SHALL approximately equal the predicted risk_score within a tolerance of ±1 percentage point.

**Validates: Requirements 9.2 (explainability correctness)**

### Property 20: Calibration Metric Consistency

*For any* calibration calculation over a time period, the reported predicted_rate for each risk_band SHALL equal the mean of predicted probabilities for predictions in that band, and actual_rate SHALL equal the proportion of actual readmissions in that band.

**Validates: Requirements 5.11 (model monitoring)**

### Property 21: PSI Drift Detection Threshold

*For any* feature drift calculation, if the calculated PSI score exceeds 0.25, the drift_detected flag SHALL be true; otherwise false.

**Validates: Requirements 9.14 (drift monitoring)**

### Property 22: Fairness Metric Neutrality

*For any* fairness analysis across demographic groups (gender, age, race), the reported metrics (avg_risk_score, high_risk_pct, readmission_rate) for each group SHALL be computed independently without cross-group bias in the calculation methodology.

**Validates: Requirements (fairness calculations - implicit from monitoring requirements)**

### Property 23: Input Sanitization

*For any* user-provided input string (text fields, search queries, filter values), the system SHALL sanitize to prevent SQL injection and XSS attacks by escaping or rejecting special characters (<, >, &, ", ', ;, --, /*, */) and using parameterized queries for database operations.

**Validates: Requirements 17.5, 17.6**

### Property 24: Authentication Token Expiration

*For any* JWT access token, once the expiration time (exp claim) has passed, subsequent requests using that token SHALL be rejected with HTTP 401 Unauthorized, requiring re-authentication.

**Validates: Requirements 2.6**

### Property 25: Ward-Based Data Isolation

*For any* user with role nurse, doctor, or social_worker making a patient data request, the returned results SHALL include only patients whose current_ward_id matches the user's ward_id, unless the user has explicit cross-ward permissions.

**Validates: Requirements 18.2**

### Property 26: Session Timeout Enforcement

*For any* authenticated user session, if no API requests are made for 30 consecutive minutes, the next request SHALL fail with HTTP 401, and the user SHALL be required to re-authenticate.

**Validates: Requirements 17.10**

### Property 27: Encounter Discharge Triggers Prediction

*For any* encounter update that sets discharge_date from NULL to a non-NULL value, the system SHALL automatically trigger a risk prediction for that encounter and store the result in the risk_predictions table.

**Validates: Requirements 5.7**

### Property 28: Notification Read State Tracking

*For any* notification marked as read (is_read updated to true), the read_at timestamp SHALL be set to the current UTC time, and subsequent reads SHALL not update the timestamp.

**Validates: Requirements (notification tracking - implicit)**

### Property 29: Intervention Due Date Alerting

*For any* intervention with status in {pending, in_progress} and due_date < current_time, the hourly background job SHALL create or update a notification for the assigned_to user with type "overdue_intervention".

**Validates: Requirements (background job correctness - implicit from 3.4)**

### Property 30: Model Version Activation Uniqueness

*For any* model version activation, at most one model version SHALL have is_active=true at any time, and activating a new version SHALL set is_active=false for all other versions.

**Validates: Requirements (model management - implicit)**

## 8. Error Handling Strategy

### 8.1 HTTP Status Codes

| Status Code | Use Case | Example |
|-------------|----------|---------|
| 200 OK | Successful GET, PUT request | Patient details retrieved |
| 201 Created | Successful POST creating resource | New patient created |
| 204 No Content | Successful DELETE | Intervention deleted |
| 400 Bad Request | Validation error, malformed input | Invalid date format |
| 401 Unauthorized | Missing or invalid authentication | Expired JWT token |
| 403 Forbidden | Valid auth but insufficient permissions | Nurse accessing admin endpoint |
| 404 Not Found | Resource doesn't exist | Patient ID not found |
| 409 Conflict | Unique constraint violation | Duplicate MRN |
| 422 Unprocessable Entity | Semantic validation error | Future date for date_of_birth |
| 429 Too Many Requests | Rate limit exceeded | >5 failed login attempts |
| 500 Internal Server Error | Unexpected server error | Database connection failure |
| 503 Service Unavailable | Service temporarily down | ML model unavailable |

### 8.2 Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": [
      {
        "field": "date_of_birth",
        "message": "Date of birth must be in the past"
      },
      {
        "field": "risk_score",
        "message": "Risk score must be between 0 and 100"
      }
    ],
    "timestamp": "2024-01-20T15:30:00Z",
    "request_id": "req_abc123"
  }
}
```

### 8.3 Frontend Error Handling

```typescript
// api/client.ts
import axios from 'axios';
import { useAuthStore } from '@/stores/authStore';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 30000,
});

// Request interceptor: Add auth token
apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor: Handle errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired, redirect to login
      useAuthStore.getState().logout();
      window.location.href = '/login';
    } else if (error.response?.status === 403) {
      // Insufficient permissions
      toast.error('You do not have permission to perform this action');
    } else if (error.response?.status >= 500) {
      // Server error
      toast.error('Server error. Please try again later.');
    }
    return Promise.reject(error);
  }
);
```

## 9. Testing Strategy

### 9.1 Backend Testing

**Unit Tests** (pytest):
- Model validation (Pydantic schemas)
- Business logic in service layer
- Utility functions (security, formatters)
- Feature engineering

**Integration Tests**:
- API endpoints with test database
- Database queries and ORM operations
- ML model predictions with test data

**Test Structure**:
```python
# tests/test_patients.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_patient_success(client: AsyncClient, auth_headers):
    """Test successful patient creation"""
    payload = {
        "mrn": "TEST001",
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": "1970-01-01",
        "gender": "male"
    }
    
    response = await client.post("/api/patients", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["mrn"] == "TEST001"
    assert "id" in data

@pytest.mark.asyncio
async def test_create_patient_duplicate_mrn(client: AsyncClient, auth_headers, existing_patient):
    """Test duplicate MRN rejection"""
    payload = {
        "mrn": existing_patient.mrn,  # Duplicate
        "first_name": "Jane",
        "last_name": "Doe",
        "date_of_birth": "1980-01-01",
        "gender": "female"
    }
    
    response = await client.post("/api/patients", json=payload, headers=auth_headers)
    assert response.status_code == 409
    assert "MRN already exists" in response.json()["error"]["message"]
```

### 9.2 Frontend Testing

**Unit Tests** (Vitest + React Testing Library):
- Component rendering
- User interactions
- Form validation
- Utility functions

**Example**:
```typescript
// components/patients/RiskBadge.test.tsx
import { render, screen } from '@testing-library/react';
import { RiskBadge } from './RiskBadge';

describe('RiskBadge', () => {
  it('renders high risk with red color', () => {
    render(<RiskBadge score={75} />);
    const badge = screen.getByText(/high/i);
    expect(badge).toHaveClass('bg-red-600');
  });
  
  it('renders medium risk with yellow color', () => {
    render(<RiskBadge score={50} />);
    const badge = screen.getByText(/medium/i);
    expect(badge).toHaveClass('bg-amber-500');
  });
  
  it('renders low risk with green color', () => {
    render(<RiskBadge score={25} />);
    const badge = screen.getByText(/low/i);
    expect(badge).toHaveClass('bg-emerald-500');
  });
});
```

## 10. Summary

This technical design document provides comprehensive specifications for the ReadmitCare platform, covering:

1. **Database Design**: 14 PostgreSQL tables with complete schema, foreign keys, indexes, and support for SQLite development
2. **Backend Architecture**: FastAPI with 14 API endpoint groups, JWT authentication, RBAC, APScheduler background jobs, and business logic separation
3. **ML Pipeline**: XGBoost ensemble (15 models) with uncertainty quantification, SHAP explainability (top 8 factors), risk banding, what-if scenarios, and monitoring (calibration, AUROC, PSI drift, fairness)
4. **Frontend Architecture**: React 18 + TypeScript with 9 pages, TanStack Query state management, Tailwind CSS styling (navy/teal/coral theme), Recharts visualizations, dnd-kit Kanban
5. **Infrastructure**: Docker Compose setup with one-command deployment, data preparation script (UCI dataset with synthetic fallback), seed script (2000+ test records)
6. **Correctness Properties**: 30 properties covering database integrity, authentication security, permission enforcement, risk prediction accuracy, monitoring correctness, and input validation

The design enables rapid development with clear separation of concerns, comprehensive testing capabilities, and production-ready infrastructure configuration.

