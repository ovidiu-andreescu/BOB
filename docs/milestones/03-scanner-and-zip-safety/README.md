# Milestone 3 - Scanner And ZIP Safety

Purpose: track safe directory and ZIP scanning work.

Status: implemented for the MVP. Keep future UI work aligned with these safety boundaries.

## Goal

Safely scan local demo repos and uploaded ZIP files without executing or installing anything.

## Required Files

- `repoquest/scanner.py`
- `repoquest/zip_safety.py`
- `repoquest/sample_loader.py`
- `tests/test_scanner.py`
- `tests/test_zip_safety.py`
- `tests/fixtures/`

## Implementation Tasks

- Scan directories with ignore rules and file limits.
- Implement ZIP scanning directly through `zipfile.ZipFile`.
- Reject ZIPs larger than `MAX_ZIP_SIZE_MB`.
- Reject absolute paths.
- Reject paths containing `..`.
- Reject paths that would escape a target directory if extracted.
- Skip unsupported, binary, oversized, and ignored files.
- Limit total scanned files.
- Decode text safely with UTF-8 and replacement fallback.
- Never execute uploaded code.
- Never install uploaded dependencies.
- Never import uploaded modules.

## Tests/Checks

- Normal directory scan.
- Normal ZIP scan.
- ZIP slip path rejection.
- Absolute ZIP path rejection.
- Max file count handling.
- Binary/unsupported file skip.
- Oversized file skip.
- Friendly warnings for skipped files or scan limits.

## Exit Criteria

- Upload path is safe enough to enable in the UI.
- Bad ZIP input fails gracefully without raw tracebacks.

## Carry Forward To UI

- The upload UI should show limits before upload.
- ZIP errors should be user-friendly and should not expose raw tracebacks in cloud mode.
- The scanner should remain static-analysis only: no dependency installation, imports, or script execution.
