"""
Core Configuration & Persistence Package for PragyanAI DemandX.
"""

from config.database import get_connection, init_db
from config.seed_data import populate_seed_data
from config.seed_data_extended import populate_extended_seed
from config.settings import settings

__all__ = [
    "get_connection",
    "init_db",
    "populate_seed_data",
    "populate_extended_seed",
    "settings",
]
