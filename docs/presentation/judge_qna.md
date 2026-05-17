# RepoQuest Judge Q&A

## What is RepoQuest?

RepoQuest is a Streamlit web app that turns a small unfamiliar codebase into a guided onboarding journey. It detects the project type, maps architecture, identifies key files, creates a reading path, generates component cards, builds a quiz, and exports a Markdown guide.

## Is this just a chatbot?

No. RepoQuest is not a generic repo chatbot. It is a static codebase analyzer with deterministic evidence and optional AI Fusion. The app generates concrete artifacts: graphs, reading paths, cards, quizzes, reports, and assistant-ready workflows.

## Does it execute uploaded code?

No. RepoQuest never executes uploaded code, never installs uploaded dependencies, and never imports uploaded modules. Uploads are scanned statically.

## How do ZIP uploads stay safe?

RepoQuest validates ZIP files before scanning:

- rejects oversized ZIPs
- rejects absolute paths
- rejects `..` traversal
- skips unsupported binary files
- limits total files scanned
- limits per-file size
- decodes text safely

## What does AI do?

AI Fusion runs only when configured. It receives bounded deterministic context and capped snippets. It can confirm or challenge interpretation-level conclusions such as project type, architecture notes, reading notes, component notes, risks, and recommendations.

## Can AI hallucinate?

It can try, but RepoQuest validates AI output before trusting it. AI overrides must cite existing scanned files. If AI references missing files, lacks evidence, claims tests were run, or asks to execute uploaded code, the output is rejected or downgraded.

## Why not use AI for everything?

Deterministic analysis is faster, auditable, and safe by default. AI is valuable for synthesis, but the product should not depend on a model to know what files exist or what routes were extracted.

RepoQuest uses the right tool for each job:

- deterministic code for evidence
- AI for interpretation

## What does IBM Bob do at runtime?

Nothing. IBM Bob was used during development as the coding partner. RepoQuest does not require IBM Bob at runtime.

## What did IBM Bob help build?

Bob helped with:

- scaffolding
- ZIP scanner
- framework detection rules
- route extraction
- import graph
- Streamlit UI
- tests
- documentation
- AI assistant foundation
- AI Fusion iteration

## What is the target user?

The primary user is a developer onboarding to a small unfamiliar repo. Secondary users include hackathon teams, reviewers, maintainers, and developers preparing work for IBM Bob or another AI coding assistant.

## What are the limitations?

RepoQuest is designed for small prototype-sized repositories. It is not a full static analyzer, security scanner, monorepo platform, or semantic code search engine.

Current limits include:

- max ZIP size: 25 MB
- max scanned files: 600
- max file preview size
- heuristic framework detection
- no runtime execution

## Why Streamlit?

Streamlit makes the app easy to demo, easy to deploy, and suitable for Streamlit Community Cloud. It supports uploads, tables, tabs, download buttons, and Graphviz rendering without extra infrastructure.

## What is the main demo takeaway?

RepoQuest turns repo confusion into a contributor-ready map.

It answers:

- What kind of codebase is this?
- Where do I start?
- What connects to what?
- What should I read first?
- What should I test?
- What should I ask IBM Bob to do next?

