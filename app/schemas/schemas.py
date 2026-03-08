from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class UserCreate(BaseModel):
    username: str
    email: EmailStr # Pydantic's built-in email validation
    password: str 


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

# Track schemas

class TrackCreate(BaseModel):
    title: str
    artist: str
    genre: Optional[str] = None
    valence: Optional[float] = None     # 0.0 = sad, 1.0 = happy
    energy: Optional[float] = None      # 0.0 = calm, 1.0 = energetic
    danceability: Optional[float] = None # 0.0 = not danceable, 1.0 = danceable
    tempo: Optional[float] = None       # BPM (beats per minute)
    duration_ms: Optional[int] = None  # Duration in milliseconds
    spotify_id: Optional[str] = None          # Spotify's unique track ID

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
        from_attributes = True # Tells Pydantic to read data from SQLAlchemy models

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