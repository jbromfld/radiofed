import uuid
from music21 import converter
from sqlalchemy import text
from db import SessionLocal


def ingest_midi(file_path, genre="unknown"):
    session = SessionLocal()
    
    score = converter.parse(file_path)

    tempo = score.metronomeMarkBoundaries()[0][2].number
    time_sig = score.recurse().getElementsByClass('TimeSignature')[0]
    key = score.analyze('key')

    song_id = uuid.uuid4()

    session.execute(text("""
        INSERT INTO songs (id, title, genre, tempo_bpm, time_signature, key_tonic, key_mode)
        VALUES (:id, :title, :genre, :tempo, :time_sig, :tonic, :mode)
    """), {
        "id": song_id,
        "title": file_path.split("/")[-1],
        "genre": genre,
        "tempo": tempo,
        "time_sig": str(time_sig.ratioString),
        "tonic": key.tonic.name,
        "mode": key.mode
    })

    measures = score.parts[0].getElementsByClass("Measure")

    for measure in measures:
        measure_id = uuid.uuid4()

        session.execute(text("""
            INSERT INTO measures (id, section_id, bar_number)
            VALUES (:id, NULL, :bar_number)
        """), {
            "id": measure_id,
            "bar_number": measure.number
        })

        for element in measure.notes:
            event_id = uuid.uuid4()

            session.execute(text("""
                INSERT INTO events (
                    id, measure_id, event_type,
                    pitch_midi, pitch_class, octave,
                    duration_beats, beat_position
                )
                VALUES (:id, :measure_id, 'note',
                        :pitch_midi, :pitch_class, :octave,
                        :duration, :beat_position)
            """), {
                "id": event_id,
                "measure_id": measure_id,
                "pitch_midi": element.pitch.midi,
                "pitch_class": element.pitch.name,
                "octave": element.pitch.octave,
                "duration": element.duration.quarterLength,
                "beat_position": element.beat
            })

    session.commit()
    session.close()