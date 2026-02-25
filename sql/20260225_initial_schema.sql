CREATE TABLE songs (
    id UUID PRIMARY KEY,
    title TEXT,
    artist TEXT,
    genre TEXT,
    tempo_bpm FLOAT,
    time_signature TEXT,
    key_tonic TEXT,
    key_mode TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_songs_genre ON songs(genre);

CREATE TABLE sections (
    id UUID PRIMARY KEY,
    song_id UUID REFERENCES songs(id) ON DELETE CASCADE,
    section_label TEXT,        -- A, B, etc.
    section_role TEXT,         -- VERSE, CHORUS, INTRO
    start_bar INT,
    end_bar INT
);

CREATE INDEX idx_sections_song ON sections(song_id);

CREATE TABLE measures (
    id UUID PRIMARY KEY,
    section_id UUID REFERENCES sections(id) ON DELETE CASCADE,
    bar_number INT,
    chord_root TEXT,
    chord_quality TEXT,
    scale_degree TEXT
);

CREATE INDEX idx_measures_section ON measures(section_id);

CREATE TABLE events (
    id UUID PRIMARY KEY,
    measure_id UUID REFERENCES measures(id) ON DELETE CASCADE,
    event_type TEXT,                -- note | chord
    pitch_midi INT,
    pitch_class TEXT,
    octave INT,
    string_number INT,
    fret_number INT,
    duration_beats FLOAT,
    beat_position FLOAT
);

CREATE INDEX idx_events_measure ON events(measure_id);
CREATE INDEX idx_events_pitch ON events(pitch_midi);

CREATE TABLE chord_transitions (
    song_id UUID REFERENCES songs(id) ON DELETE CASCADE,
    from_degree TEXT,
    to_degree TEXT,
    count INT,
    PRIMARY KEY (song_id, from_degree, to_degree)
);

CREATE TABLE song_features (
    song_id UUID PRIMARY KEY REFERENCES songs(id) ON DELETE CASCADE,
    unique_chords INT,
    total_measures INT,
    avg_note_density FLOAT,
    repetition_score FLOAT,
    avg_fret_position FLOAT,
    chord_entropy FLOAT
);