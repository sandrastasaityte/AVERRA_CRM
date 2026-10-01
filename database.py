import os

from pathlib import Path

from sqlalchemy import (
    create_engine,
    text,
)
from sqlalchemy.orm import (
    declarative_base,
    sessionmaker,
)


# ============================================================
# BASE DIRECTORY
# ============================================================

BASE_DIR = Path(__file__).resolve().parent


# ============================================================
# DATA DIRECTORY
# ============================================================

DATA_DIR = BASE_DIR / "data"

DATA_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# DATABASE FILE
# ============================================================

DATABASE_FILE = DATA_DIR / "averra.db"


# ============================================================
# DATABASE URL
# ============================================================

DATABASE_URL = (
    f"sqlite:///{DATABASE_FILE.as_posix()}"
)


# ============================================================
# SQLALCHEMY BASE
# ============================================================

# IMPORTANT:
# Base is defined here so models.py can safely use:
#
# from database import Base
#
# Do NOT import Base from models.py.
Base = declarative_base()


# ============================================================
# ENGINE
# ============================================================

engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,
    },
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
# CREATE DATABASE
# ============================================================

def create_database():
    """
    Create all database tables.

    models.py is imported inside this function deliberately.
    This prevents a circular import between database.py
    and models.py.
    """

    from models import (
        Client,
        ClientContact,
        Employee,
        EmployeeSkill,
        Job,
        Candidate,
        Activity,
        Placement,
        Contract,
        Invoice,
        Payment,
    )

    Base.metadata.create_all(
        bind=engine
    )

    return True


# ============================================================
# INIT DATABASE
# ============================================================

def init_db():
    """
    Alias for create_database().
    """
    return create_database()


# ============================================================
# GET SESSION
# ============================================================

def get_session():
    """
    Return a new SQLAlchemy database session.

    Screens should use:

        session = get_session()

    and close it when finished.
    """

    return SessionLocal()


# ============================================================
# CLOSE SESSION
# ============================================================

def close_session(
    session,
):
    """
    Safely close a SQLAlchemy session.
    """

    if session is not None:

        try:
            session.close()

        except Exception:
            pass


# ============================================================
# DATABASE CONNECTION TEST
# ============================================================

def test_connection():
    """
    Test whether the SQLite database connection works.
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

        close_session(
            session
        )


# ============================================================
# DATABASE EXISTS
# ============================================================

def database_exists():
    """
    Check whether the SQLite database file exists.
    """

    return DATABASE_FILE.exists()


# ============================================================
# DATABASE PATH
# ============================================================

def get_database_path():
    """
    Return the absolute path to the SQLite database.
    """

    return str(
        DATABASE_FILE
    )


# ============================================================
# DATABASE URL
# ============================================================

def get_database_url():
    """
    Return the SQLAlchemy database URL.
    """

    return DATABASE_URL


# ============================================================
# DATABASE SIZE
# ============================================================

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
# GET TABLE NAMES
# ============================================================

def get_table_names():
    """
    Return all database table names.
    """

    try:

        from sqlalchemy import inspect

        inspector = inspect(
            engine
        )

        return inspector.get_table_names()

    except Exception:

        return []


# ============================================================
# TABLE EXISTS
# ============================================================

def table_exists(
    table_name,
):
    """
    Check whether a database table exists.
    """

    if not table_name:
        return False

    try:

        from sqlalchemy import inspect

        inspector = inspect(
            engine
        )

        return inspector.has_table(
            table_name
        )

    except Exception:

        return False


# ============================================================
# TABLE ROW COUNT
# ============================================================

def get_table_row_count(
    table_name,
):
    """
    Return the number of rows in a table.
    """

    if not table_exists(
        table_name
    ):
        return 0

    session = None

    try:

        session = get_session()

        query = text(
            f'SELECT COUNT(*) FROM "{table_name}"'
        )

        result = session.execute(
            query
        )

        return int(
            result.scalar() or 0
        )

    except Exception:

        return 0

    finally:

        close_session(
            session
        )


# ============================================================
# DATABASE SUMMARY
# ============================================================

def get_database_summary():
    """
    Return basic information about the AVERRA database.
    """

    tables = get_table_names()

    table_counts = {}

    for table in tables:

        table_counts[
            table
        ] = get_table_row_count(
            table
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
# SQLITE CONFIGURATION
# ============================================================

def configure_sqlite():
    """
    Configure SQLite settings for the CRM.
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

        return True

    except Exception:

        if session is not None:

            try:
                session.rollback()

            except Exception:
                pass

        return False

    finally:

        close_session(
            session
        )


# ============================================================
# INITIALIZE DATABASE
# ============================================================

def initialize_database():
    """
    Initialize the AVERRA CRM database.

    This creates the data folder, creates missing tables,
    and configures SQLite.
    """

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    create_database()

    configure_sqlite()

    return True


# ============================================================
# DATABASE HEALTH CHECK
# ============================================================

def database_health_check():
    """
    Return a database health report.
    """

    connection_ok = (
        test_connection()
    )

    tables = get_table_names()

    return {
        "connection": connection_ok,
        "database_exists": database_exists(),
        "database_path": get_database_path(),
        "tables_count": len(tables),
        "tables": tables,
    }


# ============================================================
# RESET DATABASE
# ============================================================

def reset_database():
    """
    WARNING:
    Deletes all existing CRM tables and recreates them.

    Development/testing only.

    Do NOT use this in production because it deletes
    all CRM data.
    """

    from models import (
        Client,
        ClientContact,
        Employee,
        EmployeeSkill,
        Job,
        Candidate,
        Activity,
        Placement,
        Contract,
        Invoice,
        Payment,
    )

    Base.metadata.drop_all(
        bind=engine
    )

    Base.metadata.create_all(
        bind=engine
    )

    configure_sqlite()

    return True