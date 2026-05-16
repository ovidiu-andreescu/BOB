# Milestone 18 - Testable AI Evals And Trust Gates

Purpose: make optional AI mode measurable, reject invalid output, and keep the product trustworthy.

MVP 2 phase: Optional AI Code Assistant.

## Goal

Add validation, eval fixtures, and UI trust signals before assistant output is treated as useful.

Evals must work for mock, cloud, async service, and local model providers. CI should rely on deterministic mock fixtures, not live model calls.

## Trust Gates

- Schema validation.
- Evidence path validation.
- Nonexistent file citation rejection.
- Missing-evidence downgrade.
- No unsupported claims about code execution.
- No unsupported claims about test execution.
- No secrets in output.
- Confidence thresholds.
- Clear fallback if validation fails.

## Eval Fixtures

- React + FastAPI demo repo.
- Unknown small repo.
- Documentation-only repo.
- Repo with tests but no app code.
- Repo with misleading README.
- Repo with scan warnings/skipped files.
- Repo where mock AI cites nonexistent files.
- Repo where mock AI omits evidence.
- Local model style responses with verbose/non-schema text.
- Async service timeout/error responses.

## Metrics

- Schema validity rate.
- Evidence coverage rate.
- Unsupported-claim count.
- Hallucinated file path count.
- Missing-evidence recommendation count.
- User-facing fallback quality.

## Tests/Checks

- Mock malformed assistant output is rejected.
- Local-model malformed output is rejected.
- Output referencing nonexistent files is rejected.
- Output without evidence is downgraded or hidden.
- Output claiming tests passed without verification is rejected or labeled unsupported.
- Deterministic MVP still passes with assistant mode disabled.

## Exit Criteria

- Assistant output cannot silently bypass validation.
- Failed assistant calls do not break deterministic analysis.
- The UI clearly shows when a suggestion is AI-assisted and whether it passed evidence checks.
- AI mode is testable in CI without network access.
- Provider-specific failures show provider/model labels and do not affect deterministic analysis.
