"""
MedCode AI -- Database Factory
===============================
Returns the correct database and claim tracker implementation
based on the DATABASE_URL configuration.
"""

from core.config import DATABASE_URL


def get_database():
    """
    Return the appropriate Database instance based on DATABASE_URL.
    PostgreSQL when URL starts with 'postgresql', SQLite otherwise.
    """
    if DATABASE_URL.startswith("postgresql"):
        from storage.postgres_database import PostgresDatabase
        return PostgresDatabase()
    from storage.database import Database
    return Database()


def get_claim_tracker():
    """
    Return the appropriate ClaimTracker instance based on DATABASE_URL.
    PostgreSQL when URL starts with 'postgresql', SQLite otherwise.
    """
    if DATABASE_URL.startswith("postgresql"):
        from billing.postgres_claim_tracker import PostgresClaimTracker
        return PostgresClaimTracker()
    from billing.claim_tracker import ClaimTracker
    return ClaimTracker()
