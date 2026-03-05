-- =========================================================
-- Add song_hotttnesss and artist_hotttnesss to songs table
-- and rebuild song_ml_view to include them.
-- =========================================================

ALTER TABLE songs ADD COLUMN IF NOT EXISTS song_hotttnesss FLOAT;
ALTER TABLE songs ADD COLUMN IF NOT EXISTS artist_hotttnesss FLOAT;

-- Rebuild the materialized view to include new columns
DROP MATERIALIZED VIEW IF EXISTS song_ml_view;

CREATE MATERIALIZED VIEW song_ml_view AS
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
