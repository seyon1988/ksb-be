import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL")

# If no explicit DATABASE_URL env var, try local sqlite or fallback
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./ksb_admin.db"

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine_kwargs = {}
if "sqlite" in DATABASE_URL:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs["pool_pre_ping"] = True

try:
    engine = create_engine(DATABASE_URL, **engine_kwargs)
    # Test connection
    with engine.connect() as conn:
        pass
except Exception as e:
    print(f"Warning: Failed to connect to {DATABASE_URL} ({e}). Falling back to local SQLite database.")
    DATABASE_URL = "sqlite:///./ksb_admin.db"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
