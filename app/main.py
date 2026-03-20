from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from app.database import engine, Base
from app.routers import users, tracks, sessions, analytics, ai
from fastapi.middleware.cors import CORSMiddleware



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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # allows any origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# serve the UI files through FastAPI so the browser can load JS files properly
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/ui")
def serve_ui():
    return FileResponse("static/musicmood_ui.html")

# --- Global Error Handlers ---
# These catch errors across ALL endpoints automatically
# Without these, FastAPI returns messy HTML errors instead of clean JSON

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Fires whenever a request fails Pydantic validation
    # e.g. missing required field, wrong data type, failed validator
    # Returns a clean JSON response telling the user exactly what went wrong
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "detail": "One or more fields are invalid.",
            "fields": [
                {
                    "field": err["loc"][-1],   # the name of the field that failed e.g. "username"
                    "message": err["msg"]      # why it failed
                }
                for err in exc.errors()
            ]
        }
    )

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    # Fires whenever someone hits an endpoint that doesn't exist
    # Returns clean JSON instead of the default "Not Found" HTML page
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "detail": f"The requested resource was not found: {request.url.path}"
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    # Fires whenever something unexpected crashes inside the code
    # Hides the internal error details from the user and returns a cleaner one
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": "An unexpected error occurred. Please try again later."
        }
    )

app.include_router(users.router)     # include the authentication routes from users.py
app.include_router(tracks.router)    # include the track management routes from tracks.py
app.include_router(sessions.router)  # include the listening session routes from sessions.py
app.include_router(analytics.router) # include the analytics routes from analytics.py
app.include_router(ai.router)        # include the AI insights routes from ai.py


@app.get("/")
def root():
    return FileResponse("static/musicmood_ui.html")
        # "docs": "/docs",        # Swagger UI — all endpoints documented here automatically
    
