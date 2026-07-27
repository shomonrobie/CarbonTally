# backend/routes/admin/__init__.py
"""
Admin Routes Package
All admin-related endpoints.
"""

from . import staff
from . import defra
from . import extraction
from . import assignments
from . import permissions
from . import reviews


__all__ = ['staff', 'defra', 'extraction', 'assignments','permissions','reviews' ]