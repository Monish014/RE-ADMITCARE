# Implementation Plan: ReadmitCare Platform

## Overview

This implementation plan breaks down the ReadmitCare platform development into six phases, following an incremental approach that establishes foundational infrastructure first, then builds core prediction and patient management features, followed by interventions, workflow automation, monitoring, and comprehensive testing. Each task references specific requirements and includes clear acceptance criteria.

## Tasks

### Phase 1: Foundation & Infrastructure

- [x] 1. Set up Docker Compose development environment
  - [x] 1.1 Create docker-compose.yml with PostgreSQL 13+, backend API, and frontend services
    - Define PostgreSQL service with volume persistence and health checks
    - Define backend service with hot reload for development
    - Define frontend service with Vite dev server
    - Configure networking and environment variables
    - _Requirements: 24.2, 24.3_
  
  - [x] 1.2 Create Dockerfile for backend FastAPI application
    - Use Python 3.11 base image
    - Install dependencies from requirements.txt
    - Configure working directory and entrypoint
    - _Requirements: 24.2, 24.6_
  
  - [x] 1.3 Create Dockerfile for frontend React application
    - Use Node.js 18+ base image
    - Configure Vite build process
    - Serve production build with nginx
    - _Requirements: 24.6_

- [x] 2. Implement PostgreSQL database schema with SQLAlchemy ORM
  - [x] 2.1 Create SQLAlchemy models for core entities
    - Implement User, Ward, Patient, Encounter models with proper relationships
    - Add enums for role, encounter_type, gender
    - Configure UUID primary keys and timestamps
    - _Requirements: 1.1, 1.3_
  
  - [x] 2.2 Create SQLAlchemy models for clinical data
    - Implement Diagnosis, Medication, LabResult, SocialScreening models
    - Add foreign key relationships to Patient and Encounter
    - Include validation constraints (check constraints)
    - _Requirements: 1.1_
  
  - [x] 2.3 Create SQLAlchemy models for risk and interventions
    - Implement RiskPrediction, Intervention, FollowUpContact, Outcome models
    - Add JSONB columns for feature_contributions and metadata
    - Configure cascade rules for deletions
    - _Requirements: 1.9, 1.10_
  
  - [x] 2.4 Create SQLAlchemy models for system operations
    - Implement ModelVersion, Notification, AuditLog models
    - Add indexes for frequently queried fields
    - Configure immutability for audit logs
    - _Requirements: 1.8, 1.11, 1.12_

- [x] 3. Set up Alembic database migrations
  - [x] 3.1 Initialize Alembic and create initial migration
    - Configure alembic.ini with async database URL support
    - Create initial migration from SQLAlchemy models
    - Test migration up and down on PostgreSQL
    - Test migration on SQLite for development fallback
    - _Requirements: 24.10_
  
  - [x] 3.2 Create database indexes migration
    - Add composite indexes for common query patterns
    - Create indexes on foreign keys for join performance
    - Add indexes for pagination and filtering (created_at, risk_score, status fields)
    - _Requirements: 1.12_

- [x] 4. Implement data preparation and seeding scripts
  - [x] 4.1 Create UCI diabetes readmission dataset download script
    - Download dataset from UCI repository
    - Parse and validate CSV structure
    - Handle network failures with retry logic
    - _Requirements: 9.3_
  
  - [x] 4.2 Create synthetic data generation fallback
    - Generate realistic patient demographics using Faker
    - Create plausible encounter data with admission/discharge dates
    - Generate diagnoses, medications, and lab results
    - Calculate synthetic readmission outcomes
    - _Requirements: 9.3_
  
  - [x] 4.3 Create database seed script
    - Seed initial users (admin, sample doctors, nurses, social workers)
    - Seed wards and organizational structure
    - Seed sample patients with complete clinical history
    - Hash passwords securely with bcrypt cost factor 12
    - _Requirements: 2.2, 24.10_

- [x] 5. Build ML model training pipeline
  - [x] 5.1 Implement feature engineering module
    - Extract demographic features (age, gender encoding)
    - Calculate clinical history features (prior admissions, days since last admission)
    - Compute diagnosis-based features (num_diagnoses, specific condition flags)
    - Generate medication features (polypharmacy indicators)
    - Extract lab result features (abnormal flags, missing labs)
    - Process social screening scores
    - _Requirements: 9.1_
  
  - [x] 5.2 Create XGBoost ensemble training script
    - Implement bootstrap sampling for 15 model ensemble
    - Configure XGBoost hyperparameters (max_depth, learning_rate, n_estimators)
    - Train baseline logistic regression for comparison
    - Handle missing values with model-based imputation
    - Save trained models to data/models/ directory
    - _Requirements: 9.3, 9.4, 9.5, 9.6, 9.8_
  
  - [x] 5.3 Validate model performance on test set
    - Calculate accuracy, precision, recall, F1-score
    - Verify AUC-ROC >= 0.80 threshold
    - Generate calibration curves
    - Test prediction latency < 500ms
    - _Requirements: 9.4, 9.5, 9.12_

- [x] 6. Implement JWT authentication and authorization
  - [x] 6.1 Create authentication utilities
    - Implement password hashing with bcrypt (cost factor 12)
    - Create JWT token generation with 8-hour expiration
    - Implement JWT token validation and refresh
    - Add rate limiting for login attempts (5 attempts per 15 minutes)
    - _Requirements: 2.2, 2.3, 2.4, 2.5, 2.15, 2.16_
  
  - [x] 6.2 Build authentication endpoints
    - Implement POST /api/auth/register endpoint
    - Implement POST /api/auth/login endpoint with credentials validation
    - Implement POST /api/auth/refresh endpoint for token renewal
    - Return user object with JWT token on successful auth
    - _Requirements: 2.1, 2.3_
  
  - [x] 6.3 Create RBAC middleware and dependencies
    - Implement get_current_user dependency for JWT validation
    - Create require_role decorator for permission checks
    - Enforce ward-based data isolation for non-admin users
    - Implement role permission matrix (nurse, doctor, social_worker, admin)
    - _Requirements: 2.8, 2.9, 2.10, 2.11, 2.12, 2.13, 18.1, 18.2, 18.3_

- [x] 7. Implement audit logging system
  - [x] 7.1 Create audit logging middleware
    - Log all API requests with user_id, action, resource_type, resource_id
    - Capture IP address and user agent
    - Record before/after values for data modifications
    - Make audit logs immutable after creation
    - _Requirements: 8.3, 8.4, 18.5, 18.6, 18.7, 18.8, 18.9_
  
  - [x] 7.2 Build audit log query endpoint
    - Implement GET /api/audit/logs with filtering by user, action, resource, date range
    - Restrict access to admin role only
    - Support pagination for large result sets
    - _Requirements: 8.1, 8.2, 8.10, 8.11_

- [x] 8. Create health check endpoints
  - [x] 8.1 Implement liveness and readiness probes
    - Create GET /health/live endpoint (always returns 200 if service running)
    - Create GET /health/ready endpoint (checks database connection)
    - Test database connectivity with pool health check
    - Return JSON with service status and version
    - _Requirements: 24.11, 25.1, 25.6_

- [x] 9. Checkpoint - Verify foundation infrastructure
  - Run database migrations successfully on PostgreSQL and SQLite
  - Seed database with sample data
  - Train baseline ML model and verify AUC-ROC >= 0.80
  - Test authentication flow (register, login, token refresh)
  - Verify audit logging captures create/update operations
  - Ensure all health endpoints return expected responses

### Phase 2: Core Prediction & Patient Management

- [x] 10. Build patient management CRUD API endpoints
  - [x] 10.1 Implement patient list endpoint with filtering
    - Create GET /api/patients with pagination support
    - Add query params: page, limit, search (name/MRN), ward_id, risk_band
    - Return patient list with current risk scores
    - Apply role-based filtering (ward isolation for non-admins)
    - _Requirements: 3.3, 3.4_
  
  - [x] 10.2 Implement patient creation endpoint
    - Create POST /api/patients with validation
    - Validate MRN uniqueness
    - Validate date_of_birth is past date
    - Log patient creation in audit trail
    - _Requirements: 3.1, 3.2, 3.11, 3.12, 3.15_
  
  - [x] 10.3 Implement patient detail endpoint
    - Create GET /api/patients/:id with complete patient data
    - Include current encounter, recent risk predictions, active interventions
    - Return JSONB fields (comorbidities, feature_contributions) properly deserialized
    - _Requirements: 3.5, 3.6_
  
  - [x] 10.4 Implement patient update endpoint
    - Create PUT /api/patients/:id with partial updates
    - Validate updated data (date_of_birth, risk_score range)
    - Log changes to audit trail with before/after values
    - _Requirements: 3.7, 3.8, 3.14_
  
  - [x] 10.5 Write unit tests for patient endpoints
    - Test pagination and filtering logic
    - Test MRN uniqueness validation
    - Test role-based access control (ward isolation)
    - Test error handling for invalid data
    - _Requirements: 3.14_

- [x] 11. Build encounter management endpoints
  - [x] 11.1 Create encounter admission endpoint
    - Implement POST /api/encounters with encounter_type, admission_date
    - Link encounter to patient_id and admitting_provider_id
    - Validate admission_date not in future
    - _Requirements: 1.4_
  
  - [x] 11.2 Create encounter discharge endpoint
    - Implement PUT /api/encounters/:id/discharge
    - Validate discharge_date >= admission_date
    - Update encounter with discharge details
    - Trigger automatic risk prediction on discharge
    - _Requirements: 1.4_
  
  - [x] 11.3 Implement encounter detail endpoint
    - Create GET /api/encounters/:id with related data
    - Include diagnoses, medications, lab_results, social_screening
    - Return risk predictions for the encounter
    - _Requirements: 1.4_

- [x] 12. Implement risk prediction endpoints
  - [x] 12.1 Build prediction generation endpoint
    - Create POST /api/prediction/generate with encounter_id
    - Extract features from encounter using feature engineering module
    - Load active XGBoost ensemble from data/models/
    - Generate 15 predictions and calculate mean + confidence interval
    - Run SHAP explainer for feature contributions
    - Save prediction to risk_predictions table with model_version_id
    - Return risk_score, risk_band (low/medium/high), confidence bounds, and top 10 feature contributions
    - _Requirements: 5.1, 5.2, 9.1, 9.2, 9.10, 9.11_
  
  - [x] 12.2 Build latest risk score query endpoint
    - Create GET /api/prediction/score/:patient_id
    - Query most recent prediction for patient
    - Return 404 if no predictions exist
    - _Requirements: 5.3, 5.4_
  
  - [x] 12.3 Build high-risk patient list endpoint
    - Create GET /api/patients/high-risk
    - Filter patients with risk_score >= 70
    - Order by risk_score descending
    - Include patient details and latest prediction
    - _Requirements: 5.5, 5.6_
  
  - [x] 12.4 Implement what-if analysis endpoint
    - Create POST /api/prediction/what-if with encounter_id and modifications
    - Clone encounter features and apply modifications
    - Generate new prediction with modified features
    - Return original_score, modified_score, and delta
    - _Requirements: 5.11_
  
  - [x] 12.5 Write unit tests for risk prediction
    - Test prediction generation with valid encounter
    - Test handling of missing critical features
    - Test prediction latency < 2 seconds
    - Test SHAP contribution ranking
    - _Requirements: 9.7, 9.12_

- [x] 13. Create alert auto-generation logic
  - [x] 13.1 Implement high-risk alert creation
    - Create alert when risk_score >= 70 after prediction
    - Set alert type="high_risk", severity="high"
    - Assign to patient's primary_provider_id
    - _Requirements: 5.8, 6.10_
  
  - [x] 13.2 Write unit tests for alert generation
    - Test alert created when risk_score >= 70
    - Test no alert when risk_score < 70
    - Test alert assignment to correct provider
    - _Requirements: 5.8_

- [ ] 14. Build frontend authentication pages
  - [ ] 14.1 Create login page
    - Build login form with email and password fields
    - Validate email format and password length client-side
    - Call POST /api/auth/login on submission
    - Store JWT token in secure cookie or localStorage
    - Redirect to dashboard on successful login
    - Display error message "Invalid email or password" on 401
    - _Requirements: 10.1, 10.2, 10.3, 10.6, 10.7_
  
  - [ ] 14.2 Implement token management
    - Store access_token and refresh_token securely
    - Add Authorization header to all API requests
    - Implement automatic token refresh on 401 responses
    - Redirect to login on token expiration
    - Implement automatic logout after 30 minutes of inactivity
    - _Requirements: 10.7, 10.8, 10.13, 10.14_
  
  - [ ] 14.3 Create logout functionality
    - Implement logout button in header
    - Clear authentication tokens
    - Redirect to login page
    - _Requirements: 10.12_

- [ ] 15. Build patient list page (frontend)
  - [ ] 15.1 Create patient list table component
    - Display columns: name, MRN, discharge_date, risk_score, status
    - Implement color-coded risk badges (red >=70, yellow 40-69, green <40)
    - Add pagination controls with configurable page size
    - Make rows clickable to navigate to patient detail page
    - _Requirements: 11.1, 11.4, 11.5, 11.6_
  
  - [ ] 15.2 Implement patient list filtering
    - Add risk level filter dropdown (all/high/medium/low)
    - Add discharge date range picker
    - Add search input for name or MRN
    - Update URL query params on filter change
    - _Requirements: 11.2_
  
  - [ ] 15.3 Add patient list sorting
    - Implement sortable columns (name, discharge_date, risk_score)
    - Show sort direction indicator (up/down arrow)
    - Update query params and refresh data on sort change
    - _Requirements: 11.3_

- [ ] 16. Build patient detail page (frontend)
  - [ ] 16.1 Create patient demographics section
    - Display patient name, MRN, DOB, gender, contact info, address
    - Show current ward and primary provider
    - Display admission and discharge dates
    - _Requirements: 11.7_
  
  - [ ] 16.2 Create risk assessment panel
    - Display current risk_score with color-coded badge
    - Show confidence interval (lower/upper bounds)
    - Render feature contributions as horizontal bar chart (top 10 factors)
    - Add "Generate New Risk Assessment" button
    - Show loading indicator during prediction
    - _Requirements: 11.7, 11.9, 11.10, 11.11_
  
  - [ ] 16.3 Create clinical data display sections
    - Show diagnoses list with ICD-10 codes and descriptions
    - Display active medications table (name, dosage, frequency, route)
    - Show recent lab results with flags (high/low/critical)
    - Display social screening scores
    - _Requirements: 11.7_
  
  - [ ] 16.4 Add error handling and loading states
    - Show loading spinner while fetching patient data
    - Display user-friendly error message on API failure
    - Implement retry button for failed requests
    - _Requirements: 11.11, 11.12_

- [ ] 17. Checkpoint - Verify core functionality
  - Create patient via API and verify in database
  - Create encounter with admission and discharge dates
  - Generate risk prediction and verify risk_score, confidence bounds, SHAP contributions
  - Verify high-risk alert created when risk_score >= 70
  - Test patient list page with filtering, sorting, pagination
  - Test patient detail page displays all clinical data correctly
  - Verify risk assessment panel shows feature contributions chart
  - Test authentication flow and RBAC (ward isolation for non-admin users)

### Phase 3: Interventions & Care Coordination

- [ ] 18. Implement intervention recommendation engine
  - [ ] 18.1 Create rule-based recommender service
    - Define rules: if risk_score >= 70 → recommend "Home health visit", "Medication reconciliation"
    - Define rules: if social_support_score < 3 → recommend "Social work consult"
    - Define rules: if num_medications > 10 → recommend "Pharmacist review"
    - Return ranked list of recommended interventions with rationale
    - _Requirements: 5.8_
  
  - [ ] 18.2 Build intervention recommendation endpoint
    - Create GET /api/interventions/recommend/:encounter_id
    - Apply recommender rules based on patient risk and clinical data
    - Return intervention suggestions with priority ranking
    - _Requirements: 5.8_

- [ ] 19. Build intervention CRUD API endpoints
  - [ ] 19.1 Implement intervention list endpoint
    - Create GET /api/interventions with filtering
    - Support query params: patient_id, status, assigned_to_id, due_date_from, due_date_to
    - Return paginated intervention list
    - _Requirements: 7.1, 7.2_
  
  - [ ] 19.2 Implement intervention creation endpoint
    - Create POST /api/interventions with validation
    - Validate patient_id and encounter_id exist
    - Assign intervention to user (assigned_to_id)
    - Set default status="pending"
    - _Requirements: 7.3, 7.4_
  
  - [ ] 19.3 Implement intervention update endpoint
    - Create PUT /api/interventions/:id
    - Allow status transitions: pending → in_progress → completed/cancelled
    - Validate status transition rules
    - Log updates to audit trail
    - _Requirements: 7.5, 7.6_
  
  - [ ] 19.4 Implement intervention completion endpoint
    - Create PUT /api/interventions/:id/complete
    - Set status="completed" and completed_at timestamp
    - Require outcome_notes in request body
    - _Requirements: 7.6_

- [ ] 20. Build Kanban board task management (frontend)
  - [ ] 20.1 Create Kanban board component with dnd-kit
    - Render columns for statuses: pending, in_progress, completed
    - Display intervention cards with patient name, description, due date
    - Implement drag-and-drop between columns
    - Color-code cards by priority (overdue = red, due soon = yellow)
    - _Requirements: None directly, supports intervention workflow_
  
  - [ ] 20.2 Implement drag-and-drop status updates
    - Handle onDragEnd event to update intervention status
    - Call PUT /api/interventions/:id with new status
    - Show optimistic update (move card immediately)
    - Revert on API error
    - _Requirements: None directly_
  
  - [ ] 20.3 Add intervention detail modal
    - Show full intervention details on card click
    - Display patient link, assigned user, due date, notes
    - Allow editing description and outcome_notes
    - Provide "Complete" button for marking done
    - _Requirements: None directly_

- [ ] 21. Build dashboard page with KPIs (frontend)
  - [ ] 21.1 Create dashboard statistics panel
    - Display cards with key metrics: total_patients, active_encounters, high_risk_count, overdue_interventions, readmission_rate_30d
    - Fetch data from GET /api/dashboard/stats
    - Update metrics every 5 minutes with auto-refresh
    - _Requirements: None directly, supports Requirement 16_
  
  - [ ] 21.2 Create time-series charts for dashboard
    - Render line chart for readmission rate trend (last 12 months)
    - Render bar chart for admissions/discharges by month
    - Render histogram for risk score distribution
    - Use Recharts library for visualizations
    - _Requirements: 16.2, 16.3_
  
  - [ ] 21.3 Add dashboard filtering controls
    - Add date range selector (last 7 days, 30 days, 90 days, custom)
    - Add ward filter dropdown for multi-ward view
    - Update charts and metrics on filter change
    - _Requirements: 16.5_

- [ ] 22. Build what-if analysis UI panel (frontend)
  - [ ] 22.1 Create what-if scenario form
    - Display current feature values for encounter (read-only)
    - Add input fields to modify: num_diagnoses, num_medications, social_support_score, has_follow_up_appointment
    - Add "Calculate Impact" button
    - _Requirements: 5.11_
  
  - [ ] 22.2 Implement what-if visualization
    - Call POST /api/prediction/what-if with modifications
    - Display original_score vs modified_score side-by-side
    - Show delta with color (green if decreased, red if increased)
    - Render bar chart comparing original and modified risk
    - _Requirements: 5.11_

- [ ] 23. Checkpoint - Verify care coordination features
  - Generate intervention recommendations for high-risk patient
  - Create interventions via API and verify in database
  - Test Kanban board drag-and-drop status updates
  - Verify intervention completion updates completed_at timestamp
  - Test dashboard KPI calculations (high_risk_count, overdue_interventions)
  - Test what-if analysis shows accurate risk delta
  - Verify all charts render correctly with sample data

### Phase 4: Intake & Workflow Automation

- [ ] 24. Build patient intake forms (frontend)
  - [ ] 24.1 Create new admission form
    - Build multi-step form: (1) Patient demographics, (2) Encounter details, (3) Diagnoses, (4) Medications, (5) Social screening
    - Validate MRN uniqueness before submission
    - Validate date fields (DOB < today, admission_date <= today)
    - Display progress indicator for multi-step form
    - _Requirements: None directly, supports Requirement 3_
  
  - [ ] 24.2 Implement admission form submission
    - Call POST /api/intake/admission with complete patient data
    - Display success message on creation
    - Navigate to patient detail page on success
    - Handle validation errors with field-level error messages
    - _Requirements: None directly_
  
  - [ ] 24.3 Create discharge form
    - Build form with discharge_date, discharge_disposition, follow-up instructions
    - Pre-populate encounter details (read-only)
    - Validate discharge_date >= admission_date
    - _Requirements: None directly_
  
  - [ ] 24.4 Implement discharge form submission
    - Call POST /api/intake/discharge
    - Automatically trigger risk prediction on discharge
    - Display risk score immediately after discharge
    - Navigate to patient detail page showing new risk assessment
    - _Requirements: None directly_

- [ ] 25. Implement FHIR R4 bundle ingestion
  - [ ] 25.1 Create FHIR resource parser utilities
    - Parse FHIR Patient resource to Patient model
    - Parse FHIR Encounter resource to Encounter model
    - Parse FHIR Condition resource to Diagnosis model
    - Parse FHIR MedicationRequest resource to Medication model
    - Handle missing optional fields gracefully
    - _Requirements: 23.4, 23.5_
  
  - [ ] 25.2 Implement FHIR bundle ingestion endpoint
    - Create POST /api/intake/fhir-bundle
    - Validate FHIR Bundle structure
    - Parse Patient, Encounter, Condition, MedicationRequest resources
    - Create database records in transaction (rollback on error)
    - Return created patient_id, encounter_id, resource counts
    - _Requirements: 23.4_
  
  - [ ] 25.3 Write unit tests for FHIR parsing
    - Test valid FHIR Bundle creates correct database records
    - Test invalid FHIR Bundle returns 400 error
    - Test partial bundle (missing optional resources)
    - Test duplicate MRN handling
    - _Requirements: 23.4_

- [ ] 26. Implement CSV bulk upload with validation
  - [ ] 26.1 Create CSV validation service
    - Validate CSV headers match expected schema
    - Validate required fields are not empty
    - Validate data types (dates, numbers, enums)
    - Validate MRN uniqueness across rows
    - Return detailed error messages with row numbers
    - _Requirements: None directly_
  
  - [ ] 26.2 Implement CSV bulk import endpoint
    - Create POST /api/intake/csv-bulk (multipart/form-data)
    - Parse CSV file with pandas
    - Validate all rows before creating records
    - Create patients in batch transaction
    - Return created_count, failed_count, and error details
    - _Requirements: None directly_
  
  - [ ] 26.3 Write unit tests for CSV import
    - Test valid CSV creates all patients
    - Test CSV with validation errors returns detailed error list
    - Test duplicate MRN handling across rows
    - Test empty file returns appropriate error
    - _Requirements: None directly_

- [ ] 27. Implement follow-up contact tracking
  - [ ] 27.1 Create follow-up contact endpoints
    - Implement POST /api/follow-up-contacts to record contact attempt
    - Implement GET /api/follow-up-contacts?patient_id=X to list contacts
    - Store contact_method, contact_outcome, notes, contacted_by_id, contact_date
    - Allow setting next_contact_date for future follow-up
    - _Requirements: None directly, supports care coordination_
  
  - [ ] 27.2 Build follow-up contact form (frontend)
    - Create modal form for recording follow-up contact
    - Dropdowns for contact_method and contact_outcome
    - Text area for notes
    - Date picker for next_contact_date
    - Display contact history timeline for patient
    - _Requirements: None directly_

- [ ] 28. Implement APScheduler background jobs
  - [ ] 28.1 Set up APScheduler with async support
    - Initialize AsyncIOScheduler in FastAPI lifespan
    - Configure job store (in-memory for development, PostgreSQL for production)
    - Add health check for scheduler status
    - _Requirements: 25.2_
  
  - [ ] 28.2 Create nightly re-scoring job
    - Schedule job daily at 2:00 AM
    - Query encounters discharged within last 30 days
    - Generate fresh risk predictions for each encounter
    - Log re-scoring summary (count, errors)
    - _Requirements: None directly, supports ongoing risk assessment_
  
  - [ ] 28.3 Create hourly overdue check job
    - Schedule job every hour
    - Query interventions with status in (pending, in_progress) and due_date < now
    - Create high-priority notification for assigned user
    - Create critical notification if overdue > 24 hours
    - _Requirements: None directly, supports care coordination_
  
  - [ ] 28.4 Write unit tests for scheduled jobs
    - Test rescore job generates predictions for recent discharges
    - Test overdue check job creates notifications correctly
    - Test job error handling (model unavailable, database error)
    - _Requirements: None directly_

- [ ] 29. Build notification system
  - [ ] 29.1 Create notification CRUD endpoints
    - Implement GET /api/notifications?is_read=false for unread notifications
    - Implement PUT /api/notifications/:id/mark-read
    - Implement GET /api/notifications/unread-count
    - Support filtering by priority, notification_type
    - _Requirements: 14.1, 14.2, 14.3_
  
  - [ ] 29.2 Build notification UI components (frontend)
    - Add notification badge in header showing unread count
    - Create notification dropdown with recent notifications
    - Color-code by priority (critical=red, high=orange, medium=yellow, low=gray)
    - Add "Mark all as read" button
    - Display notification icon based on type
    - _Requirements: 14.1, 14.2, 14.5, 14.12_
  
  - [ ] 29.3 Implement real-time notifications (optional WebSocket)
    - Set up WebSocket connection for logged-in users
    - Push critical notifications in real-time
    - Display browser notification (if permitted)
    - Play audio alert for critical notifications
    - _Requirements: 14.11, 14.12_

- [ ] 30. Checkpoint - Verify workflow automation
  - Test new admission form creates patient, encounter, and related clinical data
  - Test discharge form triggers risk prediction automatically
  - Ingest sample FHIR Bundle and verify database records created
  - Upload sample CSV and verify bulk patient creation
  - Record follow-up contact and verify in database
  - Verify nightly re-scoring job executes and updates predictions
  - Verify overdue check job creates notifications for overdue interventions
  - Test notification badge updates in real-time
  - Verify critical notifications display browser alerts

### Phase 5: Monitoring & Quality Assurance

- [ ] 31. Implement outcome recording
  - [ ] 31.1 Create outcome recording endpoint
    - Implement POST /api/outcomes with validation
    - Validate readmission consistency (if readmitted=true, require readmission_date, days_to_readmission)
    - Calculate days_to_readmission automatically from discharge_date and readmission_date
    - Enforce one outcome per encounter (unique constraint)
    - _Requirements: None directly_
  
  - [ ] 31.2 Create outcome query endpoint
    - Implement GET /api/outcomes/encounter/:encounter_id
    - Return outcome record or null if not recorded
    - _Requirements: None directly_

- [ ] 32. Build model monitoring page (frontend)
  - [ ] 32.1 Implement calibration chart
    - Call GET /api/monitoring/calibration with date range
    - Render calibration curve comparing predicted_rate vs actual_rate by risk band
    - Display scatter plot with diagonal reference line (perfect calibration)
    - Show overall AUROC metric
    - _Requirements: None directly, supports model performance tracking_
  
  - [ ] 32.2 Implement rolling AUROC chart
    - Call GET /api/monitoring/performance?window_days=30
    - Render line chart showing AUROC over time (rolling 30-day window)
    - Display horizontal reference line at AUROC=0.80 threshold
    - Highlight periods where AUROC < 0.75 in red
    - _Requirements: 9.4, 9.5_
  
  - [ ] 32.3 Implement feature drift monitoring
    - Call GET /api/monitoring/drift?feature=age for key features
    - Display PSI (Population Stability Index) score for each feature
    - Show reference distribution vs current distribution as overlaid histograms
    - Flag features with PSI > 0.25 (significant drift)
    - _Requirements: 9.14_

- [ ] 33. Build monitoring API endpoints
  - [ ] 33.1 Implement calibration metrics endpoint
    - Create GET /api/monitoring/calibration?start_date&end_date
    - Query outcomes and predictions for date range
    - Group by risk_band (low/medium/high)
    - Calculate predicted_rate (avg risk_score) and actual_rate (readmission rate) per band
    - Calculate overall AUROC using scikit-learn
    - _Requirements: None directly_
  
  - [ ] 33.2 Implement performance metrics endpoint
    - Create GET /api/monitoring/performance?window_days=30
    - Calculate rolling AUROC with configurable window size
    - Return time-series data: [{ date, auroc, n_predictions }]
    - _Requirements: 9.5_
  
  - [ ] 33.3 Implement drift detection endpoint
    - Create GET /api/monitoring/drift?feature=age
    - Load reference distribution from model training data
    - Calculate current distribution from recent predictions (last 30 days)
    - Compute PSI (Population Stability Index)
    - Return drift_detected flag (PSI > 0.25)
    - _Requirements: 9.14_

- [ ] 34. Implement fairness metrics
  - [ ] 34.1 Build fairness metrics endpoint
    - Create GET /api/fairness/metrics?start_date&end_date
    - Group patients by gender, age_group, race (if available)
    - Calculate per group: avg_risk_score, high_risk_pct, readmission_rate
    - Return metrics for each demographic dimension
    - _Requirements: None directly, supports equitable care_
  
  - [ ] 34.2 Build fairness metrics page (frontend)
    - Display metrics tables by demographic group
    - Highlight groups with >10% difference in high_risk_pct
    - Render bar chart comparing readmission rates across groups
    - Add date range filter
    - _Requirements: None directly_

- [ ] 35. Build model comparison page (frontend)
  - [ ] 35.1 Implement model version management endpoint
    - Create GET /api/model/versions
    - Return list of model versions with metrics (AUROC, precision, recall)
    - Show is_active flag for currently deployed model
    - _Requirements: 9.9, 9.10_
  
  - [ ] 35.2 Implement model activation endpoint
    - Create POST /api/model/activate with version_id
    - Set is_active=true for selected model, false for others
    - Require admin role for this operation
    - Reload model in predictor service
    - _Requirements: 9.10_
  
  - [ ] 35.3 Build model comparison table (frontend)
    - Display table of model versions with metrics
    - Highlight active model
    - Add "Activate" button for non-active models (admin only)
    - Show trained_at timestamp and hyperparameters
    - _Requirements: 9.9, 9.10_

- [ ] 36. Implement care plan generation
  - [ ] 36.1 Build care plan endpoint
    - Create GET /api/careplan/:encounter_id
    - Aggregate patient demographics, encounter details, risk assessment
    - Include diagnoses, medications, interventions, follow-up contacts
    - Generate structured care plan JSON
    - _Requirements: None directly_
  
  - [ ] 36.2 Implement AI care plan draft (Claude API or template)
    - Option A: Call Claude API with patient context to generate care plan text
    - Option B: Use template with patient-specific data insertion
    - Include risk-based recommendations from recommender engine
    - Format as structured sections (goals, medications, appointments, follow-up plan)
    - _Requirements: None directly_
  
  - [ ] 36.3 Build care plan view page (frontend)
    - Display care plan with patient header
    - Show risk assessment summary with key factors
    - List diagnoses, medications, and active interventions
    - Display follow-up plan with scheduled contacts
    - Add "Print" and "Export PDF" buttons
    - _Requirements: None directly_

- [ ] 37. Checkpoint - Verify monitoring and quality features
  - Record outcomes for sample encounters (readmitted and not readmitted)
  - Test calibration chart shows predicted vs actual rates by risk band
  - Verify rolling AUROC chart displays performance over time
  - Test drift detection identifies features with PSI > 0.25
  - Verify fairness metrics show breakdowns by demographic groups
  - Test model version management and activation (admin role)
  - Generate care plan for sample encounter and verify completeness
  - Test AI-generated care plan includes risk-based recommendations

### Phase 6: Testing, Documentation & Polish

- [ ] 38. Write comprehensive backend test suite
  - [ ] 38.1 Write authentication and RBAC tests
    - Test user registration with password hashing
    - Test login success and failure scenarios
    - Test JWT token generation and validation
    - Test token expiration and refresh flow
    - Test rate limiting on login endpoint
    - Test role-based access control for each endpoint
    - Test ward-based data isolation
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.8, 2.9, 2.10, 2.11, 2.12, 2.13, 2.15, 2.16_
  
  - [ ] 38.2 Write patient and encounter endpoint tests
    - Test patient creation with valid and invalid data
    - Test MRN uniqueness validation
    - Test patient list filtering (risk_band, ward_id, search)
    - Test patient list pagination and sorting
    - Test encounter admission and discharge flow
    - Test discharge triggers risk prediction
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.11, 3.12, 3.14, 3.15_
  
  - [ ] 38.3 Write risk prediction tests
    - Test prediction generation with valid encounter
    - Test prediction returns risk_score, confidence interval, feature contributions
    - Test high-risk alert creation when risk_score >= 70
    - Test what-if analysis returns correct delta
    - Test prediction latency < 2 seconds
    - Test handling of missing features
    - _Requirements: 5.1, 5.2, 5.8, 9.7, 9.11, 9.12_
  
  - [ ] 38.4 Write FHIR parsing tests
    - Test FHIR Patient resource maps to Patient model correctly
    - Test FHIR Encounter, Condition, MedicationRequest parsing
    - Test FHIR Bundle ingestion creates correct database records
    - Test invalid FHIR Bundle returns 400 error with details
    - _Requirements: 23.4, 23.5_
  
  - [ ] 38.5 Write intervention and outcome tests
    - Test intervention creation and status transitions
    - Test intervention list filtering
    - Test intervention completion updates completed_at timestamp
    - Test outcome recording with readmission validation
    - Test outcome uniqueness constraint per encounter
    - _Requirements: None directly_
  
  - [ ] 38.6 Write monitoring and fairness tests
    - Test calibration calculation for risk bands
    - Test AUROC calculation
    - Test drift detection (PSI calculation)
    - Test fairness metrics grouping by demographics
    - _Requirements: None directly_
  
  - [ ] 38.7 Write audit logging tests
    - Test audit log creation on patient create/update
    - Test audit logs are immutable
    - Test audit log filtering by user, action, date range
    - Test audit log access restricted to admin role
    - _Requirements: 8.3, 8.4, 8.10, 8.11, 18.5, 18.6, 18.9_

- [ ] 39. Write comprehensive frontend test suite
  - [ ] 39.1 Write component tests for risk visualization
    - Test RiskBadge component displays correct color (red/yellow/green) based on score
    - Test FeatureContributionBars component renders top 10 factors
    - Test contribution bar widths proportional to contribution values
    - Test bar colors (red for increase, blue for decrease)
    - _Requirements: 11.5_
  
  - [ ] 39.2 Write tests for what-if panel
    - Test WhatIfPanel component renders current feature values
    - Test input changes update state correctly
    - Test "Calculate Impact" button calls API with modifications
    - Test result display shows original vs modified risk with delta
    - Test delta color (green=decreased, red=increased)
    - _Requirements: None directly_
  
  - [ ] 39.3 Write tests for Kanban board
    - Test Kanban columns render correctly (pending, in_progress, completed)
    - Test intervention cards display patient name, description, due date
    - Test drag-and-drop updates intervention status
    - Test overdue cards highlighted in red
    - Test card click opens detail modal
    - _Requirements: None directly_
  
  - [ ] 39.4 Write integration tests for dashboard
    - Test dashboard stats load and display correctly
    - Test readmission rate chart renders with time-series data
    - Test risk distribution histogram displays correctly
    - Test date range filter updates metrics
    - _Requirements: 16.1, 16.2, 16.3, 16.5_
  
  - [ ] 39.5 Write tests for authentication flow
    - Test login form validation
    - Test successful login stores token and redirects
    - Test login failure displays error message
    - Test automatic logout after 30 minutes inactivity
    - Test token refresh on 401 response
    - _Requirements: 10.1, 10.2, 10.3, 10.7, 10.8, 10.13, 10.14_

- [ ] 40. Create comprehensive README with demo script
  - [ ] 40.1 Write README with setup instructions
    - Document prerequisites (Docker, Python 3.11, Node.js 18+)
    - Provide step-by-step setup: clone repo, configure .env, run migrations, seed data
    - Document environment variables (DATABASE_URL, SECRET_KEY, etc.)
    - Include troubleshooting section for common issues
    - _Requirements: 24.14_
  
  - [ ] 40.2 Create demo script
    - Provide sample data loading script for realistic demo
    - Document demo flow: login → patient list → patient detail → risk prediction → intervention creation → dashboard
    - Include screenshots or video walkthrough
    - Provide sample API requests with curl/httpie examples
    - _Requirements: None directly_

- [ ] 41. Write technical documentation
  - [ ] 41.1 Create ER diagram documentation
    - Export ER diagram from design document as SVG/PNG
    - Document each table's purpose and relationships
    - Explain foreign key cascade rules
    - Document indexes and their query optimization purpose
    - _Requirements: 1.11, 1.12_
  
  - [ ] 41.2 Create architecture documentation
    - Document three-tier architecture (frontend, backend, database)
    - Explain async SQLAlchemy setup
    - Document ML pipeline flow (feature extraction → prediction → SHAP)
    - Explain background job scheduling
    - Document authentication and RBAC implementation
    - _Requirements: 24.14_
  
  - [ ] 41.3 Create API reference documentation
    - Generate OpenAPI 3.0 spec from FastAPI
    - Document all endpoints with request/response examples
    - Explain authentication headers (JWT Bearer token)
    - Document error response formats
    - Include API versioning information
    - _Requirements: 23.10, 23.11_

- [ ] 42. Final checkpoint - End-to-end testing
  - Run complete test suite (backend pytest, frontend Vitest)
  - Verify all tests pass with >80% code coverage
  - Deploy to staging environment using Docker Compose
  - Execute demo script from README
  - Perform manual testing of all user flows:
    - Nurse logs in → views patient list → filters high-risk patients → views patient detail
    - Doctor generates risk prediction → reviews SHAP contributions → creates intervention
    - Social worker views assigned interventions → updates status on Kanban board
    - Admin views monitoring page → checks calibration → reviews fairness metrics
  - Verify audit logs capture all operations
  - Test error handling (network failures, invalid inputs, 404s)
  - Verify responsive design on mobile/tablet/desktop
  - Test accessibility with keyboard navigation and screen reader
  - Review and address any remaining bugs or UX issues

## Notes

- **Tasks marked with `*` are optional** and can be skipped for faster MVP delivery, though they are recommended for production quality
- **Test-related sub-tasks** (marked with `*`) are optional but provide confidence in implementation correctness
- **Each task references specific requirements** for traceability from requirements to implementation
- **Checkpoints** ensure incremental validation and provide natural pause points for feedback
- **Programming language**: Python (backend), TypeScript/JavaScript (frontend)
- **Primary frameworks**: FastAPI (backend), React 18 (frontend)
- **Database**: PostgreSQL (production), SQLite (development fallback)
- **ML library**: XGBoost with SHAP for explainability
- **All context documents** (requirements.md, design.md) are available during implementation

## Task Dependency Graph

```json
{
  "waves": [
    {
      "id": 0,
      "tasks": ["1.1", "1.2", "1.3"]
    },
    {
      "id": 1,
      "tasks": ["2.1", "2.2", "2.3", "2.4"]
    },
    {
      "id": 2,
      "tasks": ["3.1", "3.2"]
    },
    {
      "id": 3,
      "tasks": ["4.1", "4.2", "4.3"]
    },
    {
      "id": 4,
      "tasks": ["5.1"]
    },
    {
      "id": 5,
      "tasks": ["5.2", "5.3"]
    },
    {
      "id": 6,
      "tasks": ["6.1"]
    },
    {
      "id": 7,
      "tasks": ["6.2", "6.3", "7.1"]
    },
    {
      "id": 8,
      "tasks": ["7.2", "8.1"]
    },
    {
      "id": 9,
      "tasks": ["10.1", "10.2", "10.3", "10.4", "11.1", "11.2", "11.3"]
    },
    {
      "id": 10,
      "tasks": ["10.5"]
    },
    {
      "id": 11,
      "tasks": ["12.1"]
    },
    {
      "id": 12,
      "tasks": ["12.2", "12.3", "12.4", "13.1"]
    },
    {
      "id": 13,
      "tasks": ["12.5", "13.2"]
    },
    {
      "id": 14,
      "tasks": ["14.1"]
    },
    {
      "id": 15,
      "tasks": ["14.2", "14.3"]
    },
    {
      "id": 16,
      "tasks": ["15.1", "15.2", "15.3"]
    },
    {
      "id": 17,
      "tasks": ["16.1", "16.2", "16.3", "16.4"]
    },
    {
      "id": 18,
      "tasks": ["18.1"]
    },
    {
      "id": 19,
      "tasks": ["18.2", "19.1", "19.2"]
    },
    {
      "id": 20,
      "tasks": ["19.3", "19.4"]
    },
    {
      "id": 21,
      "tasks": ["20.1", "20.2", "20.3"]
    },
    {
      "id": 22,
      "tasks": ["21.1", "21.2", "21.3", "22.1", "22.2"]
    },
    {
      "id": 23,
      "tasks": ["24.1", "24.3"]
    },
    {
      "id": 24,
      "tasks": ["24.2", "24.4"]
    },
    {
      "id": 25,
      "tasks": ["25.1"]
    },
    {
      "id": 26,
      "tasks": ["25.2", "25.3"]
    },
    {
      "id": 27,
      "tasks": ["26.1"]
    },
    {
      "id": 28,
      "tasks": ["26.2", "26.3"]
    },
    {
      "id": 29,
      "tasks": ["27.1", "27.2"]
    },
    {
      "id": 30,
      "tasks": ["28.1"]
    },
    {
      "id": 31,
      "tasks": ["28.2", "28.3", "28.4"]
    },
    {
      "id": 32,
      "tasks": ["29.1"]
    },
    {
      "id": 33,
      "tasks": ["29.2", "29.3"]
    },
    {
      "id": 34,
      "tasks": ["31.1", "31.2"]
    },
    {
      "id": 35,
      "tasks": ["32.1", "32.2", "32.3"]
    },
    {
      "id": 36,
      "tasks": ["33.1", "33.2", "33.3"]
    },
    {
      "id": 37,
      "tasks": ["34.1", "34.2"]
    },
    {
      "id": 38,
      "tasks": ["35.1"]
    },
    {
      "id": 39,
      "tasks": ["35.2"]
    },
    {
      "id": 40,
      "tasks": ["35.3"]
    },
    {
      "id": 41,
      "tasks": ["36.1"]
    },
    {
      "id": 42,
      "tasks": ["36.2"]
    },
    {
      "id": 43,
      "tasks": ["36.3"]
    },
    {
      "id": 44,
      "tasks": ["38.1", "38.2", "38.3", "38.4", "38.5", "38.6", "38.7"]
    },
    {
      "id": 45,
      "tasks": ["39.1", "39.2", "39.3", "39.4", "39.5"]
    },
    {
      "id": 46,
      "tasks": ["40.1", "40.2"]
    },
    {
      "id": 47,
      "tasks": ["41.1", "41.2", "41.3"]
    }
  ]
}
```
