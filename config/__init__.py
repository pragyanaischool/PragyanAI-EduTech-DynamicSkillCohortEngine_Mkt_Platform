"""
Core Configuration & Persistence Package for PragyanAI DemandX.

Provides database connections, schema initialization, mock data seeding,
and centralized environment/runtime settings.
"""

from config.database import get_connection, init_db
from config.seed_data import populate_seed_data
from config.settings import settings

__all__ = [
    "get_connection",
    "init_db",
    "populate_seed_data",
    "settings",
]
