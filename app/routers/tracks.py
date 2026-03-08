from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.models import Track
from app.schemas.schemas import TrackCreate, TrackResponse, TrackUpdate
from app.auth import get_current_user
from app.models.models import User

router = APIRouter(
    prefix="/tracks",
    tags=["Tracks"]     # groups endpoints in Swagger UI
)

# GET all tracks — public, no auth needed
@router.get("/", response_model=List[TrackResponse])
def get_tracks(
    genre: str = None, # filter by genre if provided
    limit: int = 50, # max number of tracks to return (the DB is huge)
    db: Session = Depends(get_db)
):
    query = db.query(Track)
    if genre:
        # filter by genre if provided
        query = query.filter(Track.genre == genre)
    return query.limit(limit).all()

# GET a single track by ID
@router.get("/{track_id}", response_model=TrackResponse)
def get_track(track_id: int, db: Session = Depends(get_db)):
    track = db.query(Track).filter(Track.id == track_id).first()
    if not track:
        # 404 if track doesn't exist
        raise HTTPException(status_code=404, detail="Track not found")
    return track

# POST create a new track - requires auth
@router.post("/", response_model=TrackResponse, status_code=201)
def create_track(
    track: TrackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)      # must be logged in
):
    # check spotify_id isn't already in the DB
    if track.spotify_id:
        existing = db.query(Track).filter(Track.spotify_id == track.spotify_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Track with this Spotify ID already exists")

    new_track = Track(**track.model_dump())
    db.add(new_track)
    db.commit()
    db.refresh(new_track)
    return new_track

# PUT update a track — requires auth
# (It's a PUT becuse you're replacing the resourc e with what is now being sent)
@router.put("/{track_id}", response_model=TrackResponse)
def update_track(
    track_id: int,
    track_update: TrackUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # must be logged in
):
    track = db.query(Track).filter(Track.id == track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")

    # only update fields that were actually given to update (exclude_unset=True)
    update_data = track_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(track, field, value)

    db.commit()
    db.refresh(track)
    return track

# DELETE a track - requires auth
@router.delete("/{track_id}", status_code=204)
def delete_track(
    track_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # must be logged in
):
    track = db.query(Track).filter(Track.id == track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")

    db.delete(track)
    db.commit()
    # 204 means success with no content returned