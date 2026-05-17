# RepoQuest Submission Blurb

## Short Submission

RepoQuest helps developers onboard to unfamiliar codebases faster by turning repo structure into a guided quest. It uses deterministic static analysis to detect the project type, frameworks, entry points, routes, imports, architecture, reading path, component cards, tests, quiz questions, and an exportable Markdown onboarding guide. Optional AI Fusion runs after the deterministic pass to confirm or improve interpretation with cited evidence and validation gates.

## Longer Submission

Developers waste time figuring out where to start in unfamiliar codebases. RepoQuest solves this by generating an onboarding journey from a small repo: project fingerprint, architecture map, dependency graph, 30-minute reading path, component/file cards, onboarding quiz, test intelligence, work plans, agent-ready prompts, and a Markdown export.

RepoQuest is safe by default. It never executes uploaded code, never installs uploaded dependencies, and does not require credentials for the default demo. ZIP uploads are scanned defensively with path traversal checks, file limits, and binary skipping.

The app also includes optional AI Fusion. When AI is configured, RepoQuest first builds deterministic evidence, then AI Fusion audits the interpretation. AI can confirm or challenge conclusions like project type or architecture notes, but only with cited scanned files and validation gates. Deterministic facts such as scanned files, routes, imports, skipped files, and safety warnings remain authoritative.

RepoQuest was built with IBM Bob as a development partner, but it does not require IBM Bob at runtime. The result is a Streamlit app that is demoable in under two minutes and deployable without external infrastructure.

## One-Line Pitch

RepoQuest turns an unfamiliar repo into a contributor-ready onboarding quest.

## Three Bullet Pitch

- Scans small repos safely and deterministically.
- Generates architecture, reading paths, component cards, quiz, and Markdown exports.
- Uses optional AI Fusion to improve interpretation without giving up evidence, validation, or safety.

