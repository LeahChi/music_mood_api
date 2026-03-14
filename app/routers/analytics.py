from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from app.database import get_db
from app.models.models import ListeningSession, Track, User, ListeningContext
from app.auth import get_current_user   
from collections import Counter

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"]  # groups endpoints together in Swagger UI
)

def compute_emotion (valence: float, energy: float) -> str:
    """ Mapping valence and energy, based on Russell's circumplex model of affect:
    high valence + high energy = happy
    low valence + high energy = tense
    low valence + low energy = melancholic
    high valence + low energy = calm"""
    if valence >= 0.5 and energy >= 0.5:
        return "Happy"
    elif valence < 0.5 and energy >= 0.5:
        return "Tense"
    elif valence < 0.5 and energy < 0.5:
        return "Melancholic"
    else:
        return "Calm"
    

# --- Endpoint 1: Mood trend over time ---
# Mood score = average valence of tracks listened to each day
@router.get("/mood-trend/{user_id}")
def get_mood_trend(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # users can only view their own mood trend
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="You can only view your own mood trend")

    # get all sessions for this user, joined with track data
    sessions = (
        db.query(ListeningSession, Track)
        .join(Track, ListeningSession.track_id == Track.id)
        .filter(ListeningSession.user_id == user_id)
        .order_by(ListeningSession.listened_at)
        .all()
    )

    if not sessions:
        raise HTTPException(status_code=404, detail="No listening sessions found for this user")

    # group sessions by date and compute average valence per day
    daily_data = {}
    for session, track in sessions:
        date_key = session.listened_at.strftime("%Y-%m-%d")  # group by day
        if date_key not in daily_data:
            daily_data[date_key] = []
        if track.valence is not None:
            daily_data[date_key].append(track.valence)

    # build the trend — one entry per day
    trend = []
    for date, valences in sorted(daily_data.items()):
        avg_valence = sum(valences) / len(valences)
        trend.append({
            "date": date,
            "mood_score": round(avg_valence, 3),                    # average valence for that day
            "dominant_emotion": compute_emotion(avg_valence, 0.5),  # map to emotion label
            "sessions_count": len(valences)                         # how many tracks that day
        })

    return {
        "user_id": user_id,
        "mood_trend": trend,
        "overall_mood_score": round(sum(v for vals in daily_data.values() for v in vals) / sum(len(v) for v in daily_data.values()), 3)
    }

# --- Endpoint 2: Context breakdown ---
# Shows what contexts the user listens to music in
# e.g. 40% working, 30% commuting, 20% exercising etc
@router.get("/context-breakdown/{user_id}")
def get_context_breakdown(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="You can only view your own context breakdown")

    # count sessions per context for this user
    sessions = (
        db.query(ListeningSession)
        .filter(ListeningSession.user_id == user_id)
        .all()
    )

    if not sessions:
        raise HTTPException(status_code=404, detail="No listening sessions found for this user")

    # count how many sessions per context
    context_counts = Counter(session.context.value for session in sessions)
    total = sum(context_counts.values())

    # build breakdown with counts and percentages
    breakdown = []
    for context, count in context_counts.most_common():
        breakdown.append({
            "context": context,
            "count": count,
            "percentage": round((count / total) * 100, 1)  # percentage of total sessions
        })

    # compute average audio features per context
    # e.g. "when working, you listen to calmer music"
    context_features = {}
    for session in sessions:
        ctx = session.context.value
        track = db.query(Track).filter(Track.id == session.track_id).first()
        if track and track.valence is not None:
            if ctx not in context_features:
                context_features[ctx] = {"valence": [], "energy": [], "danceability": []}
            context_features[ctx]["valence"].append(track.valence)
            context_features[ctx]["energy"].append(track.energy)
            context_features[ctx]["danceability"].append(track.danceability)

    # add average features to each context
    for item in breakdown:
        ctx = item["context"]
        if ctx in context_features:
            features = context_features[ctx]
            item["avg_valence"] = round(sum(features["valence"]) / len(features["valence"]), 3)
            item["avg_energy"] = round(sum(features["energy"]) / len(features["energy"]), 3)
            item["avg_danceability"] = round(sum(features["danceability"]) / len(features["danceability"]), 3)
            item["typical_emotion"] = compute_emotion(item["avg_valence"], item["avg_energy"])

    return {
        "user_id": user_id,
        "total_sessions": total,
        "context_breakdown": breakdown
    }

# --- Endpoint 3: Genre emotion map ---
# Shows which emotions are associated with each genre across ALL users
# Not user specific! It's a global insight.
@router.get("/genre-emotion-map")
def get_genre_emotion_map(db: Session = Depends(get_db)):

    # get all tracks that have been listened to, with their genre and features
    listened_tracks = (
        db.query(Track)
        .join(ListeningSession, Track.id == ListeningSession.track_id)
        .filter(Track.genre.isnot(None))
        .all()
    )

    if not listened_tracks:
        raise HTTPException(status_code=404, detail="No listening data found")

    # group audio features by genre
    genre_data = {}
    for track in listened_tracks:
        genre = track.genre
        if genre not in genre_data:
            genre_data[genre] = {"valence": [], "energy": [], "danceability": [], "tempo": []}
        if track.valence is not None:
            genre_data[genre]["valence"].append(track.valence)
            genre_data[genre]["energy"].append(track.energy)
            genre_data[genre]["danceability"].append(track.danceability)
            genre_data[genre]["tempo"].append(track.tempo)

    # compute averages per genre and map to emotion
    genre_map = []
    for genre, features in genre_data.items():
        if features["valence"]:
            avg_valence = sum(features["valence"]) / len(features["valence"])
            avg_energy = sum(features["energy"]) / len(features["energy"])
            genre_map.append({
                "genre": genre,
                "avg_valence": round(avg_valence, 3),
                "avg_energy": round(avg_energy, 3),
                "avg_danceability": round(sum(features["danceability"]) / len(features["danceability"]), 3),
                "avg_tempo": round(sum(features["tempo"]) / len(features["tempo"]), 1),
                "dominant_emotion": compute_emotion(avg_valence, avg_energy),
                "track_count": len(features["valence"])
            })

    # sort by number of tracks so most listened genres appear first
    genre_map.sort(key=lambda x: x["track_count"], reverse=True)

    return {
        "genre_emotion_map": genre_map,
        "total_genres": len(genre_map)
    }

# --- Endpoint 4: Top tracks ---
# Shows the user's most listened tracks with their audio features
@router.get("/top-tracks/{user_id}")
def get_top_tracks(
    user_id: int,
    limit: int = 10,                                  # default top 10
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="You can only view your own top tracks")

    # count how many times each track was listened to
    track_counts = (
        db.query(
            ListeningSession.track_id,
            func.count(ListeningSession.track_id).label("play_count")  # count plays per track
        )
        .filter(ListeningSession.user_id == user_id)
        .group_by(ListeningSession.track_id)
        .order_by(func.count(ListeningSession.track_id).desc())        # most played first
        .limit(limit)
        .all()
    )

    if not track_counts:
        raise HTTPException(status_code=404, detail="No listening sessions found for this user")

    # build response with full track details + play count
    top_tracks = []
    for track_id, play_count in track_counts:
        track = db.query(Track).filter(Track.id == track_id).first()
        if track:
            top_tracks.append({
                "track_id": track.id,
                "title": track.title,
                "artist": track.artist,
                "genre": track.genre,
                "play_count": play_count,
                "valence": track.valence,
                "energy": track.energy,
                "danceability": track.danceability,
                "tempo": track.tempo,
                "dominant_emotion": compute_emotion(track.valence or 0.5, track.energy or 0.5)
            })

    return {
        "user_id": user_id,
        "top_tracks": top_tracks
    }