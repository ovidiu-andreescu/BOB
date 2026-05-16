"""Generate component cards and quiz questions for repository onboarding."""

from dataclasses import replace

from repoquest.models import (
  RepositorySnapshot,
  ProjectFingerprint,
  FileInfo,
  RouteInfo,
  ComponentCard,
  QuizQuestion,
)
from repoquest.config import MAX_COMPONENT_CARDS, MAX_QUIZ_QUESTIONS
from repoquest.response_templates import (
  format_likely_role,
  get_assistant_action_for_file,
  get_connection_target_roles,
  get_distractor_roles,
  get_test_ideas_for_file,
  get_why_it_matters,
)


CARD_ROLE_PRIORITY = [
  "entrypoint",
  "backend_route",
  "backend_service",
  "model",
  "frontend_page",
  "api_client",
  "frontend_component",
]


def _is_init_file(file_info: FileInfo) -> bool:
  """Return whether a file is a Python package initializer."""
  return file_info.name == "__init__.py" or file_info.path.endswith("/__init__.py")


def _contains_any(text: str, needles: tuple[str, ...]) -> bool:
  """Return whether text contains any of the provided needles."""
  return any(needle in text for needle in needles)


def _infer_component_card_role(
  file_info: FileInfo,
  fingerprint: ProjectFingerprint,
  routes: list[RouteInfo],
) -> str | None:
  """Infer a card-worthy role from deterministic evidence.

  This is intentionally conservative and generic. It lets component cards survive
  upstream role-classification gaps without adding demo-specific path checks.
  """
  if file_info.skipped or _is_init_file(file_info):
    return None

  if file_info.role in CARD_ROLE_PRIORITY:
    return file_info.role

  route_files = {route.file_path for route in routes}
  if file_info.path in route_files:
    return "backend_route"

  if file_info.path in set(fingerprint.entry_points):
    return "entrypoint"

  path_lower = file_info.path.lower()
  name_lower = file_info.name.lower()
  text = file_info.text_preview

  if _contains_any(text, ("@app.get", "@app.post", "@app.put", "@app.delete",
      "@router.get", "@router.post", "@router.put", "@router.delete",
      "@app.route")):
    return "backend_route"

  if _contains_any(text, ("express()", "app.get(", "app.post(", "router.get(", "router.post(")):
    return "backend_route"

  if "services/" in path_lower or "/service/" in path_lower:
    return "backend_service"

  if (
    "models/" in path_lower
    or "/schemas/" in path_lower
    or name_lower in ("models.py", "schema.py", "schemas.py")
  ):
    return "model"

  if "pages/" in path_lower or (
    "/app/" in path_lower and name_lower in ("page.tsx", "page.jsx")
  ):
    return "frontend_page"

  if "components/" in path_lower:
    return "frontend_component"

  if name_lower in ("app.tsx", "app.jsx", "main.tsx", "main.jsx", "index.tsx", "index.jsx"):
    return "entrypoint"

  if (
    "api" in name_lower
    or "client" in name_lower
    or _contains_any(text, ("fetch(", "axios.", "XMLHttpRequest"))
  ) and file_info.suffix.lower() in (".js", ".jsx", ".ts", ".tsx"):
    return "api_client"

  return None


def _build_effective_roles(
  snapshot: RepositorySnapshot,
  fingerprint: ProjectFingerprint,
  routes: list[RouteInfo],
) -> dict[str, str]:
  """Build deterministic card/quiz roles without mutating the snapshot."""
  roles = {}
  for file_info in snapshot.files:
    role = _infer_component_card_role(file_info, fingerprint, routes)
    if role:
      roles[file_info.path] = role
  return roles


def _with_effective_role(file_info: FileInfo, role: str) -> FileInfo:
  """Return a FileInfo view with the card role applied."""
  if file_info.role == role:
    return file_info
  return replace(file_info, role=role)


def _find_connected_files(
  file_info: FileInfo,
  snapshot: RepositorySnapshot,
  effective_roles: dict[str, str] | None = None,
) -> list[str]:
  """Find files that are likely connected to this file.

  Uses simple heuristics based on imports, path structure, and naming.
  """
  connected = []
  effective_roles = effective_roles or {}
  file_name_base = file_info.name.replace(file_info.suffix, "").lower()

  target_roles = get_connection_target_roles(file_info.role)
  for other in snapshot.files:
    other_role = effective_roles.get(other.path, other.role)
    if (
      other.skipped
      or _is_init_file(other)
      or other.path == file_info.path
      or other_role not in target_roles
    ):
      continue

    if other_role in ("frontend_component", "api_client", "backend_route"):
      connected.append(other.path)
    elif file_name_base in other.path.lower():
      connected.append(other.path)

  # Check for explicit imports in the text preview
  if file_info.text_preview:
    for other in snapshot.files:
      if other.skipped or _is_init_file(other) or other.path == file_info.path:
        continue

      # Simple check: if the other file's name appears in this file's content
      other_name_base = other.name.replace(other.suffix, "")
      if other_name_base in file_info.text_preview:
        if other.path not in connected:
          connected.append(other.path)

  return connected[:5] # Limit to top 5 connections


def _generate_detected_items(file_info: FileInfo, routes: list[RouteInfo]) -> list[str]:
  """Generate a list of detected items for this file (routes, functions, etc.)."""
  items = []

  # For backend routes, list the detected routes
  if file_info.role == "backend_route":
    file_routes = [r for r in routes if r.file_path == file_info.path]
    for route in file_routes[:5]: # Limit to 5
      items.append(f"{route.method} {route.path}")

  # For other files, we could detect functions, classes, etc.
  # For now, keep it simple and just note the role
  if not items and file_info.role != "unknown":
    items.append(f"Classified as {file_info.role}")

  return items


def _generate_test_ideas(file_info: FileInfo, routes: list[RouteInfo]) -> list[str]:
  """Generate suggested test ideas for this file."""
  return get_test_ideas_for_file(file_info, routes)


def _generate_bob_prompt(file_info: FileInfo, routes: list[RouteInfo]) -> str:
  """Generate a suggested AI assistant action for this file."""
  return get_assistant_action_for_file(file_info, routes)


def generate_component_cards(
  snapshot: RepositorySnapshot,
  fingerprint: ProjectFingerprint,
  routes: list[RouteInfo],
) -> list[ComponentCard]:
  """Generate component cards for important files.

  Args:
    snapshot: The repository snapshot
    fingerprint: The project fingerprint
    routes: Detected API routes

  Returns:
    List of ComponentCard objects for important files
  """
  cards = []
  effective_roles = _build_effective_roles(snapshot, fingerprint, routes)

  # Collect candidates by role (exclude __init__.py)
  candidates_by_role = {role: [] for role in CARD_ROLE_PRIORITY}

  for file_info in snapshot.files:
    if file_info.skipped or _is_init_file(file_info):
      continue

    role = effective_roles.get(file_info.path)
    if role in CARD_ROLE_PRIORITY:
      candidates_by_role[role].append(file_info)

  # Generate cards, prioritizing by role
  for role in CARD_ROLE_PRIORITY:
    for file_info in sorted(candidates_by_role[role], key=lambda f: f.path):
      if len(cards) >= MAX_COMPONENT_CARDS:
        break

      effective_file = _with_effective_role(file_info, role)

      # Generate card title
      title = file_info.name

      why_it_matters = get_why_it_matters(effective_file)

      # Find connections
      connected_to = _find_connected_files(effective_file, snapshot, effective_roles)

      # Generate detected items
      detected_items = _generate_detected_items(effective_file, routes)

      # Generate test ideas
      test_ideas = _generate_test_ideas(effective_file, routes)

      # Generate assistant action
      bob_prompt = _generate_bob_prompt(effective_file, routes)

      cards.append(ComponentCard(
        path=file_info.path,
        title=title,
        role=format_likely_role(role),
        why_it_matters=why_it_matters,
        connected_to=connected_to,
        detected_items=detected_items,
        suggested_test_ideas=test_ideas,
        suggested_bob_prompt=bob_prompt,
      ))

    if len(cards) >= MAX_COMPONENT_CARDS:
      break

  return cards


def generate_quiz(
  snapshot: RepositorySnapshot,
  fingerprint: ProjectFingerprint,
  routes: list[RouteInfo],
) -> list[QuizQuestion]:
  """Generate quiz questions for onboarding verification.

  Args:
    snapshot: The repository snapshot
    fingerprint: The project fingerprint
    routes: Detected API routes

  Returns:
    List of QuizQuestion objects
  """
  questions = []
  effective_roles = _build_effective_roles(snapshot, fingerprint, routes)

  # Helper to filter out __init__.py and get good files
  def get_good_files(role: str) -> list[FileInfo]:
    return [
      _with_effective_role(f, role)
      for f in snapshot.files
      if effective_roles.get(f.path) == role
      and not f.skipped
      and not _is_init_file(f)
    ]

  # Find key files for questions
  entry_points = get_good_files("entrypoint")
  backend_routes = get_good_files("backend_route")
  api_clients = get_good_files("api_client")
  models = get_good_files("model")
  frontend_pages = get_good_files("frontend_page")
  frontend_components = get_good_files("frontend_component")
  backend_services = get_good_files("backend_service")

  # Helper to get plausible distractors based on role
  def get_distractors(correct_file: FileInfo, count: int = 3) -> list[str]:
    """Get plausible distractor files based on the correct file's role."""
    distractors = []

    related_roles = get_distractor_roles(correct_file.role)
    if related_roles:
      role_groups = {
        "entrypoint": entry_points,
        "backend_route": backend_routes,
        "backend_service": backend_services,
        "model": models,
        "frontend_page": frontend_pages,
        "frontend_component": frontend_components,
        "api_client": api_clients,
      }
      candidates = [
        file_info
        for role in related_roles
        for file_info in role_groups.get(role, [])
      ]
    else:
      # Fallback: use files from any role except docs/config
      candidates = [f for f in snapshot.files
             if not f.skipped
             and f.role not in ("documentation", "config", "unknown")
             and not _is_init_file(f)]

    # Filter out the correct answer and get unique paths
    candidates = [f for f in candidates if f.path != correct_file.path]
    seen = set()
    for f in candidates:
      if f.path not in seen and len(distractors) < count:
        distractors.append(f.path)
        seen.add(f.path)

    # If we don't have enough, pad with any non-skipped files
    if len(distractors) < count:
      fallback = [f.path for f in snapshot.files
            if not f.skipped
            and f.path != correct_file.path
            and f.path not in distractors
            and not _is_init_file(f)]
      distractors.extend(fallback[:count - len(distractors)])

    return distractors[:count]

  # Question 1: Entry point identification
  if entry_points:
    backend_entry = next(
      (f for f in entry_points if "backend" in f.path.lower() or f.name == "main.py"),
      None,
    )
    if backend_entry:
      distractors = get_distractors(backend_entry)
      options = [backend_entry.path] + distractors

      questions.append(QuizQuestion(
        question="Which file is the main backend entry point?",
        options=options,
        correct_answer=backend_entry.path,
        explanation=(
          f"{backend_entry.path} is the main entry point where the backend application "
          "is configured and started."
        ),
      ))

  # Question 2: Route identification
  if routes and backend_routes:
    route = routes[0]
    route_file = next((f for f in backend_routes if f.path == route.file_path), None)
    if route_file:
      distractors = get_distractors(route_file)
      options = [route_file.path] + distractors

      questions.append(QuizQuestion(
        question=f"Which file defines the {route.method} {route.path} endpoint?",
        options=options,
        correct_answer=route_file.path,
        explanation=(
          f"{route_file.path} contains the route handler for {route.method} {route.path}."
        ),
      ))

  # Question 3: Frontend entry point
  if entry_points:
    frontend_entry = next(
      (f for f in entry_points if "frontend" in f.path.lower() or "App.tsx" in f.path),
      None,
    )
    if frontend_entry:
      distractors = get_distractors(frontend_entry)
      options = [frontend_entry.path] + distractors

      questions.append(QuizQuestion(
        question="Which file is the main frontend entry point?",
        options=options,
        correct_answer=frontend_entry.path,
        explanation=f"{frontend_entry.path} is where the frontend application is initialized.",
      ))

  # Question 4: API client identification
  if api_clients:
    api_client = api_clients[0]
    distractors = get_distractors(api_client)
    options = [api_client.path] + distractors

    questions.append(QuizQuestion(
      question="Which file likely handles API calls to the backend?",
      options=options,
      correct_answer=api_client.path,
      explanation=f"{api_client.path} is the API client that communicates with the backend.",
    ))

  # Question 5: Model/data structure
  if models:
    model = models[0]
    distractors = get_distractors(model)
    options = [model.path] + distractors

    questions.append(QuizQuestion(
      question="Which file defines data models or schemas?",
      options=options,
      correct_answer=model.path,
      explanation=f"{model.path} contains data model definitions used throughout the application.",
    ))

  # Question 6: Framework detection
  if fingerprint.frameworks:
    framework = fingerprint.frameworks[0]

    # Create plausible wrong answers
    all_frameworks = ["React", "Vue", "Angular", "FastAPI", "Flask", "Django", "Express", "Next.js"]
    wrong_frameworks = [f for f in all_frameworks if f != framework.name][:3]
    options = [framework.name] + wrong_frameworks

    questions.append(QuizQuestion(
      question=f"Which {framework.category} framework is used in this project?",
      options=options,
      correct_answer=framework.name,
      explanation=(
        f"The project uses {framework.name}. Evidence: "
        f"{framework.evidence[0] if framework.evidence else 'detected from project files'}."
      ),
    ))

  # Question 7: Project type
  if fingerprint.project_type:
    project_types = [
      "Full-stack web application",
      "Frontend web application",
      "Backend API",
      "Python package/library",
    ]
    wrong_types = [t for t in project_types if t != fingerprint.project_type][:3]
    options = [fingerprint.project_type] + wrong_types

    questions.append(QuizQuestion(
      question="What type of project is this?",
      options=options,
      correct_answer=fingerprint.project_type,
      explanation=f"This is a {fingerprint.project_type}. {fingerprint.summary}",
    ))

  # Question 8: Where to add a new route
  if backend_routes:
    route_file = backend_routes[0]
    distractors = get_distractors(route_file)
    options = [route_file.path] + distractors

    questions.append(QuizQuestion(
      question="If you wanted to add a new API endpoint, which file would you likely edit?",
      options=options,
      correct_answer=route_file.path,
      explanation=(
        f"{route_file.path} contains route definitions, making it the logical place "
        "to add new endpoints."
      ),
    ))

  # Limit to MAX_QUIZ_QUESTIONS
  return questions[:MAX_QUIZ_QUESTIONS]
