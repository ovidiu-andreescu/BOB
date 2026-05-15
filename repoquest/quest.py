"""Generate component cards and quiz questions for repository onboarding."""

from repoquest.models import (
    RepositorySnapshot,
    ProjectFingerprint,
    FileInfo,
    RouteInfo,
    ComponentCard,
    QuizQuestion,
)
from repoquest.config import MAX_COMPONENT_CARDS, MAX_QUIZ_QUESTIONS


def _find_connected_files(file_info: FileInfo, snapshot: RepositorySnapshot) -> list[str]:
    """Find files that are likely connected to this file.
    
    Uses simple heuristics based on imports, path structure, and naming.
    """
    connected = []
    file_path_lower = file_info.path.lower()
    file_name_base = file_info.name.replace(file_info.suffix, "").lower()
    
    # For backend routes, look for related services and models
    if file_info.role == "backend_route":
        for other in snapshot.files:
            if other.skipped or other.path == file_info.path:
                continue
            
            # Look for services with similar names
            if other.role == "backend_service" and file_name_base in other.path.lower():
                connected.append(other.path)
            
            # Look for models with similar names
            if other.role == "model" and file_name_base in other.path.lower():
                connected.append(other.path)
    
    # For services, look for related models
    if file_info.role == "backend_service":
        for other in snapshot.files:
            if other.skipped or other.path == file_info.path:
                continue
            
            if other.role == "model" and file_name_base in other.path.lower():
                connected.append(other.path)
    
    # For frontend pages, look for components and API clients
    if file_info.role == "frontend_page":
        for other in snapshot.files:
            if other.skipped or other.path == file_info.path:
                continue
            
            # Look for components
            if other.role == "frontend_component":
                connected.append(other.path)
            
            # Look for API clients
            if other.role == "api_client":
                connected.append(other.path)
    
    # For API clients, look for backend routes
    if file_info.role == "api_client":
        for other in snapshot.files:
            if other.skipped or other.path == file_info.path:
                continue
            
            if other.role == "backend_route":
                connected.append(other.path)
    
    # Check for explicit imports in the text preview
    if file_info.text_preview:
        for other in snapshot.files:
            if other.skipped or other.path == file_info.path:
                continue
            
            # Simple check: if the other file's name appears in this file's content
            other_name_base = other.name.replace(other.suffix, "")
            if other_name_base in file_info.text_preview:
                if other.path not in connected:
                    connected.append(other.path)
    
    return connected[:5]  # Limit to top 5 connections


def _generate_detected_items(file_info: FileInfo, routes: list[RouteInfo]) -> list[str]:
    """Generate a list of detected items for this file (routes, functions, etc.)."""
    items = []
    
    # For backend routes, list the detected routes
    if file_info.role == "backend_route":
        file_routes = [r for r in routes if r.file_path == file_info.path]
        for route in file_routes[:5]:  # Limit to 5
            items.append(f"{route.method} {route.path}")
    
    # For other files, we could detect functions, classes, etc.
    # For now, keep it simple and just note the role
    if not items and file_info.role != "unknown":
        items.append(f"Classified as {file_info.role}")
    
    return items


def _generate_test_ideas(file_info: FileInfo, routes: list[RouteInfo]) -> list[str]:
    """Generate suggested test ideas for this file."""
    ideas = []
    
    if file_info.role == "backend_route":
        file_routes = [r for r in routes if r.file_path == file_info.path]
        if file_routes:
            ideas.append("Test valid requests with expected data")
            ideas.append("Test requests with missing required fields")
            ideas.append("Test requests with invalid data types")
            if any("delete" in r.method.lower() for r in file_routes):
                ideas.append("Test deleting non-existent resources")
    
    elif file_info.role == "backend_service":
        ideas.append("Test the main business logic with valid inputs")
        ideas.append("Test edge cases and boundary conditions")
        ideas.append("Test error handling for invalid inputs")
    
    elif file_info.role == "model":
        ideas.append("Test data validation rules")
        ideas.append("Test serialization and deserialization")
        ideas.append("Test default values and optional fields")
    
    elif file_info.role == "frontend_component":
        ideas.append("Test component renders correctly with props")
        ideas.append("Test user interactions and event handlers")
        ideas.append("Test edge cases like empty or null data")
    
    elif file_info.role == "api_client":
        ideas.append("Test successful API calls")
        ideas.append("Test error handling for failed requests")
        ideas.append("Test request timeout scenarios")
    
    return ideas[:3]  # Limit to 3 ideas


def _generate_bob_prompt(file_info: FileInfo, routes: list[RouteInfo]) -> str:
    """Generate a suggested IBM Bob prompt for this file."""
    path = file_info.path
    role = file_info.role
    
    if role == "backend_route":
        file_routes = [r for r in routes if r.file_path == path]
        if file_routes:
            route_list = ", ".join(f"{r.method} {r.path}" for r in file_routes[:3])
            return f"Explain {path}, identify edge cases for routes ({route_list}), and generate pytest tests for the detected endpoints."
        return f"Explain {path}, identify potential edge cases, and suggest improvements for the route handlers."
    
    elif role == "backend_service":
        return f"Review {path} for business logic correctness, identify edge cases, and suggest error handling improvements."
    
    elif role == "model":
        return f"Review {path} data model, suggest validation rules, and identify potential data integrity issues."
    
    elif role == "frontend_component":
        return f"Review {path} component, suggest accessibility improvements, and identify potential UI edge cases."
    
    elif role == "frontend_page":
        return f"Review {path} page, suggest UX improvements, and identify potential user flow issues."
    
    elif role == "api_client":
        return f"Review {path} API client, suggest error handling improvements, and identify retry/timeout strategies."
    
    elif role == "entrypoint":
        return f"Explain {path} application setup, identify configuration issues, and suggest security improvements."
    
    else:
        return f"Explain {path} and suggest improvements for code quality and maintainability."


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
    
    # Priority roles for component cards
    priority_roles = [
        "entrypoint",
        "backend_route",
        "backend_service",
        "model",
        "frontend_page",
        "api_client",
        "frontend_component",
    ]
    
    # Collect candidates by role
    candidates_by_role = {role: [] for role in priority_roles}
    
    for file_info in snapshot.files:
        if file_info.skipped:
            continue
        
        if file_info.role in priority_roles:
            candidates_by_role[file_info.role].append(file_info)
    
    # Generate cards, prioritizing by role
    for role in priority_roles:
        for file_info in candidates_by_role[role]:
            if len(cards) >= MAX_COMPONENT_CARDS:
                break
            
            # Generate card title
            title = file_info.name
            
            # Generate "why it matters" text
            if role == "entrypoint":
                why_it_matters = "This is where the application starts. Understanding this file shows how the app is configured and initialized."
            elif role == "backend_route":
                why_it_matters = "This file defines API endpoints. Frontend requests enter the backend here."
            elif role == "backend_service":
                why_it_matters = "This file contains business logic. It processes data and implements core functionality."
            elif role == "model":
                why_it_matters = "This file defines data structures. Understanding these models is key to understanding the data flow."
            elif role == "frontend_page":
                why_it_matters = "This is a main UI page. It shows how users interact with the application."
            elif role == "api_client":
                why_it_matters = "This file handles frontend-backend communication. It's the bridge between UI and API."
            elif role == "frontend_component":
                why_it_matters = "This is a reusable UI component. Understanding it helps you see how the interface is built."
            else:
                why_it_matters = "This file plays an important role in the codebase."
            
            # Find connections
            connected_to = _find_connected_files(file_info, snapshot)
            
            # Generate detected items
            detected_items = _generate_detected_items(file_info, routes)
            
            # Generate test ideas
            test_ideas = _generate_test_ideas(file_info, routes)
            
            # Generate Bob prompt
            bob_prompt = _generate_bob_prompt(file_info, routes)
            
            cards.append(ComponentCard(
                path=file_info.path,
                title=title,
                role=f"Likely role: {role.replace('_', ' ')}",
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
    
    # Find key files for questions
    entry_points = [f for f in snapshot.files if f.role == "entrypoint" and not f.skipped]
    backend_routes = [f for f in snapshot.files if f.role == "backend_route" and not f.skipped]
    frontend_pages = [f for f in snapshot.files if f.role == "frontend_page" and not f.skipped]
    api_clients = [f for f in snapshot.files if f.role == "api_client" and not f.skipped]
    models = [f for f in snapshot.files if f.role == "model" and not f.skipped]
    
    # Question 1: Entry point identification
    if entry_points:
        backend_entry = next((f for f in entry_points if "backend" in f.path.lower() or f.name == "main.py"), None)
        if backend_entry:
            # Create distractors
            other_files = [f for f in snapshot.files if not f.skipped and f.path != backend_entry.path][:3]
            options = [backend_entry.path] + [f.path for f in other_files]
            
            questions.append(QuizQuestion(
                question="Which file is the main backend entry point?",
                options=options,
                correct_answer=backend_entry.path,
                explanation=f"{backend_entry.path} is the main entry point where the backend application is configured and started.",
            ))
    
    # Question 2: Route identification
    if routes and backend_routes:
        route = routes[0]
        route_file = next((f for f in backend_routes if f.path == route.file_path), None)
        if route_file:
            other_files = [f for f in snapshot.files if not f.skipped and f.path != route_file.path][:3]
            options = [route_file.path] + [f.path for f in other_files]
            
            questions.append(QuizQuestion(
                question=f"Which file defines the {route.method} {route.path} endpoint?",
                options=options,
                correct_answer=route_file.path,
                explanation=f"{route_file.path} contains the route handler for {route.method} {route.path}.",
            ))
    
    # Question 3: Frontend entry point
    if entry_points:
        frontend_entry = next((f for f in entry_points if "frontend" in f.path.lower() or "App.tsx" in f.path), None)
        if frontend_entry:
            other_files = [f for f in snapshot.files if not f.skipped and f.path != frontend_entry.path][:3]
            options = [frontend_entry.path] + [f.path for f in other_files]
            
            questions.append(QuizQuestion(
                question="Which file is the main frontend entry point?",
                options=options,
                correct_answer=frontend_entry.path,
                explanation=f"{frontend_entry.path} is where the frontend application is initialized.",
            ))
    
    # Question 4: API client identification
    if api_clients:
        api_client = api_clients[0]
        other_files = [f for f in snapshot.files if not f.skipped and f.path != api_client.path][:3]
        options = [api_client.path] + [f.path for f in other_files]
        
        questions.append(QuizQuestion(
            question="Which file likely handles API calls to the backend?",
            options=options,
            correct_answer=api_client.path,
            explanation=f"{api_client.path} is the API client that communicates with the backend.",
        ))
    
    # Question 5: Model/data structure
    if models:
        model = models[0]
        other_files = [f for f in snapshot.files if not f.skipped and f.path != model.path][:3]
        options = [model.path] + [f.path for f in other_files]
        
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
            explanation=f"The project uses {framework.name}. Evidence: {framework.evidence[0] if framework.evidence else 'detected from project files'}.",
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
        other_files = [f for f in snapshot.files if not f.skipped and f.path != route_file.path][:3]
        options = [route_file.path] + [f.path for f in other_files]
        
        questions.append(QuizQuestion(
            question="If you wanted to add a new API endpoint, which file would you likely edit?",
            options=options,
            correct_answer=route_file.path,
            explanation=f"{route_file.path} contains route definitions, making it the logical place to add new endpoints.",
        ))
    
    # Limit to MAX_QUIZ_QUESTIONS
    return questions[:MAX_QUIZ_QUESTIONS]

# Made with Bob
