from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime
from typing import Optional

# --- User schemas ---

class UserCreate(BaseModel):
    username: str
    email: EmailStr # Pydantic's built-in email validation
    password: str 

    @field_validator("username")
    def username_must_be_valid(cls, v):
        # this runs automatically every time someone sends a username
        v = v.strip()  # remove accidental spaces at start/end
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters")
        if len(v) > 30:
            raise ValueError("Username must be under 30 characters")
        if not v.isalnum():
            # no spaces or symbols
            raise ValueError("Username must only contain letters and numbers")
        return v

    @field_validator("password")
    def password_must_be_strong(cls, v):
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True # Tells Pydantic to read data from SQLAlchemy models


class UserLogin(BaseModel):
    username: str
    password: str

# What's sent back after a successful login
class Token(BaseModel):
    access_token: str
    token_type: str

# JWT token: endoded data that includes the username and an expiration time
class TokenData(BaseModel):
    username: Optional[str] = None


# --- Track schemas --- 

class TrackCreate(BaseModel):
    title: str
    artist: str
    genre: Optional[str] = None
    valence: Optional[float] = None      # 0.0 = sad, 1.0 = happy
    energy: Optional[float] = None       # 0.0 = calm, 1.0 = energetic
    danceability: Optional[float] = None # 0.0 = not danceable, 1.0 = danceable
    tempo: Optional[float] = None        # BPM (beats per minute)
    duration_ms: Optional[int] = None    # Duration in milliseconds
    spotify_id: Optional[str] = None     # Spotify's unique track ID

    @field_validator("valence", "energy", "danceability")
    def must_be_between_0_and_1(cls, v):
        # these are Spotify audio features — by definition they must be 0-1
        # anything outside this range means bad data
        if v is not None and not 0 <= v <= 1:
            raise ValueError("Must be between 0 and 1")
        return v

    @field_validator("tempo")
    def tempo_must_be_positive(cls, v):
        # tempo is beats per minute — can't be negative or zero
        if v is not None and v <= 0:
            raise ValueError("Tempo must be a positive number")
        return v

# What gets sent back when returning a track
class TrackResponse(BaseModel):
    id: int
    title: str
    artist: str
    genre: Optional[str] = None
    valence: Optional[float] = None
    energy: Optional[float] = None
    danceability: Optional[float] = None
    tempo: Optional[float] = None
    duration_ms: Optional[int] = None
    spotify_id: Optional[str] = None

    class Config:
        from_attributes = True            # Tells Pydantic to read data from SQLAlchemy models

# When someone wants to update a track
class TrackUpdate(BaseModel):
    title: Optional[str] = None
    artist: Optional[str] = None
    genre: Optional[str] = None
    valence: Optional[float] = None
    energy: Optional[float] = None
    danceability: Optional[float] = None
    tempo: Optional[float] = None
    duration_ms: Optional[int] = None


# --- Session schemas ---

# When a user logs a listening session, they just provide the track_id and context — everything else is automatic
class SessionCreate(BaseModel):
    track_id: int                        # which track they listened to
    context: str = "other"               # what they were doing e.g. "working", "commuting"

    @field_validator("track_id")
    def track_id_must_be_positive(cls, v):
        # track IDs in our DB start at 1 — 0 or negative means bad input
        if v <= 0:
            raise ValueError("track_id must be a positive integer")
        return v

    @field_validator("context")
    def context_must_be_valid(cls, v):
        # only allow the contexts we defined in our ListeningContext enum
        # grounded in Schäfer's research on music functions in everyday life
        valid_contexts = ["working", "commuting", "exercising", "relaxing", "socialising", "sleeping", "other"]
        if v not in valid_contexts:
            raise ValueError(f"context must be one of: {valid_contexts}")
        return v

# What we send back when returning a session
class SessionResponse(BaseModel):
    id: int
    user_id: int
    track_id: int
    listened_at: datetime                 # when they listened to the track (automatically set)
    context: str                          # what context they were in

    class Config:
        from_attributes = True
        use_enum_values = True            # converts enum to plain string in response