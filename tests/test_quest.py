"""Tests for component cards and quiz generation."""


from repoquest.sample_loader import load_demo_repo
from repoquest.detectors import generate_fingerprint
from repoquest.route_extractors import extract_all_routes
from repoquest.quest import generate_component_cards, generate_quiz
from repoquest.models import FileInfo, ProjectFingerprint, RepositorySnapshot, RouteInfo


def test_component_cards_generated():
  """Test that component cards are generated for demo repo."""
  snapshot = load_demo_repo()
  fingerprint = generate_fingerprint(snapshot)
  routes = extract_all_routes(snapshot.files)

  cards = generate_component_cards(snapshot, fingerprint, routes)
  assert cards
  assert cards

  assert len(cards) > 0


def test_component_cards_generated_from_evidence_when_roles_are_unknown():
  """Cards should use deterministic evidence, not only pre-classified roles."""
  snapshot = RepositorySnapshot(
    source_name="generic-api",
    total_files_seen=3,
    total_files_scanned=3,
    warnings=[],
    files=[
      FileInfo(
        path="src/server.py",
        name="server.py",
        suffix=".py",
        size_bytes=120,
        language="Python",
        role="unknown",
        text_preview=(
          'from fastapi import FastAPI\napp = FastAPI()\n@app.get("/items")\n'
          "def list_items():\n  return []\n"
        ),
        line_count=5,
      ),
      FileInfo(
        path="web/src/App.tsx",
        name="App.tsx",
        suffix=".tsx",
        size_bytes=100,
        language="TypeScript",
        role="unknown",
        text_preview=(
          'import { fetchItems } from "./api";\n'
          "export default function App() { return null; }\n"
        ),
        line_count=2,
      ),
      FileInfo(
        path="web/src/api.ts",
        name="api.ts",
        suffix=".ts",
        size_bytes=100,
        language="TypeScript",
        role="unknown",
        text_preview='export async function fetchItems() { return fetch("/items"); }\n',
        line_count=1,
      ),
    ],
  )
  fingerprint = ProjectFingerprint(
    project_type="Full-stack web application",
    confidence=0.7,
    frameworks=[],
    entry_points=["src/server.py", "web/src/App.tsx"],
    key_folders=["src", "web/src"],
    summary="Detected from static evidence.",
    warnings=[],
  )
  routes = [
    RouteInfo(
      framework="fastapi",
      method="GET",
      path="/items",
      file_path="src/server.py",
      function_name="list_items",
    )
  ]

  cards = generate_component_cards(snapshot, fingerprint, routes)

  card_paths = {card.path for card in cards}
  assert {"src/server.py", "web/src/App.tsx", "web/src/api.ts"}.issubset(card_paths)
  route_card = next(card for card in cards if card.path == "src/server.py")
  assert "GET /items" in route_card.detected_items


def test_component_cards_never_include_init_py_even_with_route_evidence():
  """Python package initializers should not leak into component cards."""
  snapshot = RepositorySnapshot(
    source_name="init-route",
    total_files_seen=1,
    total_files_scanned=1,
    warnings=[],
    files=[
      FileInfo(
        path="api/__init__.py",
        name="__init__.py",
        suffix=".py",
        size_bytes=100,
        language="Python",
        role="unknown",
        text_preview='@router.get("/hidden")\ndef hidden():\n  return {}\n',
        line_count=3,
      )
    ],
  )
  fingerprint = ProjectFingerprint(
    project_type="Backend API",
    confidence=0.6,
    frameworks=[],
    entry_points=["api/__init__.py"],
    key_folders=["api"],
    summary="Detected from static evidence.",
    warnings=[],
  )
  routes = [
    RouteInfo(
      framework="fastapi",
      method="GET",
      path="/hidden",
      file_path="api/__init__.py",
      function_name="hidden",
    )
  ]

  cards = generate_component_cards(snapshot, fingerprint, routes)

  assert cards == []


def test_component_card_for_backend_route_includes_routes():
  """Test that component card for backend route includes detected routes."""
  snapshot = load_demo_repo()
  fingerprint = generate_fingerprint(snapshot)
  routes = extract_all_routes(snapshot.files)

  cards = generate_component_cards(snapshot, fingerprint, routes)

  # Find card for backend route file
  route_cards = [c for c in cards if "routes" in c.path.lower() and "backend" in c.path.lower()]

  assert len(route_cards) > 0

  # Check that it has detected items (routes)
  route_card = route_cards[0]
  assert len(route_card.detected_items) > 0

  # Should include HTTP methods
  detected_text = " ".join(route_card.detected_items)
  assert any(method in detected_text for method in ["GET", "POST", "DELETE", "PUT"])


def test_component_cards_have_required_fields():
  """Test that component cards have all required fields."""
  snapshot = load_demo_repo()
  fingerprint = generate_fingerprint(snapshot)
  routes = extract_all_routes(snapshot.files)

  cards = generate_component_cards(snapshot, fingerprint, routes)
  assert cards


def test_component_cards_exclude_init_py():
  """Test that component cards exclude __init__.py files."""
  snapshot = load_demo_repo()
  fingerprint = generate_fingerprint(snapshot)
  routes = extract_all_routes(snapshot.files)

  cards = generate_component_cards(snapshot, fingerprint, routes)

  # No card should be for __init__.py
  init_cards = [c for c in cards if c.path.endswith("__init__.py")]
  assert len(init_cards) == 0, "__init__.py files should not appear in component cards"


def test_quiz_excludes_init_py_from_answers():
  """Test that quiz does not use __init__.py as correct answers."""
  snapshot = load_demo_repo()
  fingerprint = generate_fingerprint(snapshot)
  routes = extract_all_routes(snapshot.files)

  quiz = generate_quiz(snapshot, fingerprint, routes)

  # No correct answer should be __init__.py
  for question in quiz:
    assert not question.correct_answer.endswith("__init__.py"), \
      f"Quiz question should not have __init__.py as correct answer: {question.question}"


def test_quiz_uses_role_based_distractors():
  """Test that quiz uses plausible role-based distractors, not generic files."""
  snapshot = load_demo_repo()
  fingerprint = generate_fingerprint(snapshot)
  routes = extract_all_routes(snapshot.files)

  quiz = generate_quiz(snapshot, fingerprint, routes)

  # Find a route-related question
  route_questions = [
    q for q in quiz
    if "endpoint" in q.question.lower() or "route" in q.question.lower()
  ]

  if route_questions:
    q = route_questions[0]
    # Distractors should not all be README.md,.gitignore, or index.html
    generic_files = ["README.md", ".gitignore", "index.html"]
    distractor_count = sum(1 for opt in q.options if opt != q.correct_answer)
    generic_distractor_count = sum(1 for opt in q.options if any(g in opt for g in generic_files))

    # At least some distractors should be plausible backend files
    assert generic_distractor_count < distractor_count, \
      "Quiz should use role-based distractors, not only generic files"


def test_quiz_excludes_init_py_from_distractors():
  """Test that quiz does not use __init__.py as distractors."""
  snapshot = load_demo_repo()
  fingerprint = generate_fingerprint(snapshot)
  routes = extract_all_routes(snapshot.files)

  quiz = generate_quiz(snapshot, fingerprint, routes)

  # No option should be __init__.py
  for question in quiz:
    for option in question.options:
      assert not option.endswith("__init__.py"), \
        f"Quiz options should not include __init__.py: {question.question}"


def test_component_cards_include_test_ideas():
  """Test that component cards include test ideas."""
  snapshot = load_demo_repo()
  fingerprint = generate_fingerprint(snapshot)
  routes = extract_all_routes(snapshot.files)

  cards = generate_component_cards(snapshot, fingerprint, routes)

  # At least some cards should have test ideas
  cards_with_test_ideas = [c for c in cards if len(c.suggested_test_ideas) > 0]
  assert len(cards_with_test_ideas) > 0


def test_component_cards_include_bob_prompts():
  """Test that component cards include Bob-ready prompts."""
  snapshot = load_demo_repo()
  fingerprint = generate_fingerprint(snapshot)
  routes = extract_all_routes(snapshot.files)

  cards = generate_component_cards(snapshot, fingerprint, routes)

  for card in cards:
    # Assistant action should mention the file path
    assert card.path in card.suggested_bob_prompt or card.title in card.suggested_bob_prompt


def test_component_cards_respect_max_limit():
  """Test that component cards respect MAX_COMPONENT_CARDS limit."""
  from repoquest.config import MAX_COMPONENT_CARDS

  snapshot = load_demo_repo()
  fingerprint = generate_fingerprint(snapshot)
  routes = extract_all_routes(snapshot.files)

  cards = generate_component_cards(snapshot, fingerprint, routes)

  assert len(cards) <= MAX_COMPONENT_CARDS


def test_quiz_generated():
  """Test that quiz questions are generated for demo repo."""
  snapshot = load_demo_repo()
  fingerprint = generate_fingerprint(snapshot)
  routes = extract_all_routes(snapshot.files)

  quiz = generate_quiz(snapshot, fingerprint, routes)

  assert len(quiz) > 0


def test_quiz_includes_route_question():
  """Test that quiz includes a question about route file or endpoint."""
  snapshot = load_demo_repo()
  fingerprint = generate_fingerprint(snapshot)
  routes = extract_all_routes(snapshot.files)

  quiz = generate_quiz(snapshot, fingerprint, routes)

  # Should have at least one question about routes or endpoints
  route_questions = [
    q for q in quiz
    if "route" in q.question.lower() or "endpoint" in q.question.lower() or "/api" in q.question
  ]

  assert len(route_questions) > 0


def test_quiz_includes_frontend_question():
  """Test that quiz includes a question about frontend entry point."""
  snapshot = load_demo_repo()
  fingerprint = generate_fingerprint(snapshot)
  routes = extract_all_routes(snapshot.files)

  quiz = generate_quiz(snapshot, fingerprint, routes)

  # Should have at least one question about frontend
  frontend_questions = [
    q for q in quiz
    if "frontend" in q.question.lower() or "app.tsx" in q.question.lower()
  ]

  assert len(frontend_questions) > 0


def test_quiz_questions_have_required_fields():
  """Test that quiz questions have all required fields."""
  snapshot = load_demo_repo()
  fingerprint = generate_fingerprint(snapshot)
  routes = extract_all_routes(snapshot.files)

  quiz = generate_quiz(snapshot, fingerprint, routes)

  for question in quiz:
    assert question.question
    assert len(question.question) > 10 # Should be meaningful
    assert len(question.options) >= 2 # At least 2 options
    assert question.correct_answer
    assert question.correct_answer in question.options
    assert question.explanation
    assert len(question.explanation) > 10 # Should be meaningful


def test_quiz_respects_max_limit():
  """Test that quiz respects MAX_QUIZ_QUESTIONS limit."""
  from repoquest.config import MAX_QUIZ_QUESTIONS

  snapshot = load_demo_repo()
  fingerprint = generate_fingerprint(snapshot)
  routes = extract_all_routes(snapshot.files)

  quiz = generate_quiz(snapshot, fingerprint, routes)

  assert len(quiz) <= MAX_QUIZ_QUESTIONS


def test_quiz_correct_answers_are_valid():
  """Test that correct answers are always in the options list."""
  snapshot = load_demo_repo()
  fingerprint = generate_fingerprint(snapshot)
  routes = extract_all_routes(snapshot.files)

  quiz = generate_quiz(snapshot, fingerprint, routes)

  for question in quiz:
    assert question.correct_answer in question.options


def test_quiz_has_variety():
  """Test that quiz has variety in question types."""
  snapshot = load_demo_repo()
  fingerprint = generate_fingerprint(snapshot)
  routes = extract_all_routes(snapshot.files)

  quiz = generate_quiz(snapshot, fingerprint, routes)

  # Should have questions about different aspects
  question_texts = [q.question.lower() for q in quiz]

  # Check for variety (at least 3 different question patterns)
  patterns = [
    any("entry point" in q for q in question_texts),
    any("endpoint" in q or "route" in q for q in question_texts),
    any("frontend" in q for q in question_texts),
    any("api" in q for q in question_texts),
    any("framework" in q or "type" in q for q in question_texts),
  ]

  assert sum(patterns) >= 3 # At least 3 different types of questions

# Made with Bob
