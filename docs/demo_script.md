# RepoQuest Demo Script

**Duration:** 1-2 minutes  
**Audience:** Hackathon judges  
**Goal:** Demonstrate RepoQuest's value proposition and key features

## Opening (10 seconds)

"This is **RepoQuest**, a tool that helps developers onboard to unfamiliar codebases faster."

"Instead of spending hours figuring out where to start, RepoQuest turns a repository into a guided onboarding journey."

## Setup (10 seconds)

"For this demo, I'll use our bundled demo repository - a small React + FastAPI travel planner app."

*Click "Use demo repo" in sidebar*

"This avoids asking judges to connect GitHub or upload files, but RepoQuest also supports secure ZIP uploads with path traversal protection."

## Analysis (20 seconds)

*Click "Generate Onboarding Quest"*

"RepoQuest scans the repository using deterministic static analysis - no AI runtime, no external APIs."

*Wait for analysis to complete (~3-5 seconds)*

"Analysis complete! Let's explore what it found."

## Overview Tab (15 seconds)

*Navigate to Overview tab*

"RepoQuest detected this as a **full-stack web application** with 87% confidence."

"It found React + Vite on the frontend and FastAPI on the backend."

*Point to frameworks section*

"Each detection includes evidence - like finding 'from fastapi import FastAPI' in the code."

## Architecture Map Tab (15 seconds)

*Navigate to Architecture Map tab*

"Here's a human-friendly architecture map showing how components connect."

*Point to graph*

"Frontend components call the API client, which connects to backend routes, services, and models."

*Scroll to routes table*

"RepoQuest also extracted all API endpoints - GET /trips, POST /trips, DELETE /trips/{id}."

## Reading Path Tab (15 seconds)

*Navigate to Reading Path tab*

"Instead of randomly exploring files, RepoQuest suggests a 30-minute reading path."

*Expand first item*

"Start with the README, then the backend entry point, then routes, services, models, and finally frontend components."

"Each item explains why you should read it and what to look for."

## Components Tab (10 seconds)

*Navigate to Components tab*

*Expand backend/routes/trips.py card*

"Component cards provide detailed information about important files."

"This route file connects to the recommendations service and trip model."

"RepoQuest suggests test ideas and even provides an IBM Bob prompt for deeper exploration."

## Tests Tab (10 seconds)

*Navigate to Tests tab*

"RepoQuest identifies test files separately and suggests additional test coverage."

"It detected pytest tests and shows what's being tested."

## Quiz Tab (10 seconds)

*Navigate to Quest & Quiz tab*

"The onboarding quiz verifies understanding."

*Show a question*

"Questions are generated based on the actual repository structure - like 'Which file defines the /trips endpoint?'"

## Documentation Tab (10 seconds)

*Navigate to Documentation tab*

*Click "Generate Documentation"*

"RepoQuest can preview README and config files, then generate a comprehensive onboarding guide."

*Show preview*

"The guide includes everything we just explored - frameworks, architecture, reading path, component cards, and quiz."

## Export Tab (10 seconds)

*Navigate to Export tab*

"Finally, download the guide as a Markdown file."

*Click download button*

"This can be committed to the repo, shared with new team members, or used during code reviews."

## Built with IBM Bob Tab (10 seconds)

*Navigate to Built with IBM Bob tab*

"RepoQuest was built with IBM Bob as a development partner."

"Bob helped with scaffolding, implementation, testing, and documentation."

"But here's the key: **RepoQuest doesn't use AI at runtime**."

"All analysis is deterministic - static file scanning, pattern matching, and heuristics."

"No credentials, no external APIs, no hidden network calls."

## Closing (10 seconds)

"RepoQuest demonstrates how AI can assist development while keeping the final product fast, predictable, and auditable."

"It turns an unfamiliar repo into a guided onboarding journey in seconds."

"Thank you!"

---

## Key Points to Emphasize

1. **Problem:** Developers waste time figuring out where to start in unfamiliar codebases
2. **Solution:** Guided onboarding journey with reading path, component cards, and quiz
3. **Security:** ZIP upload protection, no code execution
4. **Deterministic:** No runtime AI, all analysis is static and explainable
5. **Actionable:** Provides specific next steps and IBM Bob prompts
6. **Exportable:** Generates standalone Markdown guides

## Backup Talking Points

If time allows or questions arise:

### ZIP Upload Safety
"RepoQuest validates ZIP uploads against path traversal attacks, rejects oversized files, and never executes uploaded code."

### Framework Detection
"Detection is based on evidence - finding specific imports, config files, or decorators. Each finding includes confidence scores."

### Reading Path Logic
"The reading path prioritizes README first, then entry points, then routes/controllers, then services, then models, then frontend, then tests."

### Component Cards
"Cards are generated based on file role, detected routes, imports, and connections. Test ideas are heuristic-based."

### IBM Bob Integration
"Bob helped write the code, tests, and docs. The app itself is deterministic and requires no AI at runtime."

## Demo Tips

1. **Practice timing** - Aim for 90 seconds, max 2 minutes
2. **Focus on value** - Show how it helps developers, not just features
3. **Be confident** - The demo repo is designed to showcase all features
4. **Handle errors gracefully** - If something fails, explain the safety features
5. **End strong** - Emphasize deterministic analysis and IBM Bob partnership

## Common Questions

**Q: Does it work with large repositories?**  
A: RepoQuest is optimized for small to medium repos (under 600 files). For larger repos, it scans the first 600 files and provides warnings.

**Q: Can it detect custom frameworks?**  
A: RepoQuest detects common frameworks. For custom patterns, it falls back to generic file role classification and still provides useful reading paths.

**Q: Is the analysis accurate?**  
A: RepoQuest uses heuristics and shows confidence scores. It's designed as a starting point - developers should verify findings by reading the actual code.

**Q: Why not use AI at runtime?**  
A: Deterministic analysis is faster, more predictable, requires no credentials, and is fully auditable. IBM Bob helped build it, but the app itself is pure static analysis.

---

*This demo script was created with IBM Bob's assistance.*
