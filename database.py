from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


# ============================================================
# PROJECT PATHS
# ============================================================

# Folder containing this database.py file
BASE_DIR = Path(__file__).resolve().parent

# Database folder
DATA_DIR = BASE_DIR / "data"

# Make sure the data folder exists
DATA_DIR.mkdir(parents=True, exist_ok=True)

# SQLite database file
DATABASE_PATH = DATA_DIR / "averra.db"

# SQLite connection URL
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"


# ============================================================
# DATABASE ENGINE
# ============================================================

engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False
    },
)


# ============================================================
# SESSION
# ============================================================

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# ============================================================
# BASE MODEL
# ============================================================

Base = declarative_base()


# ============================================================
# GET DATABASE SESSION
# ============================================================

def get_session():
    """
    Create and return a new SQLAlchemy database session.
    """
    return SessionLocal()


# ============================================================
# CREATE DATABASE TABLES
# ============================================================

def create_database():
    """
    Create all database tables defined in models.py.
    """
    Base.metadata.create_all(bind=engine)


# ============================================================
# DATABASE INITIALISATION
# ============================================================

if __name__ == "__main__":
    create_database()
    print(f"Database ready: {DATABASE_PATH}")