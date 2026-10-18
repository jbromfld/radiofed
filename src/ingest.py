import uuid
import os
import signal
from collections import Counter

from music21 import converter, chord
from sqlalchemy import text

from db import engine

PARSE_TIMEOUT = 20  # seconds before a hanging MIDI parse is aborted


def _parse_midi(file_path):
    """Parse a MIDI file with a hard timeout. Raises TimeoutError if it hangs."""
    def _handler(signum, frame):
        raise TimeoutError(f"parse timed out after {PARSE_TIMEOUT}s")

    signal.signal(signal.SIGALRM, _handler)
    signal.alarm(PARSE_TIMEOUT)
    try:
        return converter.parse(file_path)
    finally:
        signal.alarm(0)  # cancel alarm whether we succeeded or raised


def infer_chord_from_measure(measure, key_obj):
    """
    Infer chord root + quality + scale degree from notes in measure.
    """
    notes = [n for n in measure.notes if n.isNote]

    if not notes:
        return None, None, None

    pitches = [n.pitch for n in notes]
    c = chord.Chord(pitches)

    root = c.root()
    quality = c.quality

    try:
        degree = key_obj.getScaleDegreeFromPitch(root)
    except Exception:
        degree = None

    return (
        root.name if root else None,
        quality,
        str(degree) if degree else None
    )


def _extract_msd_track_id(file_path):
    """
    Extract the MSD track ID from the LMD directory structure:
      dataset/{X}/{Y}/{Z}/{MSD_TRACK_ID}/{hash}.mid
    Returns the track ID string if it looks valid, else None.
    """
    candidate = os.path.basename(os.path.dirname(file_path))
    return candidate if candidate.startswith("TR") else None


def ingest_midi(file_path, genre="unknown"):
    title = os.path.basename(file_path)
    msd_track_id = _extract_msd_track_id(file_path)

    # Deduplication: skip files already in the database
    with engine.connect() as conn:
        existing = conn.execute(
            text("SELECT id FROM songs WHERE title = :title"),
            {"title": title}
        ).fetchone()
        if existing:
            print(f"  Skipping {title} (already ingested)")
            return None

    score = _parse_midi(file_path)

    tempo_marks = score.metronomeMarkBoundaries()
    tempo = tempo_marks[0][2].number if tempo_marks else 120

    time_sig = score.recurse().getElementsByClass('TimeSignature')
    time_signature = time_sig[0].ratioString if time_sig else "4/4"

    key_obj = score.analyze('key')
    key_confidence = getattr(key_obj, 'correlationCoefficient', None)

    song_id = uuid.uuid4()

    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO songs (
                id, title, msd_track_id, genre, tempo_bpm,
                time_signature, key_tonic, key_mode, key_confidence
            )
            VALUES (
                :id, :title, :msd_track_id, :genre, :tempo,
                :time_sig, :tonic, :mode, :key_confidence
            )
        """), {
            "id": song_id,
            "title": title,
            "msd_track_id": msd_track_id,
            "genre": genre,
            "tempo": tempo,
            "time_sig": time_signature,
            "tonic": key_obj.tonic.name,
            "mode": key_obj.mode,
            "key_confidence": float(key_confidence) if key_confidence is not None else None,
        })

        part = score.parts[0]
        measures = part.getElementsByClass("Measure")

        scale_degrees = []  # collected for chord_transitions

        for measure in measures:
            measure_id = uuid.uuid4()

            chord_root, chord_quality, scale_degree = infer_chord_from_measure(measure, key_obj)

            if scale_degree is not None:
                scale_degrees.append(scale_degree)

            conn.execute(text("""
                INSERT INTO measures (
                    id, song_id, bar_number,
                    chord_root, chord_quality, scale_degree
                )
                VALUES (
                    :id, :song_id, :bar_number,
                    :chord_root, :chord_quality, :scale_degree
                )
            """), {
                "id": measure_id,
                "song_id": song_id,
                "bar_number": measure.number,
                "chord_root": chord_root,
                "chord_quality": chord_quality,
                "scale_degree": scale_degree,
            })

            for element in measure.notes:
                if not element.isNote:
                    continue

                event_id = uuid.uuid4()

                conn.execute(text("""
                    INSERT INTO events (
                        id, measure_id,
                        pitch_midi, pitch_class,
                        octave, duration_beats,
                        beat_position
                    )
                    VALUES (
                        :id, :measure_id,
                        :pitch_midi, :pitch_class,
                        :octave, :duration,
                        :beat_position
                    )
                """), {
                    "id": event_id,
                    "measure_id": measure_id,
                    "pitch_midi": element.pitch.midi,
                    "pitch_class": element.pitch.name,
                    "octave": element.pitch.octave,
                    "duration": float(element.duration.quarterLength),
                    "beat_position": float(element.beat),
                })

        # Populate chord_transitions from consecutive scale degree pairs
        if len(scale_degrees) >= 2:
            transition_counts = Counter(zip(scale_degrees, scale_degrees[1:]))
            for (from_deg, to_deg), count in transition_counts.items():
                conn.execute(text("""
                    INSERT INTO chord_transitions (
                        song_id, from_degree, to_degree, transition_count
                    )
                    VALUES (:song_id, :from_deg, :to_deg, :count)
                    ON CONFLICT (song_id, from_degree, to_degree) DO UPDATE
                        SET transition_count = EXCLUDED.transition_count
                """), {
                    "song_id": song_id,
                    "from_deg": from_deg,
                    "to_deg": to_deg,
                    "count": count,
                })

    print(f"  Ingested: {title}")
    return song_id
