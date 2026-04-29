# Skill: Transcription Router

## Purpose

Interpret a transcript or OCR dump and route segments to the correct
repository path.

## Inputs

- Video transcript
- OCR text from frames
- User-provided file or directory context

## Outputs

- Candidate target paths
- Structured notes grouped by destination file
- Confidence notes for ambiguous mappings

## Rules

1. Prefer exact filenames mentioned in the media.
2. Fall back to directory role matching when filenames are incomplete.
3. Preserve uncertain snippets as notes instead of forcing code generation.
