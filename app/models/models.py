from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
import enum

# Set contexts based on reserch on common listening scenarios
class ListeningContext(enum.Enum):
    working = "working"
    commuting = "commuting"
    exercising = "exercising"
    relaxing = "relaxing"
    socialising = "socialising"
    sleeping = "sleeping"
    other = "other"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # user.sessions gives you all listening sessions for that user
    # user.mood_snapshots gives you all mood snapshots for that user
    sessions = relationship("ListeningSession", back_populates="user")
    mood_snapshots = relationship("MoodSnapshot", back_populates="user")

class Track(Base):
    __tablename__ = "tracks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    artist = Column(String, nullable=False)
    genre = Column(String)

    # The 4 variables come from Spotify's audio features API - they are commonly used to predict mood
    valence = Column(Float)       # 0.0 = negative mood, 1.0 = positive mood
    energy = Column(Float)        # 0.0 = calm, 1.0 = intense
    danceability = Column(Float)  # 0.0 = least danceable, 1.0 = most
    tempo = Column(Float)         # BPM

    duration_ms = Column(Integer)
    spotify_id = Column(String, unique=True)

    sessions = relationship("ListeningSession", back_populates="track")

class ListeningSession(Base):
    __tablename__ = "listening_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    track_id = Column(Integer, ForeignKey("tracks.id"), nullable=False)
    listened_at = Column(DateTime, default=datetime.utcnow)
    context = Column(Enum(ListeningContext), default=ListeningContext.other)

    # Two-way links: session.user gives you the User, session.track gives you the Track
    user = relationship("User", back_populates="sessions")
    track = relationship("Track", back_populates="sessions")

class MoodSnapshot(Base):
    __tablename__ = "mood_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    computed_mood_score = Column(Float)   # derived from avg valence of recent tracks
    dominant_emotion = Column(String)     # e.g. high valence + high energy = "energetic"
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="mood_snapshots")