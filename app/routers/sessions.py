from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from typing import List
from app.database import get_db
from app.models.models import ListeningSession, Track, User, ListeningContext
from app.schemas.schemas import SessionCreate, SessionResponse
from app.auth import get_current_user

router = APIRouter(
    prefix="/sessions",
    tags=["Listening Sessions"]  # groups endpoints together in Swagger UI
)

# POST — log a new listening session e.g. "I listened to track X while commuting"
@router.post("/", response_model=SessionResponse, status_code=201)
def create_session(
    session: SessionCreate,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user)  # user identity comes from JWT token
):
    # check the track actually exists in our database
    track = db.query(Track).filter(Track.id == session.track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")

    # validate the context is one of our allowed values
    try:
        context = ListeningContext(session.context)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid context. Must be one of: {[c.value for c in ListeningContext]}"
        )

    # create the session
    new_session = ListeningSession(
        user_id=current_user.id,
        track_id=session.track_id,
        context=context
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session

# GET — retrieve all listening sessions for a specific user
@router.get("/user/{user_id}", response_model=List[SessionResponse])
def get_user_sessions(
    user_id: int,
    limit: int = 50,                                 # default to 50 sessions
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user)  # must be logged in to view sessions
):
    # users can only view their own sessions — not other people's
    if current_user.id != user_id:
        raise HTTPException(
            status_code=403,                         # 403 = forbidden, not just unauthorised
            detail="You can only view your own listening sessions"
        )


    sessions = (db.query(ListeningSession)          # "look in the ListeningSession table"
    .filter(ListeningSession.user_id == user_id)   # "only where user_id matches"
    .order_by(ListeningSession.listened_at.desc()) # "newest first"
    .limit(limit)                                  # "only give me 50"
    .all())                                         # "return all results as a list"

    return sessions

# DELETE — remove a specific session
@router.delete("/{session_id}", status_code=204)
def delete_session(
    session_id: int,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    session = (db.query(ListeningSession)        # "look in the ListeningSession table"
    .filter(ListeningSession.id == session_id)  # "only where id matches"
    .first())                                    # "give me the first result, or None if not found"

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # users can only delete their own sessions
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only delete your own sessions"
        )

    db.delete(session)
    db.commit()