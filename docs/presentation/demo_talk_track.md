# RepoQuest Demo Talk Track

Target duration: 90 seconds.

## Opening

"This is RepoQuest. It turns an unfamiliar repo into a guided onboarding quest."

"The problem is simple: when developers join a new codebase, they waste time figuring out what kind of project it is, where the entry points are, and what files matter first."

## Start Demo

"For the demo, I will use the bundled mini travel planner repo. It is a small React and FastAPI full-stack app, so we get a clear frontend, backend, API, model, and test story."

Action:
Select demo repo and click Generate Quest.

## Overview

"RepoQuest starts with deterministic static analysis. It scans files safely, detects frameworks, classifies roles, extracts routes, builds imports, and generates an onboarding path."

"Here it identifies the repo as a full-stack web application and shows evidence for React, Vite, and FastAPI."

If AI is enabled:
"Because AI is configured, AI Fusion then runs after the deterministic pass. It either confirms the result or proposes an override, but only with cited file evidence."

## Architecture

"Next, RepoQuest creates an architecture map. This is the part a new contributor usually has to build in their head."

"The graph shows how the frontend app, pages, components, API client, backend routes, services, models, and tests relate."

## Reading Path

"Instead of telling someone to browse randomly, RepoQuest gives a 30-minute reading path."

"It starts with context, then entry points, then routes and business logic, then models, frontend, and tests."

## Component Card

"Component cards explain why a file matters, what it connects to, what routes or components were detected, and what tests would be useful."

"This is exactly the kind of handoff a new contributor or AI coding assistant needs."

## Quiz

"RepoQuest also generates a quiz. This turns onboarding from passive reading into defense mode: can you answer where the route lives, where the API client is, and what file you would edit next?"

## Export

"Finally, RepoQuest exports the whole onboarding guide as Markdown, so the result is not trapped in the app. You can commit it, share it, or hand it to IBM Bob for follow-up work."

## Close

"RepoQuest is safe and deterministic by default, but when AI is configured it becomes an AI-first hybrid analyzer. The deterministic layer produces evidence. AI Fusion improves interpretation. Together, they make repo onboarding faster, clearer, and more actionable."

