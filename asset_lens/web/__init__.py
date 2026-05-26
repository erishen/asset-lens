"""
Web module for asset-lens.
"""

try:
    from .api import app

    __all__ = ["app"]
except ImportError:
    pass
