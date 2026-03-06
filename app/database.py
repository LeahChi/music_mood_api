from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Load environment variables from .env file - keeping sensitive info hidden
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./musicmood.db")

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False} # FastAPI handles multiple threads
)

# Each request to the API gets its own session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        # Session is given to the route/caller that requested it
        yield db
    finally:
        db.close()