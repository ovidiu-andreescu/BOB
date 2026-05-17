# AI Fusion Story

## Short Version

RepoQuest uses deterministic analysis to gather evidence, then uses AI Fusion to interpret that evidence.

The AI does not replace the deterministic analyzer. It plugs into it.

## Why AI Fusion Exists

Pure deterministic rules are fast and transparent, but they can be too rigid. They might detect the right files while still under-explaining what the project actually is.

AI is better at synthesis:

- summarizing architecture
- judging whether a classification feels right
- explaining why a file matters
- spotting missing context
- recommending next steps

RepoQuest combines both:

- deterministic analysis for facts
- AI Fusion for interpretation

## Pipeline

1. RepoQuest scans the repo safely.
2. It classifies files and detects frameworks.
3. It extracts routes and imports.
4. It generates graphs, reading paths, component cards, tests, workflows, and quiz.
5. If AI is configured, AI Fusion receives a bounded context pack.
6. AI Fusion returns structured JSON.
7. RepoQuest validates that JSON against the scanned evidence.
8. Valid AI conclusions are shown in the app.
9. Invalid or unsupported AI output is rejected or shown as disagreement.

## What AI Can Override

AI Fusion can override interpretation-level outputs:

- project type
- framework label or confidence notes
- entry point ranking
- architecture summary
- reading path notes
- component notes
- risks
- recommendations

## What AI Cannot Override

AI Fusion cannot rewrite deterministic facts:

- scanned file list
- extracted route table
- import edges
- skipped files
- ZIP safety warnings
- file size limits
- upload constraints

## Trust Gates

Every AI override must:

- be strict JSON
- cite existing scanned file paths
- avoid claiming tests were run
- avoid telling RepoQuest to execute uploaded code
- avoid secrets
- meet confidence thresholds

Project-type overrides require:

- confidence of at least 0.75
- at least two evidence paths
- higher confidence than a strong deterministic result

## Demo Explanation

Use this line:

"RepoQuest does not ask AI to magically understand the repo from nowhere. The deterministic analyzer builds the evidence pack first. Then AI Fusion audits the conclusion, and RepoQuest only accepts AI changes that cite real files and pass validation."

## Why This Is Strong

This makes AI feel first-class without making the product reckless.

The product story becomes:

- reliable facts
- richer interpretation
- safer AI
- better onboarding

