import os
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool

from models import Base


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"

DATABASE_FILE = DATA_DIR / "averra.db"


# ============================================================
# DATABASE URL
# ============================================================

DATABASE_URL = (
    f"sqlite:///{DATABASE_FILE.as_posix()}"
)


# ============================================================
# CREATE DATA DIRECTORY
# ============================================================

DATA_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# SQLALCHEMY ENGINE
# ============================================================

engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,
    },
    poolclass=StaticPool,
    future=True,
)


# ============================================================
# SESSION FACTORY
# ============================================================

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


# ============================================================
# SCOPED SESSION
# ============================================================

ScopedSession = scoped_session(
    SessionLocal
)


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def init_db():
    """
    Create all database tables defined in models.py.

    Existing tables are not deleted or modified.
    """
    Base.metadata.create_all(
        bind=engine
    )


# ============================================================
# GET SESSION
# ============================================================

def get_session():
    """
    Return a new SQLAlchemy database session.

    Usage:

        session = get_session()

        try:
            ...
        finally:
            session.close()
    """
    return SessionLocal()


# ============================================================
# GET SCOPED SESSION
# ============================================================

def get_scoped_session():
    """
    Return a thread-local scoped SQLAlchemy session.

    Useful if the application needs a session that is reused
    within the same execution context.
    """
    return ScopedSession()


# ============================================================
# CLOSE SCOPED SESSION
# ============================================================

def remove_scoped_session():
    """
    Remove the current scoped session.
    """
    ScopedSession.remove()


# ============================================================
# DATABASE CONNECTION TEST
# ============================================================

def test_connection():
    """
    Test whether the database connection is working.

    Returns:
        True  -> connection successful
        False -> connection failed
    """
    session = None

    try:
        session = get_session()

        session.execute(
            text("SELECT 1")
        )

        return True

    except Exception:
        return False

    finally:
        if session:
            session.close()


# ============================================================
# DATABASE INFORMATION
# ============================================================

def get_database_path():
    """
    Return the absolute SQLite database path.
    """
    return str(
        DATABASE_FILE
    )


def get_database_url():
    """
    Return the SQLAlchemy database URL.
    """
    return DATABASE_URL


def database_exists():
    """
    Check whether the SQLite database file exists.
    """
    return DATABASE_FILE.exists()


def get_database_size():
    """
    Return database size in bytes.
    """
    if not DATABASE_FILE.exists():
        return 0

    try:
        return DATABASE_FILE.stat().st_size

    except OSError:
        return 0


# ============================================================
# DATABASE TABLE INFORMATION
# ============================================================

def get_table_names():
    """
    Return a list of tables currently present in the database.
    """
    try:
        inspector = inspect(
            engine
        )

        return inspector.get_table_names()

    except Exception:
        return []


def table_exists(
    table_name,
):
    """
    Check whether a specific table exists.
    """
    if not table_name:
        return False

    try:
        inspector = inspect(
            engine
        )

        return inspector.has_table(
            table_name
        )

    except Exception:
        return False


# ============================================================
# DATABASE TABLE COUNTS
# ============================================================

def get_table_row_count(
    table_name,
):
    """
    Return the number of rows in a database table.

    The table name is validated against the existing database
    tables before being used in the SQL statement.
    """
    if not table_name:
        return 0

    try:
        tables = get_table_names()

        if table_name not in tables:
            return 0

        with engine.connect() as connection:

            result = connection.execute(
                text(
                    f'SELECT COUNT(*) FROM "{table_name}"'
                )
            )

            return int(
                result.scalar() or 0
            )

    except Exception:
        return 0


def get_database_summary():
    """
    Return basic database information.
    """
    tables = get_table_names()

    table_counts = {}

    for table_name in tables:
        table_counts[
            table_name
        ] = get_table_row_count(
            table_name
        )

    return {
        "database_path": get_database_path(),
        "database_url": get_database_url(),
        "database_exists": database_exists(),
        "database_size_bytes": get_database_size(),
        "tables": tables,
        "table_counts": table_counts,
    }


# ============================================================
# SQLITE PRAGMAS
# ============================================================

def configure_sqlite():
    """
    Configure SQLite for the AVERRA CRM.

    WAL improves reliability for normal application use and
    busy_timeout reduces locking errors.
    """
    session = None

    try:
        session = get_session()

        session.execute(
            text(
                "PRAGMA foreign_keys = ON"
            )
        )

        session.execute(
            text(
                "PRAGMA busy_timeout = 5000"
            )
        )

        session.commit()

    except Exception:
        if session:
            session.rollback()

    finally:
        if session:
            session.close()


# ============================================================
# DATABASE STARTUP
# ============================================================

def initialize_database():
    """
    Complete database startup routine.

    1. Creates the data directory.
    2. Creates missing SQLAlchemy tables.
    3. Configures SQLite.
    """
    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    init_db()

    configure_sqlite()


# ============================================================
# DATABASE RESET
# ============================================================

def reset_database():
    """
    WARNING:
    Deletes all CRM tables and recreates them.

    This should only be used during development/testing.
    """
    Base.metadata.drop_all(
        bind=engine
    )

    Base.metadata.create_all(
        bind=engine
    )


# ============================================================
# DATABASE HEALTH CHECK
# ============================================================

def database_health_check():
    """
    Return a structured database health report.
    """
    connection_ok = test_connection()

    tables = get_table_names()

    return {
        "connection": connection_ok,
        "database_exists": database_exists(),
        "database_path": get_database_path(),
        "tables_count": len(tables),
        "tables": tables,
    }


# ============================================================
# AUTOMATIC INITIALIZATION
# ============================================================

initialize_database()