-- =========================================================
-- Guitar ML Dataset Schema (Single Instrument V1)
-- =========================================================

-- Enable UUID generation (if not already enabled)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =========================================================
-- SONGS
-- =========================================================

CREATE TABLE IF NOT EXISTS songs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT,
    msd_track_id TEXT,
    artist TEXT,
    genre TEXT,
    tempo_bpm FLOAT,
    time_signature TEXT,
    key_tonic TEXT,
    key_mode TEXT,
    key_confidence FLOAT,
    song_hotttnesss FLOAT,
    artist_hotttnesss FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_songs_msd_track_id
    ON songs(msd_track_id);

CREATE INDEX IF NOT EXISTS idx_songs_genre
    ON songs(genre);

CREATE INDEX IF NOT EXISTS idx_songs_key
    ON songs(key_tonic, key_mode);


-- =========================================================
-- MEASURES
-- =========================================================

CREATE TABLE IF NOT EXISTS measures (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    song_id UUID NOT NULL REFERENCES songs(id) ON DELETE CASCADE,
    bar_number INT NOT NULL,
    chord_root TEXT,
    chord_quality TEXT,
    scale_degree TEXT
);

CREATE INDEX IF NOT EXISTS idx_measures_song
    ON measures(song_id);

CREATE INDEX IF NOT EXISTS idx_measures_bar
    ON measures(song_id, bar_number);

CREATE INDEX IF NOT EXISTS idx_measures_degree
    ON measures(scale_degree);


-- =========================================================
-- EVENTS (Single Instrument Notes)
-- =========================================================

CREATE TABLE IF NOT EXISTS events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    measure_id UUID NOT NULL REFERENCES measures(id) ON DELETE CASCADE,
    pitch_midi INT,
    pitch_class TEXT,
    octave INT,
    duration_beats FLOAT,
    beat_position FLOAT
);

CREATE INDEX IF NOT EXISTS idx_events_measure
    ON events(measure_id);

CREATE INDEX IF NOT EXISTS idx_events_pitch
    ON events(pitch_midi);

CREATE INDEX IF NOT EXISTS idx_events_duration
    ON events(duration_beats);


-- =========================================================
-- CHORD TRANSITIONS (For ML / Markov / Clustering)
-- =========================================================

CREATE TABLE IF NOT EXISTS chord_transitions (
    song_id UUID NOT NULL REFERENCES songs(id) ON DELETE CASCADE,
    from_degree TEXT NOT NULL,
    to_degree TEXT NOT NULL,
    transition_count INT NOT NULL,
    PRIMARY KEY (song_id, from_degree, to_degree)
);

CREATE INDEX IF NOT EXISTS idx_chord_transitions_song
    ON chord_transitions(song_id);


-- =========================================================
-- SONG-LEVEL FEATURES (Derived Table)
-- =========================================================

CREATE TABLE IF NOT EXISTS song_features (
    song_id UUID PRIMARY KEY REFERENCES songs(id) ON DELETE CASCADE,
    unique_chords INT,
    total_measures INT,
    avg_note_density FLOAT,
    chord_entropy FLOAT,
    pitch_range INT,
    avg_pitch FLOAT,
    pitch_variance FLOAT,
    avg_note_duration FLOAT,
    note_duration_variance FLOAT,
    melodic_interval FLOAT,
    note_count INT,
    created_at TIMESTAMP DEFAULT NOW()
);


-- =========================================================
-- MATERIALIZED VIEW FOR ML EXPORT
-- (pandas-ready: SELECT * FROM song_ml_view)
-- After ingestion run: REFRESH MATERIALIZED VIEW song_ml_view;
-- =========================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS song_ml_view AS
SELECT
    s.id               AS song_id,
    s.genre,
    s.tempo_bpm,
    s.time_signature,
    s.key_tonic,
    s.key_mode,
    s.key_confidence,
    s.song_hotttnesss,
    s.artist_hotttnesss,
    f.unique_chords,
    f.total_measures,
    f.avg_note_density,
    f.chord_entropy,
    f.pitch_range,
    f.avg_pitch,
    f.pitch_variance,
    f.avg_note_duration,
    f.note_duration_variance,
    f.melodic_interval,
    f.note_count
FROM songs s
LEFT JOIN song_features f ON s.id = f.song_id;


ALTER TABLE songs ADD COLUMN IF NOT EXISTS msd_track_id TEXT;
CREATE INDEX IF NOT EXISTS idx_songs_msd_track_id ON songs(msd_track_id);

-- =========================================================
-- DONE
-- =========================================================
