# TODO
- [ ] Build chord_transitions pivot table for clustering
  - Per-song 7×7 transition probability matrix (scale degrees 1–7), flattened to 49 features
  - Query: `SELECT song_id, from_degree, to_degree, transition_count::float / SUM(...) OVER (...) AS prob FROM chord_transitions`
  - Pivot in pandas: `df.pivot(index='song_id', columns=['from_degree','to_degree'], values='prob').fillna(0)`
  - Join to `song_ml_view` on `song_id` for the full feature matrix
