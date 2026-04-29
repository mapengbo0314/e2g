# Workflow: Video Transcriber

## Goal

Populate project files from screen recordings, walkthrough videos, and file
explanations.

## Steps

1. Ingest the source video and collect timestamps.
2. Run speech transcription and frame OCR.
3. Detect filenames, directories, architecture references, and code snippets.
4. Route extracted content through `transcription_router`.
5. Draft content in the mapped file using the repository template rules.
6. Flag anything uncertain for human confirmation.

## Primary outputs

- Structured transcript
- File-to-content mapping
- Ready-to-apply source or documentation edits
