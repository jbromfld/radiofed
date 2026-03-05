"""
Enrich songs table with artist, title, genre, and hotttnesss from MSD metadata files.

Required downloads (free):
  msd_summary_file.h5   — https://labrosa.ee.columbia.edu/millionsong/pages/getting-dataset
  msd_tagtraum_cd2.cls  — https://www.tagtraum.com/msd_genre_datasets.html

Usage:
  python src/enrich_metadata.py \
      --h5 /path/to/msd_summary_file.h5 \
      --genres /path/to/msd_tagtraum_cd2.cls

Requires: pip install tables
"""

import sys
import os
import argparse
import logging

sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import text
from db import engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger(__name__)


def load_msd_summary(h5_path):
    """
    Load track_id → (artist_name, title) from msd_summary_file.h5.

    The summary file splits data across two row-aligned tables:
      analysis/songs  — contains track_id (starts with TR)
      metadata/songs  — contains artist_name, title
    """
    try:
        import tables
    except ImportError:
        raise ImportError("Install PyTables first: pip install tables")

    log.info(f"Loading MSD summary from {h5_path}...")
    result = {}
    with tables.open_file(h5_path, "r") as h5:
        analysis = h5.root.analysis.songs
        metadata = h5.root.metadata.songs

        for a_row, m_row in zip(analysis.iterrows(), metadata.iterrows()):
            track_id         = a_row["track_id"].decode("utf-8", errors="replace").strip()
            artist           = m_row["artist_name"].decode("utf-8", errors="replace").strip()
            title            = m_row["title"].decode("utf-8", errors="replace").strip()
            song_hotttnesss  = float(m_row["song_hotttnesss"])
            artist_hotttnesss = float(m_row["artist_hotttnesss"])
            result[track_id] = (artist, title, song_hotttnesss, artist_hotttnesss)

    log.info(f"Loaded {len(result):,} MSD tracks.")
    return result


def load_tagtraum_genres(cls_path):
    """
    Load track_id → genre from msd_tagtraum_cd2.cls.
    Format: track_id<TAB>majority_genre[<TAB>minority_genre]
    Lines starting with # are comments.
    """
    log.info(f"Loading Tagtraum genre annotations from {cls_path}...")
    genres = {}
    with open(cls_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) >= 2:
                genres[parts[0]] = parts[1]

    log.info(f"Loaded {len(genres):,} genre annotations.")
    return genres


def enrich(h5_path, genres_path=None):
    msd = load_msd_summary(h5_path)
    genres = load_tagtraum_genres(genres_path) if genres_path else {}

    log.info("Fetching songs with msd_track_id from DB...")
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT id, msd_track_id FROM songs WHERE msd_track_id IS NOT NULL")
        ).fetchall()

    log.info(f"Enriching {len(rows)} songs...")
    updated = 0
    with engine.begin() as conn:
        for song_id, track_id in rows:
            meta = msd.get(track_id)
            if meta is None:
                continue
            artist, title_msd, song_hot, artist_hot = meta
            genre = genres.get(track_id)
            conn.execute(text("""
                UPDATE songs
                SET artist            = :artist,
                    genre             = COALESCE(:genre, genre),
                    song_hotttnesss   = :song_hot,
                    artist_hotttnesss = :artist_hot
                WHERE id = :id
            """), {
                "artist": artist,
                "genre": genre,
                "song_hot": song_hot if song_hot > 0 else None,
                "artist_hot": artist_hot if artist_hot > 0 else None,
                "id": song_id,
            })
            updated += 1

    log.info(f"Updated {updated} songs with artist/genre/hotttnesss.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enrich songs table from MSD metadata.")
    parser.add_argument("--h5", required=True, help="Path to msd_summary_file.h5")
    parser.add_argument("--genres", default=None, help="Path to msd_tagtraum_cd2.cls (optional)")
    args = parser.parse_args()
    enrich(args.h5, args.genres)
