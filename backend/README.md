# ReadmitCare Backend API

FastAPI-based backend for the ReadmitCare hospital discharge-planning platform.

## Dockerfile Configuration

The Dockerfile is configured for production deployment with the following specifications:

### Base Image
- **Python 3.11-slim**: Lightweight Python runtime optimized for production

### System Dependencies
- **gcc**: Required for compiling Python packages with C extensions
- **postgresql-client**: PostgreSQL database client tools

### Python Dependencies
All Python dependencies are defined in `requirements.txt` and include:
- FastAPI 0.115.0 - Web framework
- SQLAlchemy 2.0.35 - ORM with async support
- asyncpg/aiosqlite - Async database drivers
- Alembic 1.13.2 - Database migrations
- XGBoost 2.1.1 - Machine learning model
- PyJWT 2.9.0 - JWT authentication
- bcrypt 4.2.0 - Password hashing

### Working Directory
- Application code is mounted at `/app`

### Data Directories
- `/app/data/models` - Trained ML models
- `/app/data/datasets` - Training/seed data

### Port
- **8000**: FastAPI application server

### Entrypoint
The container automatically:
1. Runs database migrations: `alembic upgrade head`
2. Starts Uvicorn server: `uvicorn app.main:app --host 0.0.0.0 --port 8000`

## Building the Docker Image

```bash
docker build -t readmitcare-backend .
```

## Running the Container

```bash
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/readmitcare \
  -e SECRET_KEY=your-secret-key \
  readmitcare-backend
```

## Environment Variables

Required environment variables:
- `DATABASE_URL` - Database connection string
- `SECRET_KEY` - JWT secret key
- `ALGORITHM` - JWT algorithm (default: HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES` - Token expiration (default: 480)
- `DEBUG` - Debug mode (default: false)

## Development

For local development without Docker:

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download training dataset
python scripts/download_uci_dataset.py

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload
```

## Dataset Setup

The platform uses the UCI Diabetes 130-US Hospitals dataset for training the readmission prediction model.

### Downloading the Dataset

Run the dataset download script:

```bash
python scripts/download_uci_dataset.py
```

**Features:**
- Downloads from UCI ML Repository using official `ucimlrepo` package
- Automatic retry with exponential backoff (3 attempts)
- CSV structure validation
- Stores in `data/datasets/diabetic_data.csv`

**Dataset Information:**
- **Source**: UCI Machine Learning Repository (Dataset ID: 296)
- **Size**: 101,766 records, ~16 MB
- **Time Period**: 1999-2008
- **Hospitals**: 130 US hospitals
- **Features**: 48 columns including demographics, diagnoses, medications, lab results
- **Target**: Readmission status (NO, <30 days, >30 days)

### Testing the Dataset

Verify the downloaded dataset:

```bash
python scripts/test_dataset.py
```

This validates:
- File exists and has correct size
- CSV structure is valid
- Required columns are present
- Target variable has expected values
- Data quality checks pass

See `data/README.md` for detailed dataset documentation.

## Health Checks

- **Liveness**: `GET /health/live` - Returns 200 if service is running
- **Readiness**: `GET /health/ready` - Returns 200 if service is ready to accept requests

## API Documentation

Once running, access:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
