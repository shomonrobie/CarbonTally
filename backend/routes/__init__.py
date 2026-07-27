# backend/routes/__init__.py
"""
CarbonTally API Routes Package
All route modules are organized by domain and functionality.
"""

from . import waitlist
from . import upload
from . import reports
from . import glossary
from . import users
from . import notifications
from .admin import staff, defra, extraction, reviews
from .organizations import (
    management,
    members,
    assets,
    data,
    analytics,
    dashboard,
    files,
    team
)
from . import documents  # ✅ Add this
from . import drafts
from . import reference  # ✅ Add this
from .admin import assignments  # ✅ Add this



__all__ = [
    # Public/General routes
    'waitlist',
    'upload',
    'reports',
    'glossary',
    'users',
    'notifications',
    
    # Admin routes
    'staff',
    'defra',
    'extraction',
    'reviews',  # ✅ Add this
    # Organization routes
    'management',
    'members',
    'assets',
    'data',
    'analytics',
    'dashboard',
    'files',
    'team',  # ✅ Add this
    'documents',  # ✅ Add this
    'drafts',
    'reference',  # ✅ Add this
    'assignments',  # ✅ Add this
]