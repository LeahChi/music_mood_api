import pandas as pd
from app.database import SessionLocal
from app.models.models import Track


def seed_tracks():
    db = SessionLocal()

    # check if already seeded
    if db.query(Track).count() > 0:
        print("Tracks already seeded, skipping.")
        db.close()
        return

    print("Reading the dataset...")
    # Read the CSV — only load what we need
    df = pd.read_csv("spotify_tracks_dataset.csv", usecols=[
        "track_id", "track_name", "artists", "track_genre",
        "valence", "energy", "danceability", "tempo", "duration_ms"
    ])

    # Drop duplicates and nulls
    df = df.drop_duplicates(subset="track_id").dropna(subset=["track_name", "artists"])

    # Only taking 5000 tracks so the DB stays 'manageable'
    df = df.head(5000)

    print(f"Seeding {len(df)} tracks...")
    tracks = []
    for _, row in df.iterrows():
        track = Track(
            title=row["track_name"],
            artist=row["artists"],
            genre=row["track_genre"],
            valence=float(row["valence"]),
            energy=float(row["energy"]),
            danceability=float(row["danceability"]),
            tempo=float(row["tempo"]),
            duration_ms=int(row["duration_ms"]),
            spotify_id=row["track_id"]
        )
        tracks.append(track)

    db.bulk_save_objects(tracks)
    db.commit()
    db.close()
    print("Done! Tracks seeded successfully.")

if __name__ == "__main__":
    seed_tracks()