import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL")

# On Vercel, serverless filesystem is read-only except /tmp
if not DATABASE_URL:
    if os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        DATABASE_URL = "sqlite:////tmp/ksb_admin.db"
    else:
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
    print(f"Warning: Failed to connect to {DATABASE_URL} ({e}). Falling back to /tmp SQLite database.")
    DATABASE_URL = "sqlite:////tmp/ksb_admin.db"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
