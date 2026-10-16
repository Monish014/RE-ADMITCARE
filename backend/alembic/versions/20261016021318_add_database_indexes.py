"""add_database_indexes

Revision ID: 20261016021318
Revises: 
Create Date: 2026-10-16 02:13:18.000000

This migration adds composite and single-column indexes for common query patterns,
pagination, filtering, sorting, and join performance optimization.

Indexes are created for:
- patients: mrn, current_ward_id, primary_provider_id, last_name
- encounters: patient_id, admission_date, discharge_date, encounter_type
- risk_predictions: patient_id, encounter_id, risk_score (DESC), risk_band, predicted_at (DESC)
- interventions: patient_id, status, assigned_to_id, due_date
- notifications: user_id, is_read, created_at (DESC), priority
- audit_logs: user_id, resource_type, resource_id, created_at (DESC), action
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20261016021318'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add indexes for common query patterns, pagination, filtering, and sorting.
    Indexes on foreign keys improve join performance.
    """
    
    # ====================================================================
    # PATIENTS TABLE INDEXES
    # ====================================================================
    
    # Single-column indexes for filtering and lookups
    op.create_index(
        'idx_patients_mrn',
        'patients',
        ['mrn'],
        unique=False
    )
    
    op.create_index(
        'idx_patients_last_name',
        'patients',
        ['last_name'],
        unique=False
    )
    
    # Foreign key indexes for join performance
    op.create_index(
        'idx_patients_current_ward_id',
        'patients',
        ['current_ward_id'],
        unique=False
    )
    
    op.create_index(
        'idx_patients_primary_provider_id',
        'patients',
        ['primary_provider_id'],
        unique=False
    )
    
    # Composite index for common query pattern: filtering by ward and sorting by last_name
    op.create_index(
        'idx_patients_ward_lastname',
        'patients',
        ['current_ward_id', 'last_name'],
        unique=False
    )
    
    # ====================================================================
    # ENCOUNTERS TABLE INDEXES
    # ====================================================================
    
    # Foreign key index for joins
    op.create_index(
        'idx_encounters_patient_id',
        'encounters',
        ['patient_id'],
        unique=False
    )
    
    # Indexes for date filtering and sorting
    op.create_index(
        'idx_encounters_admission_date',
        'encounters',
        ['admission_date'],
        unique=False
    )
    
    op.create_index(
        'idx_encounters_discharge_date',
        'encounters',
        ['discharge_date'],
        unique=False
    )
    
    # Index for encounter type filtering
    op.create_index(
        'idx_encounters_encounter_type',
        'encounters',
        ['encounter_type'],
        unique=False
    )
    
    # Composite index for common query: patient's encounters ordered by admission date
    op.create_index(
        'idx_encounters_patient_admission',
        'encounters',
        ['patient_id', 'admission_date'],
        unique=False
    )
    
    # Composite index for recent discharges (common for risk re-scoring)
    op.create_index(
        'idx_encounters_discharge_date_desc',
        'encounters',
        [sa.text('discharge_date DESC')],
        unique=False,
        postgresql_using='btree'
    )
    
    # ====================================================================
    # RISK_PREDICTIONS TABLE INDEXES
    # ====================================================================
    
    # Foreign key indexes
    op.create_index(
        'idx_risk_predictions_patient_id',
        'risk_predictions',
        ['patient_id'],
        unique=False
    )
    
    op.create_index(
        'idx_risk_predictions_encounter_id',
        'risk_predictions',
        ['encounter_id'],
        unique=False
    )
    
    # Index for high-risk filtering (DESC for sorting)
    op.create_index(
        'idx_risk_predictions_risk_score',
        'risk_predictions',
        [sa.text('risk_score DESC')],
        unique=False,
        postgresql_using='btree'
    )
    
    # Index for risk band filtering
    op.create_index(
        'idx_risk_predictions_risk_band',
        'risk_predictions',
        ['risk_band'],
        unique=False
    )
    
    # Index for temporal queries (DESC for recent predictions first)
    op.create_index(
        'idx_risk_predictions_predicted_at',
        'risk_predictions',
        [sa.text('predicted_at DESC')],
        unique=False,
        postgresql_using='btree'
    )
    
    # Foreign key index for model version tracking
    op.create_index(
        'idx_risk_predictions_model_version_id',
        'risk_predictions',
        ['model_version_id'],
        unique=False
    )
    
    # Composite index for patient's latest prediction
    op.create_index(
        'idx_risk_predictions_patient_predicted',
        'risk_predictions',
        ['patient_id', sa.text('predicted_at DESC')],
        unique=False,
        postgresql_using='btree'
    )
    
    # Composite index for high-risk patients by risk band and score
    op.create_index(
        'idx_risk_predictions_band_score',
        'risk_predictions',
        ['risk_band', sa.text('risk_score DESC')],
        unique=False,
        postgresql_using='btree'
    )
    
    # ====================================================================
    # INTERVENTIONS TABLE INDEXES
    # ====================================================================
    
    # Foreign key index
    op.create_index(
        'idx_interventions_patient_id',
        'interventions',
        ['patient_id'],
        unique=False
    )
    
    op.create_index(
        'idx_interventions_encounter_id',
        'interventions',
        ['encounter_id'],
        unique=False
    )
    
    # Index for status filtering (Kanban board queries)
    op.create_index(
        'idx_interventions_status',
        'interventions',
        ['status'],
        unique=False
    )
    
    # Index for user assignment filtering
    op.create_index(
        'idx_interventions_assigned_to_id',
        'interventions',
        ['assigned_to_id'],
        unique=False
    )
    
    # Index for due date sorting and overdue checks
    op.create_index(
        'idx_interventions_due_date',
        'interventions',
        ['due_date'],
        unique=False
    )
    
    # Composite index for user's tasks by status
    op.create_index(
        'idx_interventions_assigned_status',
        'interventions',
        ['assigned_to_id', 'status'],
        unique=False
    )
    
    # Composite index for overdue intervention checks
    op.create_index(
        'idx_interventions_status_due_date',
        'interventions',
        ['status', 'due_date'],
        unique=False
    )
    
    # ====================================================================
    # NOTIFICATIONS TABLE INDEXES
    # ====================================================================
    
    # Foreign key indexes
    op.create_index(
        'idx_notifications_user_id',
        'notifications',
        ['user_id'],
        unique=False
    )
    
    op.create_index(
        'idx_notifications_patient_id',
        'notifications',
        ['patient_id'],
        unique=False
    )
    
    # Index for read/unread filtering
    op.create_index(
        'idx_notifications_is_read',
        'notifications',
        ['is_read'],
        unique=False
    )
    
    # Index for priority filtering
    op.create_index(
        'idx_notifications_priority',
        'notifications',
        ['priority'],
        unique=False
    )
    
    # Index for temporal sorting (DESC for recent first)
    op.create_index(
        'idx_notifications_created_at',
        'notifications',
        [sa.text('created_at DESC')],
        unique=False,
        postgresql_using='btree'
    )
    
    # Composite index for unread notifications by user
    op.create_index(
        'idx_notifications_user_unread',
        'notifications',
        ['user_id', 'is_read'],
        unique=False
    )
    
    # Composite index for user's notifications sorted by created date
    op.create_index(
        'idx_notifications_user_created',
        'notifications',
        ['user_id', sa.text('created_at DESC')],
        unique=False,
        postgresql_using='btree'
    )
    
    # Composite index for high-priority unread notifications
    op.create_index(
        'idx_notifications_priority_unread',
        'notifications',
        ['priority', 'is_read', sa.text('created_at DESC')],
        unique=False,
        postgresql_using='btree'
    )
    
    # ====================================================================
    # AUDIT_LOGS TABLE INDEXES
    # ====================================================================
    
    # Foreign key index
    op.create_index(
        'idx_audit_logs_user_id',
        'audit_logs',
        ['user_id'],
        unique=False
    )
    
    # Index for resource type filtering
    op.create_index(
        'idx_audit_logs_resource_type',
        'audit_logs',
        ['resource_type'],
        unique=False
    )
    
    # Index for resource ID filtering
    op.create_index(
        'idx_audit_logs_resource_id',
        'audit_logs',
        ['resource_id'],
        unique=False
    )
    
    # Index for action filtering
    op.create_index(
        'idx_audit_logs_action',
        'audit_logs',
        ['action'],
        unique=False
    )
    
    # Index for temporal queries (DESC for recent first)
    op.create_index(
        'idx_audit_logs_created_at',
        'audit_logs',
        [sa.text('created_at DESC')],
        unique=False,
        postgresql_using='btree'
    )
    
    # Composite index for user's audit trail
    op.create_index(
        'idx_audit_logs_user_created',
        'audit_logs',
        ['user_id', sa.text('created_at DESC')],
        unique=False,
        postgresql_using='btree'
    )
    
    # Composite index for resource audit trail
    op.create_index(
        'idx_audit_logs_resource_created',
        'audit_logs',
        ['resource_type', 'resource_id', sa.text('created_at DESC')],
        unique=False,
        postgresql_using='btree'
    )
    
    # ====================================================================
    # ADDITIONAL COMMON TABLES (based on design document)
    # ====================================================================
    
    # USERS TABLE
    op.create_index(
        'idx_users_email',
        'users',
        ['email'],
        unique=False
    )
    
    op.create_index(
        'idx_users_role',
        'users',
        ['role'],
        unique=False
    )
    
    op.create_index(
        'idx_users_ward_id',
        'users',
        ['ward_id'],
        unique=False
    )
    
    # DIAGNOSES TABLE
    op.create_index(
        'idx_diagnoses_patient_id',
        'diagnoses',
        ['patient_id'],
        unique=False
    )
    
    op.create_index(
        'idx_diagnoses_encounter_id',
        'diagnoses',
        ['encounter_id'],
        unique=False
    )
    
    op.create_index(
        'idx_diagnoses_icd10_code',
        'diagnoses',
        ['icd10_code'],
        unique=False
    )
    
    op.create_index(
        'idx_diagnoses_is_primary',
        'diagnoses',
        ['is_primary'],
        unique=False
    )
    
    # MEDICATIONS TABLE
    op.create_index(
        'idx_medications_patient_id',
        'medications',
        ['patient_id'],
        unique=False
    )
    
    op.create_index(
        'idx_medications_encounter_id',
        'medications',
        ['encounter_id'],
        unique=False
    )
    
    op.create_index(
        'idx_medications_start_date',
        'medications',
        ['start_date'],
        unique=False
    )
    
    op.create_index(
        'idx_medications_end_date',
        'medications',
        ['end_date'],
        unique=False
    )
    
    # LAB_RESULTS TABLE
    op.create_index(
        'idx_lab_results_patient_id',
        'lab_results',
        ['patient_id'],
        unique=False
    )
    
    op.create_index(
        'idx_lab_results_encounter_id',
        'lab_results',
        ['encounter_id'],
        unique=False
    )
    
    op.create_index(
        'idx_lab_results_test_code',
        'lab_results',
        ['test_code'],
        unique=False
    )
    
    op.create_index(
        'idx_lab_results_result_date',
        'lab_results',
        ['result_date'],
        unique=False
    )
    
    op.create_index(
        'idx_lab_results_flag',
        'lab_results',
        ['flag'],
        unique=False
    )
    
    # SOCIAL_SCREENINGS TABLE
    op.create_index(
        'idx_social_screenings_patient_id',
        'social_screenings',
        ['patient_id'],
        unique=False
    )
    
    op.create_index(
        'idx_social_screenings_encounter_id',
        'social_screenings',
        ['encounter_id'],
        unique=False
    )
    
    op.create_index(
        'idx_social_screenings_screened_at',
        'social_screenings',
        ['screened_at'],
        unique=False
    )
    
    # FOLLOW_UP_CONTACTS TABLE
    op.create_index(
        'idx_follow_up_contacts_patient_id',
        'follow_up_contacts',
        ['patient_id'],
        unique=False
    )
    
    op.create_index(
        'idx_follow_up_contacts_encounter_id',
        'follow_up_contacts',
        ['encounter_id'],
        unique=False
    )
    
    op.create_index(
        'idx_follow_up_contacts_contact_date',
        'follow_up_contacts',
        [sa.text('contact_date DESC')],
        unique=False,
        postgresql_using='btree'
    )
    
    op.create_index(
        'idx_follow_up_contacts_next_contact_date',
        'follow_up_contacts',
        ['next_contact_date'],
        unique=False
    )
    
    # OUTCOMES TABLE
    op.create_index(
        'idx_outcomes_patient_id',
        'outcomes',
        ['patient_id'],
        unique=False
    )
    
    op.create_index(
        'idx_outcomes_encounter_id',
        'outcomes',
        ['encounter_id'],
        unique=False
    )
    
    op.create_index(
        'idx_outcomes_readmitted',
        'outcomes',
        ['readmitted'],
        unique=False
    )
    
    op.create_index(
        'idx_outcomes_outcome_date',
        'outcomes',
        [sa.text('outcome_date DESC')],
        unique=False,
        postgresql_using='btree'
    )
    
    # MODEL_VERSIONS TABLE
    op.create_index(
        'idx_model_versions_is_active',
        'model_versions',
        ['is_active'],
        unique=False
    )
    
    op.create_index(
        'idx_model_versions_trained_at',
        'model_versions',
        [sa.text('trained_at DESC')],
        unique=False,
        postgresql_using='btree'
    )
    
    # WARDS TABLE
    op.create_index(
        'idx_wards_name',
        'wards',
        ['name'],
        unique=True
    )


def downgrade() -> None:
    """
    Remove all indexes created in the upgrade function.
    """
    
    # WARDS TABLE
    op.drop_index('idx_wards_name', table_name='wards')
    
    # MODEL_VERSIONS TABLE
    op.drop_index('idx_model_versions_trained_at', table_name='model_versions')
    op.drop_index('idx_model_versions_is_active', table_name='model_versions')
    
    # OUTCOMES TABLE
    op.drop_index('idx_outcomes_outcome_date', table_name='outcomes')
    op.drop_index('idx_outcomes_readmitted', table_name='outcomes')
    op.drop_index('idx_outcomes_encounter_id', table_name='outcomes')
    op.drop_index('idx_outcomes_patient_id', table_name='outcomes')
    
    # FOLLOW_UP_CONTACTS TABLE
    op.drop_index('idx_follow_up_contacts_next_contact_date', table_name='follow_up_contacts')
    op.drop_index('idx_follow_up_contacts_contact_date', table_name='follow_up_contacts')
    op.drop_index('idx_follow_up_contacts_encounter_id', table_name='follow_up_contacts')
    op.drop_index('idx_follow_up_contacts_patient_id', table_name='follow_up_contacts')
    
    # SOCIAL_SCREENINGS TABLE
    op.drop_index('idx_social_screenings_screened_at', table_name='social_screenings')
    op.drop_index('idx_social_screenings_encounter_id', table_name='social_screenings')
    op.drop_index('idx_social_screenings_patient_id', table_name='social_screenings')
    
    # LAB_RESULTS TABLE
    op.drop_index('idx_lab_results_flag', table_name='lab_results')
    op.drop_index('idx_lab_results_result_date', table_name='lab_results')
    op.drop_index('idx_lab_results_test_code', table_name='lab_results')
    op.drop_index('idx_lab_results_encounter_id', table_name='lab_results')
    op.drop_index('idx_lab_results_patient_id', table_name='lab_results')
    
    # MEDICATIONS TABLE
    op.drop_index('idx_medications_end_date', table_name='medications')
    op.drop_index('idx_medications_start_date', table_name='medications')
    op.drop_index('idx_medications_encounter_id', table_name='medications')
    op.drop_index('idx_medications_patient_id', table_name='medications')
    
    # DIAGNOSES TABLE
    op.drop_index('idx_diagnoses_is_primary', table_name='diagnoses')
    op.drop_index('idx_diagnoses_icd10_code', table_name='diagnoses')
    op.drop_index('idx_diagnoses_encounter_id', table_name='diagnoses')
    op.drop_index('idx_diagnoses_patient_id', table_name='diagnoses')
    
    # USERS TABLE
    op.drop_index('idx_users_ward_id', table_name='users')
    op.drop_index('idx_users_role', table_name='users')
    op.drop_index('idx_users_email', table_name='users')
    
    # AUDIT_LOGS TABLE
    op.drop_index('idx_audit_logs_resource_created', table_name='audit_logs')
    op.drop_index('idx_audit_logs_user_created', table_name='audit_logs')
    op.drop_index('idx_audit_logs_created_at', table_name='audit_logs')
    op.drop_index('idx_audit_logs_action', table_name='audit_logs')
    op.drop_index('idx_audit_logs_resource_id', table_name='audit_logs')
    op.drop_index('idx_audit_logs_resource_type', table_name='audit_logs')
    op.drop_index('idx_audit_logs_user_id', table_name='audit_logs')
    
    # NOTIFICATIONS TABLE
    op.drop_index('idx_notifications_priority_unread', table_name='notifications')
    op.drop_index('idx_notifications_user_created', table_name='notifications')
    op.drop_index('idx_notifications_user_unread', table_name='notifications')
    op.drop_index('idx_notifications_created_at', table_name='notifications')
    op.drop_index('idx_notifications_priority', table_name='notifications')
    op.drop_index('idx_notifications_is_read', table_name='notifications')
    op.drop_index('idx_notifications_patient_id', table_name='notifications')
    op.drop_index('idx_notifications_user_id', table_name='notifications')
    
    # INTERVENTIONS TABLE
    op.drop_index('idx_interventions_status_due_date', table_name='interventions')
    op.drop_index('idx_interventions_assigned_status', table_name='interventions')
    op.drop_index('idx_interventions_due_date', table_name='interventions')
    op.drop_index('idx_interventions_assigned_to_id', table_name='interventions')
    op.drop_index('idx_interventions_status', table_name='interventions')
    op.drop_index('idx_interventions_encounter_id', table_name='interventions')
    op.drop_index('idx_interventions_patient_id', table_name='interventions')
    
    # RISK_PREDICTIONS TABLE
    op.drop_index('idx_risk_predictions_band_score', table_name='risk_predictions')
    op.drop_index('idx_risk_predictions_patient_predicted', table_name='risk_predictions')
    op.drop_index('idx_risk_predictions_model_version_id', table_name='risk_predictions')
    op.drop_index('idx_risk_predictions_predicted_at', table_name='risk_predictions')
    op.drop_index('idx_risk_predictions_risk_band', table_name='risk_predictions')
    op.drop_index('idx_risk_predictions_risk_score', table_name='risk_predictions')
    op.drop_index('idx_risk_predictions_encounter_id', table_name='risk_predictions')
    op.drop_index('idx_risk_predictions_patient_id', table_name='risk_predictions')
    
    # ENCOUNTERS TABLE
    op.drop_index('idx_encounters_discharge_date_desc', table_name='encounters')
    op.drop_index('idx_encounters_patient_admission', table_name='encounters')
    op.drop_index('idx_encounters_encounter_type', table_name='encounters')
    op.drop_index('idx_encounters_discharge_date', table_name='encounters')
    op.drop_index('idx_encounters_admission_date', table_name='encounters')
    op.drop_index('idx_encounters_patient_id', table_name='encounters')
    
    # PATIENTS TABLE
    op.drop_index('idx_patients_ward_lastname', table_name='patients')
    op.drop_index('idx_patients_primary_provider_id', table_name='patients')
    op.drop_index('idx_patients_current_ward_id', table_name='patients')
    op.drop_index('idx_patients_last_name', table_name='patients')
    op.drop_index('idx_patients_mrn', table_name='patients')
