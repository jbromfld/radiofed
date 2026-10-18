import math

from sqlalchemy import text

from db import engine


def compute_features(song_id):
    with engine.begin() as conn:

        unique_chords = conn.execute(text("""
            SELECT COUNT(DISTINCT chord_root)
            FROM measures
            WHERE song_id = :song_id AND chord_root IS NOT NULL
        """), {"song_id": song_id}).scalar()

        total_measures = conn.execute(text("""
            SELECT COUNT(*)
            FROM measures
            WHERE song_id = :song_id
        """), {"song_id": song_id}).scalar()

        note_stats = conn.execute(text("""
            SELECT
                COUNT(*)                                        AS note_count,
                AVG(pitch_midi)                                 AS avg_pitch,
                VARIANCE(pitch_midi)                            AS pitch_variance,
                MAX(pitch_midi) - MIN(pitch_midi)               AS pitch_range,
                AVG(duration_beats)                             AS avg_note_duration,
                VARIANCE(duration_beats)                        AS note_duration_variance
            FROM events
            WHERE measure_id IN (
                SELECT id FROM measures WHERE song_id = :song_id
            )
        """), {"song_id": song_id}).fetchone()

        note_count           = note_stats[0] or 0
        avg_pitch            = float(note_stats[1]) if note_stats[1] is not None else 0.0
        pitch_variance       = float(note_stats[2]) if note_stats[2] is not None else 0.0
        pitch_range          = int(note_stats[3])   if note_stats[3] is not None else 0
        avg_note_duration    = float(note_stats[4]) if note_stats[4] is not None else 0.0
        note_duration_variance = float(note_stats[5]) if note_stats[5] is not None else 0.0

        avg_note_density = note_count / total_measures if total_measures else 0.0

        # Melodic interval: mean absolute step between consecutive pitches
        pitch_rows = conn.execute(text("""
            SELECT e.pitch_midi
            FROM events e
            JOIN measures m ON e.measure_id = m.id
            WHERE m.song_id = :song_id
            ORDER BY m.bar_number, e.beat_position
        """), {"song_id": song_id}).fetchall()

        pitch_list = [r[0] for r in pitch_rows if r[0] is not None]
        if len(pitch_list) >= 2:
            intervals = [abs(pitch_list[i + 1] - pitch_list[i]) for i in range(len(pitch_list) - 1)]
            melodic_interval = sum(intervals) / len(intervals)
        else:
            melodic_interval = 0.0

        chord_counts = conn.execute(text("""
            SELECT chord_root, COUNT(*)
            FROM measures
            WHERE song_id = :song_id AND chord_root IS NOT NULL
            GROUP BY chord_root
        """), {"song_id": song_id}).fetchall()

        total = sum(c[1] for c in chord_counts)
        entropy = -sum(
            (c[1] / total) * math.log(c[1] / total)
            for c in chord_counts
        ) if total > 0 else 0.0

        conn.execute(text("""
            INSERT INTO song_features (
                song_id, unique_chords, total_measures,
                avg_note_density, chord_entropy,
                pitch_range, avg_pitch, pitch_variance,
                avg_note_duration, note_duration_variance,
                melodic_interval, note_count
            )
            VALUES (
                :song_id, :unique_chords, :total_measures,
                :avg_note_density, :entropy,
                :pitch_range, :avg_pitch, :pitch_variance,
                :avg_note_duration, :note_duration_variance,
                :melodic_interval, :note_count
            )
            ON CONFLICT (song_id) DO UPDATE SET
                unique_chords          = EXCLUDED.unique_chords,
                total_measures         = EXCLUDED.total_measures,
                avg_note_density       = EXCLUDED.avg_note_density,
                chord_entropy          = EXCLUDED.chord_entropy,
                pitch_range            = EXCLUDED.pitch_range,
                avg_pitch              = EXCLUDED.avg_pitch,
                pitch_variance         = EXCLUDED.pitch_variance,
                avg_note_duration      = EXCLUDED.avg_note_duration,
                note_duration_variance = EXCLUDED.note_duration_variance,
                melodic_interval       = EXCLUDED.melodic_interval,
                note_count             = EXCLUDED.note_count
        """), {
            "song_id":               song_id,
            "unique_chords":         unique_chords,
            "total_measures":        total_measures,
            "avg_note_density":      avg_note_density,
            "entropy":               entropy,
            "pitch_range":           pitch_range,
            "avg_pitch":             avg_pitch,
            "pitch_variance":        pitch_variance,
            "avg_note_duration":     avg_note_duration,
            "note_duration_variance": note_duration_variance,
            "melodic_interval":      melodic_interval,
            "note_count":            note_count,
        })
