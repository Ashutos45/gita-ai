import os
from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, declarative_base


# =====================================
# Base Directory
# =====================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# =====================================
# Database Configuration
# =====================================

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
else:
    DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'gita_ai.db')}"

# =====================================
# STARTUP DIAGNOSTICS
# =====================================
print("APP STARTED")
masked_url = DATABASE_URL
if "://" in DATABASE_URL and "@" in DATABASE_URL:
    try:
        prefix = DATABASE_URL.split("://")[0]
        rest = DATABASE_URL.split("://")[1]
        user_pass = rest.split("@")[0]
        host_db = rest.split("@")[1]
        user = user_pass.split(":")[0]
        masked_url = f"{prefix}://{user}:***@{host_db}"
    except Exception:
        masked_url = "MASKED_URL_ERROR"

print(f"DATABASE URL LOADED: {masked_url}")
print(f"POSTGRES CONNECTED: {'YES' if 'postgres' in masked_url else 'NO'}")

# =====================================
# Engine Configuration
# =====================================

is_sqlite = DATABASE_URL.startswith("sqlite")
connect_args = {"check_same_thread": False, "timeout": 30} if is_sqlite else {"connect_timeout": 3}
pool_kwargs = {} if is_sqlite else {"pool_size": 100, "max_overflow": 50}

try:
    engine = create_engine(
        DATABASE_URL,
        connect_args=connect_args,
        pool_pre_ping=True,   # Avoid stale connections
        echo=False,           # Set True only for debugging
        **pool_kwargs
    )
    print(f"ENGINE DIALECT: {engine.dialect.name}")
except Exception as e:
    print(f"ENGINE CREATION FAILED: {e}")

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if DATABASE_URL.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


# =====================================
# Session Factory
# =====================================

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# =====================================
# Base Model
# =====================================

Base = declarative_base()


# =====================================
# Database Migration Helper
# =====================================

def check_and_run_migrations():
    inspector = inspect(engine)
    if "messages" in inspector.get_table_names():
        columns = [col["name"] for col in inspector.get_columns("messages")]
        
        missing_columns = []
        if "chapter" not in columns:
            missing_columns.append("chapter")
        if "verse_number" not in columns:
            missing_columns.append("verse_number")
        if "verse_id" not in columns:
            missing_columns.append("verse_id")
            
        if missing_columns:
            print(f"Database migration needed. Missing columns in 'messages': {missing_columns}")
            with engine.begin() as conn:
                if "chapter" not in columns:
                    conn.execute(text("ALTER TABLE messages ADD COLUMN chapter INTEGER"))
                if "verse_number" not in columns:
                    conn.execute(text("ALTER TABLE messages ADD COLUMN verse_number INTEGER"))
                if "verse_id" not in columns:
                    conn.execute(text("ALTER TABLE messages ADD COLUMN verse_id INTEGER REFERENCES verses(id) ON DELETE SET NULL"))
            print("Database migration completed successfully.")

    if "users" in inspector.get_table_names():
        u_columns = [col["name"] for col in inspector.get_columns("users")]
        missing_u_columns = []
        if "preferred_language" not in u_columns:
            missing_u_columns.append("preferred_language")
        if "memory_summary" not in u_columns:
            missing_u_columns.append("memory_summary")
            
        if missing_u_columns:
            print(f"Database migration needed. Missing columns in 'users': {missing_u_columns}")
            with engine.begin() as conn:
                if "preferred_language" not in u_columns:
                    conn.execute(text("ALTER TABLE users ADD COLUMN preferred_language VARCHAR(10) DEFAULT 'en'"))
                if "memory_summary" not in u_columns:
                    conn.execute(text("ALTER TABLE users ADD COLUMN memory_summary TEXT"))
            print("Database migration for 'users' completed successfully.")