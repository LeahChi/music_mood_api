from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.models import ListeningSession, Track, User
from app.auth import get_current_user
from app.services.ai_service import interpret_mood, recommend_context

router = APIRouter(
    prefix="/ai",
    tags=["AI Insights"]  # groups AI endpoints in Swagger UI
)

def build_analytics_summary(user_id: int, db: Session) -> dict:
    """
    Queries our own database and builds a structured analytics summary.
    This is what gets sent to the AI — not raw data.
    """

    # get all sessions with track data
    sessions = (
        db.query(ListeningSession, Track)
        .join(Track, ListeningSession.track_id == Track.id)
        .filter(ListeningSession.user_id == user_id)
        .all()
    )

    if not sessions:
        return None

    # compute overall audio feature averages
    valences = [t.valence for _, t in sessions if t.valence is not None]
    energies = [t.energy for _, t in sessions if t.energy is not None]
    danceabilities = [t.danceability for _, t in sessions if t.danceability is not None]

    overall_mood = round(sum(valences) / len(valences), 3) if valences else 0.5
    avg_energy = round(sum(energies) / len(energies), 3) if energies else 0.5
    avg_danceability = round(sum(danceabilities) / len(danceabilities), 3) if danceabilities else 0.5

    # find dominant emotion from mood score and energy
    if overall_mood >= 0.5 and avg_energy >= 0.5:
        dominant_emotion = "Excited"
    elif overall_mood < 0.5 and avg_energy >= 0.5:
        dominant_emotion = "Tense"
    elif overall_mood >= 0.5 and avg_energy < 0.5:
        dominant_emotion = "Calm"
    else:
        dominant_emotion = "Melancholic"

    # find most listened genre
    genre_counts = {}
    for session, track in sessions:
        if track.genre:
            genre_counts[track.genre] = genre_counts.get(track.genre, 0) + 1
    top_genre = max(genre_counts, key=genre_counts.get) if genre_counts else "Unknown"

    # find favourite listening context
    context_counts = {}
    for session, track in sessions:
        ctx = session.context.value
        context_counts[ctx] = context_counts.get(ctx, 0) + 1
    favourite_context = max(context_counts, key=context_counts.get) if context_counts else "other"

    # find most played track
    track_counts = {}
    for session, track in sessions:
        if track.id not in track_counts:
            track_counts[track.id] = {"count": 0, "title": track.title, "artist": track.artist}
        track_counts[track.id]["count"] += 1
    top_track = max(track_counts.values(), key=lambda x: x["count"]) if track_counts else None

    return {
        "overall_mood_score": overall_mood,
        "dominant_emotion": dominant_emotion,
        "avg_energy": avg_energy,
        "avg_danceability": avg_danceability,
        "top_genre": top_genre,
        "favourite_context": favourite_context,
        "total_sessions": len(sessions),
        "top_track_title": top_track["title"] if top_track else "Unknown",
        "top_track_artist": top_track["artist"] if top_track else "Unknown"
    }


@router.get("/interpret/{user_id}")
def interpret_listening(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    The core AI endpoint. Queries our own analytics, then asks
    Llama 3 to interpret the results in natural language.
    Returns a structured JSON response with both the raw analytics
    and the AI-generated interpretation.
    """
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="You can only interpret your own listening data")

    # step 1: build analytics from our own database
    analytics = build_analytics_summary(user_id, db)
    if not analytics:
        raise HTTPException(status_code=404, detail="No listening data found for this user")

    # step 2: send analytics to AI for interpretation
    interpretation = interpret_mood(analytics)

    # step 3: return both the raw analytics AND the AI interpretation
    return {
        "user_id": user_id,
        "analytics_summary": analytics,
        "ai_interpretation": interpretation,
        "disclaimer": "This interpretation is non-clinical and reflects patterns in listening behaviour only. It is not a psychological diagnosis."
    }


@router.get("/recommend/{user_id}")
def recommend_listening_context(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Recommends the best listening context based on the user's
    current mood analytics. Uses AI to personalise the recommendation.
    """
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="You can only get recommendations for your own account")

    analytics = build_analytics_summary(user_id, db)
    if not analytics:
        raise HTTPException(status_code=404, detail="No listening data found for this user")

    recommendation = recommend_context(analytics)

    return {
        "user_id": user_id,
        "current_mood_summary": {
            "mood_score": analytics["overall_mood_score"],
            "dominant_emotion": analytics["dominant_emotion"],
            "favourite_context": analytics["favourite_context"]
        },
        "ai_recommendation": recommendation,
        "disclaimer": "This recommendation is for personal reflection only and is not clinical advice."
    }