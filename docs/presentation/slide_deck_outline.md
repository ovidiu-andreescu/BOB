# RepoQuest Slide Deck Outline

## Slide 1: Title

**RepoQuest**

Turn an unfamiliar repo into an onboarding quest.

Speaker note:
RepoQuest helps developers understand small unfamiliar codebases faster by converting repository structure into a guided journey.

## Slide 2: The Problem

**Onboarding to a repo is slow and messy**

- Developers do not know where to start.
- Architecture is hidden across files.
- Entry points, routes, models, and tests are easy to miss.
- New contributors ask the same questions repeatedly.
- Generic chatbots can hallucinate or require external setup.

Speaker note:
The first 30 minutes in a new repo are often wasted on orientation rather than useful work.

## Slide 3: The Solution

**RepoQuest creates a guided onboarding map**

- project fingerprint
- framework detection
- entry points
- architecture map
- dependency graph
- reading path
- component cards
- quiz
- Markdown export
- optional AI Fusion

Speaker note:
RepoQuest converts raw repo structure into a practical contributor guide.

## Slide 4: How It Works

**Deterministic evidence first, AI interpretation second**

1. Safe scan
2. Framework and file role detection
3. Route and import extraction
4. Architecture and dependency graphs
5. Reading path and component cards
6. Quiz and export
7. Optional AI Fusion validation

Speaker note:
The deterministic layer produces the evidence. AI Fusion can improve interpretation, but only with cited evidence.

## Slide 5: Safety Model

**Safe by default**

- no uploaded code execution
- no dependency installation
- no GitHub OAuth
- no database
- no secrets required for default demo
- ZIP slip protection
- file size and scan limits
- binary file skipping

Speaker note:
RepoQuest is designed for hackathon demos and safe repository uploads.

## Slide 6: Demo Flow

**One click to generate the quest**

1. Select bundled demo repo.
2. Click Generate Quest.
3. Show full-stack fingerprint.
4. Show architecture map.
5. Show reading path.
6. Open a component card.
7. Show quiz.
8. Export guide.

Speaker note:
The bundled demo repo avoids credentials and lets judges see the whole value in under two minutes.

## Slide 7: AI Fusion

**AI is a first-class analyzer when configured**

- Runs after deterministic analysis.
- Confirms or challenges project classification.
- Can override interpretation-level conclusions.
- Adds architecture, reading, and component notes.
- Must cite existing files.
- Cannot rewrite scanner facts.

Speaker note:
This is not AI pasted on top. AI Fusion is connected to the deterministic pipeline and validated against its evidence.

## Slide 8: What Judges Should Notice

**RepoQuest is useful immediately**

- A new contributor gets a map.
- A reviewer gets context.
- A team gets onboarding documentation.
- An AI coding assistant gets better prompts.
- The whole app works without accounts or credentials.

Speaker note:
RepoQuest turns discovery into a repeatable artifact, not a one-off conversation.

## Slide 9: Built With IBM Bob

**IBM Bob helped build RepoQuest**

- scaffolding
- scanner and ZIP safety
- framework rules
- graphs and routes
- Streamlit UI
- tests
- documentation
- code review and iteration

Speaker note:
Bob was used during development, not as a required runtime dependency.

## Slide 10: Closing

**RepoQuest turns repo confusion into contributor confidence**

Default mode:

- deterministic
- safe
- fast
- deployable

Optional AI mode:

- evidence-grounded
- validation-gated
- more comprehensive

Speaker note:
RepoQuest helps a developer answer the most important question in a new repo: where do I start?

