# backend/routes/documents/__init__.py
"""
Documents Routes Package
All document-related endpoints.
"""

from . import activity as document_activity
from . import main as documents_main

__all__ = [
    'document_activity',
    'documents_main',
]