# backend/utils/__init__.py
"""
CarbonTally Utilities Package
Shared utility functions for email, emissions calculations, and more.
"""

# Email utilities
from .email import (
    # Core functions
    send_email,
    send_email_from_db_template,
    render_template,
    render_template_subject,
    
    # Existing email functions
    send_invitation_email,
    send_welcome_email,
    send_password_reset_email,
    send_emission_report_email,
    
    # New email functions
    send_beta_invite_email,
    send_feedback_acknowledgement_email,
    send_review_completion_email,
    send_bulk_invite_summary_email,
    
    # Helpers
    log_email,
    validate_email,
)

# Emissions utilities
from .emissions import (
    ACTIVITY_TYPE_MAPPING,
    get_emission_factor,
    get_activity_category,
    calculate_emissions_with_defra,
    process_fuel_data,
    process_utility_data,
    process_scope3_data,
    extract_issues_from_result,
    has_low_confidence,
)
from .document_classifier import (
    classify_document,
)
# Staff workload utilities
from .staff_workload import (
    get_staff_workload,
    get_all_staff_workload,
    get_staff_workload_from_table,
)

# Organization utilities
from .organization_utils import (
    get_organization_name,
    get_organization_by_id,
    get_organization_stats,
    get_facility_stats,
    get_asset_stats,  # ✅ Add this
    get_organization_members,
    get_organization_assets,
)

__all__ = [
    # Email - Core
    'send_email',
    'send_email_from_db_template',
    'render_template',
    'render_template_subject',
    
    # Email - Existing
    'send_invitation_email',
    'send_welcome_email',
    'send_password_reset_email',
    'send_emission_report_email',
    
    # Email - New
    'send_beta_invite_email',
    'send_feedback_acknowledgement_email',
    'send_review_completion_email',
    'send_bulk_invite_summary_email',
    
    # Email - Helpers
    'log_email',
    'validate_email',
    
    # Emissions
    'ACTIVITY_TYPE_MAPPING',
    'get_emission_factor',
    'get_activity_category',
    'calculate_emissions_with_defra',
    'process_fuel_data',
    'process_utility_data',
    'process_scope3_data',
    'extract_issues_from_result',
    'has_low_confidence',
    
    # Staff Workload
    'get_staff_workload',
    'get_all_staff_workload',
    'get_staff_workload_from_table',
    
    # Organization
    'get_organization_name',
    'get_organization_by_id',
    'get_organization_stats',
    'get_facility_stats',
    'get_asset_stats',  # ✅ Add this
    'get_organization_members',
    'get_organization_assets',
    'classify_document',
]