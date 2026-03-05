# radiofed
ML testing


# Dataset from:
- Colin Raffel. "Learning-Based Methods for Comparing Sequences, with Applications to Audio-to-MIDI Alignment and Matching". PhD Thesis, 2016. https://colinraffel.com/projects/lmd/ -> LMD-matched
- Thierry Bertin-Mahieux, Daniel P. W. Ellis, Brian Whitman, and Paul Lamere. "The Million Song Dataset". In Proceedings of the 12th International Society for Music Information Retrieval Conference, pages 591–596, 2011.

# Metadata from MSD:
- Artist metadata `msd_summary_file.h5` → labrosa.ee.columbia.edu/millionsong/pages/getting-dataset
- Genre metadata `msd_tagtraum_cd2.cls` → tagtraum.com/msd_genre_datasets.html

# Loading data
- Ingest: `src/batch_ingest.py --limit 5000` or `src/batch_ingest.py` for all
- Metadata: `python src/enrich_metadata.py --h5 /path/to/msd_summary_file.h5 --genres /path/to/msd_tagtraum_cd2.cls`
