# radiofed

ML-ready music analysis system that ingests MIDI files, extracts musical features, and stores structured data in PostgreSQL for downstream ML pipelines.

## Project Structure

```
src/
  db.py                  # SQLAlchemy engine + session factory
  ingest.py              # MIDI parsing and PostgreSQL insertion
  batch_ingest.py        # Batch runner for data/raw_midi/
  feature_extraction.py  # Derived ML feature computation
sql/
  20260225_initial_schema.sql  # Full DB schema + materialized view
data/
  raw_midi/              # Drop .mid/.midi files here for batch ingestion
  A/ B/ ... Z/           # Source MIDI organized alphabetically by artist
```

## Tech Stack

- Python 3, music21, SQLAlchemy, psycopg2
- PostgreSQL database: `guitar_ml`
- No framework; plain scripts

## Database

**Connection string (hardcoded):** `postgresql://user:password@localhost:5432/guitar_ml`

**Key tables:**
- `songs` — metadata (title, artist, genre, tempo, key, time signature)
- `measures` — bar-level chord analysis (root, quality, scale degree)
- `events` — individual note events (pitch, octave, duration, beat)
- `chord_transitions` — Markov-chain transition counts between scale degrees
- `song_features` — derived ML features (upserted by feature_extraction.py)
- `song_ml_view` — materialized view for ML exports

## Common Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Apply schema (first time)
psql -U user -d guitar_ml -f sql/20260225_initial_schema.sql

# Batch ingest all MIDI files in data/raw_midi/
python src/batch_ingest.py

# Single file ingest
python -c "from src.ingest import ingest_midi; ingest_midi('path/to/file.mid', genre='folk')"
```

## Notes

- Database credentials are hardcoded; no .env file exists yet
- `batch_ingest.py` scans `./data/raw_midi` and defaults genre to `"folk"`
- `feature_extraction.py` uses upsert to safely re-run on existing songs
- Data sourced from Colin Raffel (2016) and Million Song Dataset (2011)
- Git branches: `master` (main), `develop` (active)
