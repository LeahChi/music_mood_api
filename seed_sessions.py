import random
from datetime import datetime, timedelta, timezone
from app.database import SessionLocal
from app.models.models import ListeningSession, User, Track, ListeningContext

def seed_sessions():
    db = SessionLocal()

    # check if already seeded
    if db.query(ListeningSession).count() > 0:
        print("Sessions already seeded, skipping.")
        db.close()
        return

    # get all users and tracks from the database
    users = db.query(User).all()
    tracks = db.query(Track).all()

    if not users or not tracks:
        print("No users or tracks found. Please seed those first.")
        db.close()
        return

    contexts = [c for c in ListeningContext]  # all possible contexts
    sessions = []

    print("Seeding listening sessions...")

    # create 200 fake sessions spread across users
    for _ in range(200):
        # pick a random user and track
        user = random.choice(users)
        track = random.choice(tracks)
        context = random.choice(contexts)

        # random timestamp within the last 30 days
        # this gives us time-based analytics to work with
        days_ago = random.randint(0, 30)
        hours_ago = random.randint(0, 23)
        listened_at = datetime.now(timezone.utc) - timedelta(days=days_ago, hours=hours_ago)

        session = ListeningSession(
            user_id=user.id,
            track_id=track.id,
            context=context,
            listened_at=listened_at
        )
        sessions.append(session)

    db.bulk_save_objects(sessions)
    db.commit()
    db.close()
    print(f"Done! 200 listening sessions seeded across {len(users)} users.")

if __name__ == "__main__":
    seed_sessions()