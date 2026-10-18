# radiofed

A Python-based data and ML pipeline for working with MIDI and the Million Song Dataset (MSD) for music analysis, feature extraction, and model experimentation.

## Overview

`radiofed` is built to ingest large music corpora, enrich them with metadata, and produce structured features that can feed recommender systems, music analysis workflows, or experimental ML pipelines. The current repo focuses on MIDI ingest, metadata enrichment, and dataset preparation for research and modeling work.

## Why this repository exists

The project sits at the intersection of data engineering and music informatics:
- ingest MIDI files into a relational database for downstream analysis
- align song metadata with public MSD references
- compute musical features from timing, pitch, chord, and key information
- support repeatable, batch-oriented dataset preparation for experiments

## Dataset sources

### Core dataset
- Colin Raffel. "Learning-Based Methods for Comparing Sequences, with Applications to Audio-to-MIDI Alignment and Matching". PhD Thesis, 2016. https://colinraffel.com/projects/lmd/ -> LMD-matched
- Thierry Bertin-Mahieux, Daniel P. W. Ellis, Brian Whitman, and Paul Lamere. "The Million Song Dataset". In Proceedings of the 12th International Society for Music Information Retrieval Conference, pages 591–596, 2011.

### Metadata sources
- Artist metadata: `msd_summary_file.h5` → labrosa.ee.columbia.edu/millionsong/pages/getting-dataset
- Genre metadata: `msd_tagtraum_cd2.cls` → tagtraum.com/msd_genre_datasets.html

## Repository layout

- `src/batch_ingest.py` — batch import of MIDI files into the database
- `src/ingest.py` — per-file MIDI parsing and structured song/measure/event ingestion
- `src/enrich_metadata.py` — attach song metadata and genre labels from MSD files
- `src/feature_extraction.py` — compute feature vectors and summary statistics
- `src/db.py` — database connection and schema helpers
- `sql/` — database schema and migration patterns
- `dataset/` — local dataset files for ingestion and experiments

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Ingest a subset or the full corpus

```bash
python src/batch_ingest.py --limit 5000
python src/batch_ingest.py
```

### Add metadata from MSD files

```bash
python src/enrich_metadata.py --h5 /path/to/msd_summary_file.h5 --genres /path/to/msd_tagtraum_cd2.cls
```

## Current workflow

This repo is optimized for reproducible, batch-style research pipelines:
1. place a MIDI dataset under `dataset/`
2. ingest rows into the database with `batch_ingest.py`
3. enrich records with MSD metadata and genre labels
4. compute features for modeling or analysis
5. iterate on experiments with cleaner, queryable data

## Notes

The project is designed as a reusable foundation for music-data experiments rather than a finished application. It is intentionally focused on ingest, enrichment, and feature preparation so that higher-level modeling work can build on a solid, inspectable dataset pipeline.
