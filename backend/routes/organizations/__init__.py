# backend/routes/organizations/__init__.py
"""
Organization Routes Package
All organization-related endpoints.
"""

from . import management
from . import members
from . import assets
from . import data
from . import analytics
from . import dashboard
from . import files
from . import team

__all__ = [
    'management',
    'members',
    'assets',
    'data',
    'analytics',
    'dashboard',
    'files',
    'team'
]