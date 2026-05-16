"""Generate component documentation pages from RepoQuest analysis."""

from repoquest.models import (
    RepositorySnapshot,
    ProjectFingerprint,
    RouteInfo,
    ComponentCard,
)
from repoquest.assistant_models import GeneratedDocPage


def validate_doc_page(
    doc_page: GeneratedDocPage,
    snapshot: RepositorySnapshot,
) -> tuple[bool, list[str]]:
    """Validate a generated doc page against the repository snapshot.
    
    Returns:
        (is_valid, validation_errors)
    """
    errors = []
    
    # Check basic validity
    if not doc_page.is_valid:
        errors.append("Doc page is missing required fields (title, content, or source_files)")
        return False, errors
    
    # Validate source files exist in snapshot
    snapshot_paths = {f.path for f in snapshot.files}
    for source_file in doc_page.source_files:
        if source_file not in snapshot_paths:
            errors.append(f"Source file not found in snapshot: {source_file}")
    
    # Validate evidence files exist
    for evidence_file in doc_page.evidence:
        if evidence_file not in snapshot_paths:
            errors.append(f"Evidence file not found in snapshot: {evidence_file}")
    
    # Check for unsafe execution claims
    unsafe_phrases = [
        "ran the tests",
        "executed the code",
        "running the application",
        "installed dependencies",
        "npm install",
        "pip install",
        "executed script",
    ]
    content_lower = doc_page.content.lower()
    for phrase in unsafe_phrases:
        if phrase in content_lower:
            errors.append(f"Doc contains unsafe execution claim: '{phrase}'")
    
    # Warn if no evidence provided
    if not doc_page.evidence and not doc_page.source_files:
        errors.append("Doc page has no evidence or source files")
    
    return len(errors) == 0, errors


def generate_api_routes_doc(
    routes: list[RouteInfo],
    snapshot: RepositorySnapshot,
) -> GeneratedDocPage:
    """Generate deterministic API routes reference documentation."""
    if not routes:
        return GeneratedDocPage(
            title="API Routes Reference",
            category="api",
            source_files=[],
            content="No API routes detected in this repository.",
            evidence=[],
            warnings=["No routes found"],
        )
    
    # Group routes by file
    routes_by_file: dict[str, list[RouteInfo]] = {}
    for route in routes:
        if route.file_path not in routes_by_file:
            routes_by_file[route.file_path] = []
        routes_by_file[route.file_path].append(route)
    
    # Build content
    lines = []
    lines.append("# API Routes Reference")
    lines.append("")
    lines.append("This document lists all detected API routes in the repository.")
    lines.append("")
    lines.append("**Note:** This is based on static analysis without executing the code.")
    lines.append("")
    
    for file_path, file_routes in sorted(routes_by_file.items()):
        lines.append(f"## {file_path}")
        lines.append("")
        
        # Group by framework
        framework = file_routes[0].framework if file_routes else "unknown"
        lines.append(f"**Framework:** {framework}")
        lines.append("")
        
        # List routes
        for route in sorted(file_routes, key=lambda r: (r.method, r.path)):
            lines.append(f"### {route.method} {route.path}")
            if route.function_name:
                lines.append(f"**Handler:** `{route.function_name}`")
            lines.append("")
    
    source_files = list(routes_by_file.keys())
    
    return GeneratedDocPage(
        title="API Routes Reference",
        category="api",
        source_files=source_files,
        content="\n".join(lines),
        evidence=source_files,
        related_components=[],
    )


def generate_component_docs(
    component_cards: list[ComponentCard],
    snapshot: RepositorySnapshot,
) -> list[GeneratedDocPage]:
    """Generate deterministic component documentation pages."""
    doc_pages = []
    
    # Group components by role
    components_by_role: dict[str, list[ComponentCard]] = {}
    for card in component_cards:
        if card.role not in components_by_role:
            components_by_role[card.role] = []
        components_by_role[card.role].append(card)
    
    # Generate a doc page for each role category
    for role, cards in sorted(components_by_role.items()):
        lines = []
        role_title = role.replace("_", " ").title()
        lines.append(f"# {role_title} Components")
        lines.append("")
        lines.append(f"This document describes the {role_title.lower()} components in the repository.")
        lines.append("")
        lines.append("**Note:** This is based on static analysis without executing the code.")
        lines.append("")
        
        for card in sorted(cards, key=lambda c: c.path):
            lines.append(f"## {card.title}")
            lines.append("")
            lines.append(f"**File:** `{card.path}`")
            lines.append("")
            lines.append(f"**Purpose:** {card.why_it_matters}")
            lines.append("")
            
            if card.detected_items:
                lines.append("**Detected Items:**")
                for item in card.detected_items[:10]:
                    lines.append(f"- {item}")
                lines.append("")
            
            if card.connected_to:
                lines.append("**Connected To:**")
                for conn in card.connected_to[:5]:
                    lines.append(f"- `{conn}`")
                lines.append("")
            
            if card.suggested_test_ideas:
                lines.append("**Test Ideas:**")
                for idea in card.suggested_test_ideas[:5]:
                    lines.append(f"- {idea}")
                lines.append("")
        
        source_files = [card.path for card in cards]
        related = []
        for card in cards:
            related.extend(card.connected_to[:3])
        related = list(set(related))[:10]
        
        doc_pages.append(GeneratedDocPage(
            title=f"{role_title} Components",
            category=role,
            source_files=source_files,
            content="\n".join(lines),
            evidence=source_files,
            related_components=related,
        ))
    
    return doc_pages


def generate_models_doc(
    snapshot: RepositorySnapshot,
) -> GeneratedDocPage:
    """Generate deterministic models/schemas reference documentation."""
    model_files = [f for f in snapshot.files if f.role == "model"]
    
    if not model_files:
        return GeneratedDocPage(
            title="Models & Schemas Reference",
            category="models",
            source_files=[],
            content="No model or schema files detected in this repository.",
            evidence=[],
            warnings=["No model files found"],
        )
    
    lines = []
    lines.append("# Models & Schemas Reference")
    lines.append("")
    lines.append("This document lists all detected data models and schemas in the repository.")
    lines.append("")
    lines.append("**Note:** This is based on static analysis without executing the code.")
    lines.append("")
    
    for file_info in sorted(model_files, key=lambda f: f.path):
        lines.append(f"## {file_info.name}")
        lines.append("")
        lines.append(f"**File:** `{file_info.path}`")
        lines.append(f"**Language:** {file_info.language}")
        lines.append(f"**Lines:** {file_info.line_count}")
        lines.append("")
        
        # Add a small preview if available
        if file_info.text_preview:
            preview = file_info.text_preview[:300]
            lines.append("**Preview:**")
            lines.append("```")
            lines.append(preview)
            if len(file_info.text_preview) > 300:
                lines.append("... (truncated)")
            lines.append("```")
            lines.append("")
    
    source_files = [f.path for f in model_files]
    
    return GeneratedDocPage(
        title="Models & Schemas Reference",
        category="models",
        source_files=source_files,
        content="\n".join(lines),
        evidence=source_files,
        related_components=[],
    )


def generate_test_reference_doc(
    snapshot: RepositorySnapshot,
) -> GeneratedDocPage:
    """Generate deterministic test reference documentation."""
    test_files = [f for f in snapshot.files if f.role == "test"]
    
    if not test_files:
        return GeneratedDocPage(
            title="Test Reference",
            category="tests",
            source_files=[],
            content="No test files detected in this repository.",
            evidence=[],
            warnings=["No test files found"],
        )
    
    lines = []
    lines.append("# Test Reference")
    lines.append("")
    lines.append("This document lists all detected test files in the repository.")
    lines.append("")
    lines.append("**Note:** This is based on static analysis. No tests were executed.")
    lines.append("")
    
    for file_info in sorted(test_files, key=lambda f: f.path):
        lines.append(f"## {file_info.name}")
        lines.append("")
        lines.append(f"**File:** `{file_info.path}`")
        lines.append(f"**Language:** {file_info.language}")
        lines.append(f"**Lines:** {file_info.line_count}")
        lines.append("")
    
    source_files = [f.path for f in test_files]
    
    return GeneratedDocPage(
        title="Test Reference",
        category="tests",
        source_files=source_files,
        content="\n".join(lines),
        evidence=source_files,
        related_components=[],
    )


def generate_all_deterministic_docs(
    snapshot: RepositorySnapshot,
    fingerprint: ProjectFingerprint,
    routes: list[RouteInfo] | None = None,
    component_cards: list[ComponentCard] | None = None,
) -> list[GeneratedDocPage]:
    """Generate all deterministic documentation pages.
    
    This function generates reference documentation without AI assistance.
    All content is derived directly from static analysis.
    """
    doc_pages = []
    
    # API routes reference
    if routes:
        doc_pages.append(generate_api_routes_doc(routes, snapshot))
    
    # Component documentation by role
    if component_cards:
        doc_pages.extend(generate_component_docs(component_cards, snapshot))
    
    # Models/schemas reference
    doc_pages.append(generate_models_doc(snapshot))
    
    # Test reference
    doc_pages.append(generate_test_reference_doc(snapshot))
    
    return doc_pages

# Made with Bob
