import os
import sys
import argparse
import logging

# Allow running from workspace root: python src/batch_ingest.py
sys.path.insert(0, os.path.dirname(__file__))

from ingest import ingest_midi
from feature_extraction import compute_features
from db import engine
from sqlalchemy import text

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "dataset")


REFRESH_EVERY = 500  # refresh song_ml_view every N successful ingests


def _refresh_view():
    with engine.begin() as conn:
        conn.execute(text("REFRESH MATERIALIZED VIEW song_ml_view"))
    log.info("song_ml_view refreshed.")


def batch_ingest(data_dir=DATA_DIR, genre="unknown", limit=None):
    """
    Ingest MIDI files from data_dir.
    limit: maximum number of new songs to ingest (None = no limit).
           Skipped (already ingested) and failed files do not count toward the limit.
           Resume a previous run by just calling again — already-ingested files are skipped.
    """
    midi_files = []
    for root, _, files in os.walk(data_dir):
        for f in files:
            if f.lower().endswith((".mid", ".midi")):
                midi_files.append(os.path.join(root, f))

    total = len(midi_files)
    limit_msg = f", limit {limit}" if limit is not None else ""
    log.info(f"Found {total} MIDI files under {os.path.abspath(data_dir)}{limit_msg}")

    succeeded = 0
    skipped = 0
    failed = 0

    for i, path in enumerate(midi_files, 1):
        if limit is not None and succeeded >= limit:
            log.info(f"Limit of {limit} reached. Stopping.")
            break
        log.info(f"[{i}/{total}] {os.path.relpath(path, data_dir)}")
        try:
            song_id = ingest_midi(path, genre=genre)
            if song_id is None:
                skipped += 1
                continue
            compute_features(song_id)
            succeeded += 1
            if succeeded % REFRESH_EVERY == 0:
                _refresh_view()
        except Exception as e:
            log.warning(f"  FAILED: {e}")
            failed += 1

    log.info(f"Done. {succeeded} ingested, {skipped} skipped, {failed} failed.")
    _refresh_view()


def backfill_msd_track_ids(data_dir=DATA_DIR):
    """
    Backfill msd_track_id for songs ingested before this column existed.
    Walks data_dir and builds a {filename: msd_track_id} map, then updates
    any songs row where msd_track_id IS NULL and title matches a known file.
    """
    log.info("Building filename → msd_track_id map from filesystem...")
    file_map = {}
    for root, _, files in os.walk(data_dir):
        for f in files:
            if f.lower().endswith((".mid", ".midi")):
                candidate = os.path.basename(root)
                if candidate.startswith("TR"):
                    file_map[f] = candidate

    log.info(f"Found {len(file_map)} MIDI files. Updating songs table...")
    updated = 0
    with engine.begin() as conn:
        rows = conn.execute(
            text("SELECT id, title FROM songs WHERE msd_track_id IS NULL")
        ).fetchall()
        for song_id, title in rows:
            track_id = file_map.get(title)
            if track_id:
                conn.execute(
                    text("UPDATE songs SET msd_track_id = :tid WHERE id = :id"),
                    {"tid": track_id, "id": song_id},
                )
                updated += 1

    log.info(f"Backfilled {updated} of {len(rows)} songs with msd_track_id.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch ingest MIDI files into the database.")
    parser.add_argument("--limit", type=int, default=None, help="Max number of new songs to ingest (default: no limit)")
    parser.add_argument("--genre", type=str, default="unknown", help="Genre label to apply to all ingested songs")
    args = parser.parse_args()
    batch_ingest(limit=args.limit, genre=args.genre)
