from fastapi import FastAPI
from app.database import engine, Base
from app.routers import users

# Scans all models and creates the matching tables in musicmood.db
# If the tables already exist, it skips them
Base.metadata.create_all(bind=engine)

# This is the actual API application
# title and description appear in the Swagger UI
app = FastAPI(
    title="MusicMood API",
    description="A music listening analytics API that explores mood-linked and context-aware listening patterns through AI-generated reflective summaries.",
    version="1.0.0"
)
app.include_router(users.router)    # include the authentication routes from users.py

@app.get("/")
def root():
    return {
        "message": "Welcome to MusicMood API",
        "docs": "/docs",        # Swagger UI — all endpoints documented here automatically
        "version": "1.0.0"
    }
