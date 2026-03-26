# music_mood_api

A music listening analytics API that combines user listening history with real Spotify audio features to generate mood analytics and AI-powered reflective summaries.

> **Live API:** https://musicmoodapi-production.up.railway.app/
> **Swagger Docs:** https://musicmoodapi-production.up.railway.app/docs
> **API Documentation PDF:** [`api_docs.pdf`](api_docs.pdf)
> **Technical Report:** [Link to report]
> **Presentation Slides:** ['presentation'](MusicMood_Presentation.pdf)

---

## Project Overview

MusicMood allows users to log listening sessions against tracks from a 5,000-track database seeded from a real Kaggle Spotify dataset. The system computes mood analytics grounded in Russell's (1980) circumplex model of affect and generates non-clinical, AI-powered reflective summaries using Llama 3.3 70B via the Groq API.

**Stack:** FastAPI · SQLite · SQLAlchemy · JWT (HS256) · Groq API · Railway

---

## Features

- Full CRUD for tracks and listening sessions
- JWT authentication with bcrypt password hashing
- Mood trend analytics derived from Spotify audio features (valence, energy, danceability)
- Context breakdown — listening patterns by context (working, commuting, exercising, etc.)
- Genre emotion map across all users
- AI interpretation endpoint — Llama 3 interprets pre-computed analytics
- AI context recommendation endpoint
- Fallback if Groq API is unavailable
- UI
- Auto-generated Swagger UI at `/docs`

---

## Setup Instructions

### Prerequisites
- Python 3.10+
- pip

### 1. Clone the repository
```bash
git clone https://github.com/LeahChi/music_mood_api.git
cd music_mood_api
```

### 2. Create and activate a virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up environment variables
Create a `.env` file in the root directory:
```
DATABASE_URL=sqlite:///./musicmood.db
SECRET_KEY=your-secret-key-here
GROQ_API_KEY=your-groq-api-key-here
```

> Get a free Groq API key at [console.groq.com](https://console.groq.com)

### 5. Seed the database
```bash
# Seed tracks from Kaggle Spotify dataset
python seed_tracks.py

# Seed demonstration listening sessions
python seed_sessions.py
```

### 6. Run the API
```bash
python -m uvicorn app.main:app --reload
```

The API will be available at:
- **UI:** http://127.0.0.1:8000/ui
- **Swagger docs:** http://127.0.0.1:8000/docs
- **Root:** http://127.0.0.1:8000

---

## API Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/auth/register` | Register a new user | No |
| POST | `/auth/login` | Login and receive JWT token | No |
| GET | `/auth/me` | Get current user info | Yes |
| GET | `/tracks/` | List all tracks | Yes |
| POST | `/tracks/` | Create a track | Yes |
| GET | `/tracks/{id}` | Get a track by ID | Yes |
| PUT | `/tracks/{id}` | Update a track | Yes |
| DELETE | `/tracks/{id}` | Delete a track | Yes |
| POST | `/sessions/` | Log a listening session | Yes |
| GET | `/sessions/{user_id}` | Get user's listening history | Yes |
| DELETE | `/sessions/{id}` | Delete a session | Yes |
| GET | `/analytics/mood-trend/{user_id}` | Mood score over time | Yes |
| GET | `/analytics/context-breakdown/{user_id}` | Listening by context | Yes |
| GET | `/analytics/genre-emotion-map` | Genre → emotion across all users | Yes |
| POST | `/ai/interpret` | AI mood interpretation | Yes |
| GET | `/ai/recommend-context` | AI context recommendation | Yes |

Full documentation: [`api_docs.pdf`](api_docs.pdf)

---

## Project Structure

```
music_mood_api/
├── app/
│   ├── routers/
│   │   ├── ai.py                 # AI interpretation endpoints
│   │   ├── analytics.py          # Analytics computation endpoints
│   │   ├── sessions.py           # Listening session endpoints
│   │   ├── tracks.py             # Track CRUD endpoints
│   │   └── users.py              # Auth endpoints
│   ├── schemas/
│   │   └── schemas.py            # Pydantic request/response schemas
│   ├── services/
│   │   └── ai_service.py         # Groq API integration and fallback logic
│   ├── __init__.py
│   ├── auth.py                   # JWT creation and verification
│   ├── database.py               # SQLite connection and session factory
│   └── main.py                   # FastAPI app, startup, global error handlers
├── static/
│   └── musicmood_ui.html         # Frontend UI served from FastAPI
├── .env                          # Not committed — see setup instructions
├── .gitignore
├── api_docs.pdf                  # API documentation
├── MusicMood_Presentation.pdf    # Presentation slides
├── Procfile                      # Railway deployment config
├── requirements.txt
├── runtime.txt                   # Python version for Railway
├── seed_sessions.py              # Seeds demonstration listening sessions
├── seed_tracks.py                # Seeds 5,000 tracks from Kaggle dataset
├── spotify_tracks_dataset.csv    # Kaggle dataset
└── TechnicalReport_201698979.pdf # Technical report

```

---

## Deployment

Deployed on Railway. The `Procfile` configures the ASGI server:
```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

---

## Data Sources

- **Spotify Tracks Dataset** — Pandya, M. (2023). Kaggle. [Link](https://www.kaggle.com/datasets/maharshipandya/-spotify-tracks-dataset)
- Audio features (valence, energy, danceability) sourced from Spotify Web API

## Academic References

- Russell, J.A. (1980) 'A circumplex model of affect', *Journal of Personality and Social Psychology*, 39(6), pp. 1161–1178
- Schäfer, T. et al. (2013) 'The psychological functions of music listening', *Frontiers in Psychology*, 4, p. 511

---

## Disclaimer

AI-generated mood interpretations are non-clinical and reflective only. The system makes no diagnostic claims and is not a substitute for professional mental health support.
