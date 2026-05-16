"""Generate AI-assisted code recommendations from repository analysis."""

from repoquest.assistant_models import (
    CodeRecommendation,
    AIRecommendationResult,
    ContextPack,
)
from repoquest.models import (
    RepositorySnapshot,
    ProjectFingerprint,
    RouteInfo,
    ComponentCard,
    WorkPlan,
)
from repoquest.recommendation_validator import validate_recommendations


def generate_mock_recommendations(
    snapshot: RepositorySnapshot,
    fingerprint: ProjectFingerprint,
    routes: list[RouteInfo],
    component_cards: list[ComponentCard],
    work_plan: WorkPlan,
    context_pack: ContextPack,
) -> AIRecommendationResult:
    """
    Generate mock AI recommendations for testing and demo purposes.

    This produces deterministic recommendations based on repo analysis
    without requiring an actual AI model.

    Args:
        snapshot: Repository snapshot
        fingerprint: Project fingerprint
        routes: Detected routes
        component_cards: Component cards
        work_plan: Generated work plan
        context_pack: Context pack used for generation

    Returns:
        AIRecommendationResult with mock recommendations
    """
    recommendations = []
    
    # Find relevant files
    backend_routes = [f.path for f in snapshot.files if f.role == "backend_route" and not f.skipped]
    test_files = [f.path for f in snapshot.files if f.role == "test" and not f.skipped]
    api_clients = [f.path for f in snapshot.files if f.role == "api_client" and not f.skipped]
    models = [f.path for f in snapshot.files if f.role == "model" and not f.skipped]
    
    # Recommendation 1: Add edge-case tests for routes
    if backend_routes and routes:
        route_file = backend_routes[0]
        test_file = test_files[0] if test_files else f"{route_file.replace('.py', '_test.py')}"
        
        route_list = [f"{r.method} {r.path}" for r in routes[:3]]
        
        recommendations.append(CodeRecommendation(
            title="Add edge-case tests for API route deletion",
            category="testing",
            priority="high",
            files=[route_file, test_file],
            evidence=[
                f"Route file: {route_file}",
                f"Detected routes: {', '.join(route_list)}",
                "DELETE endpoint found with explicit 404 handling",
            ],
            rationale="The DELETE route has explicit error handling for missing resources (404 response). This edge case should be tested to ensure the API behaves correctly when clients attempt to delete nonexistent items.",
            proposed_change_summary="Add a pytest test case that attempts to delete a nonexistent resource and verifies a 404 response is returned with an appropriate error message.",
            test_plan=[
                "Add test function test_delete_nonexistent_trip()",
                "Mock or use test database without the target resource",
                "Call DELETE endpoint with nonexistent ID",
                "Assert response status is 404",
                "Assert error message is clear and helpful",
                "Run pytest -v to verify test passes",
            ],
            workflow="Inspect route implementation -> Review existing tests -> Add new test case -> Verify test passes",
            confidence=0.85,
        ))
    
    # Recommendation 2: Improve API client error handling
    if api_clients:
        api_client = api_clients[0]
        
        recommendations.append(CodeRecommendation(
            title="Add timeout and retry logic to API client",
            category="error_handling",
            priority="high",
            files=[api_client],
            evidence=[
                f"API client: {api_client}",
                "No timeout configuration detected",
                "No retry logic for transient failures",
            ],
            rationale="The API client currently lacks timeout handling and retry logic. This can lead to poor user experience when network conditions are unstable or the backend is temporarily unavailable. Adding these features improves reliability.",
            proposed_change_summary="Add a 10-second timeout to all API calls and implement exponential backoff retry logic (max 3 retries) for transient failures like network errors or 5xx responses.",
            test_plan=[
                "Add timeout parameter to fetch/axios calls",
                "Implement retry wrapper with exponential backoff",
                "Test with simulated slow network",
                "Test with simulated network failure",
                "Verify user sees helpful error messages",
            ],
            workflow="Review current API client -> Add timeout config -> Implement retry logic -> Add error messages -> Test edge cases",
            confidence=0.90,
        ))
    
    # Recommendation 3: Add input validation to data models
    if models:
        model_file = models[0]
        
        recommendations.append(CodeRecommendation(
            title="Add Pydantic validation to data models",
            category="data_model",
            priority="medium",
            files=[model_file],
            evidence=[
                f"Model file: {model_file}",
                "Data models define structure but lack validation",
                "No constraints on required fields or data types",
            ],
            rationale="Data models currently lack validation constraints. Adding Pydantic validators ensures data integrity at the model level, catching invalid data before it enters the system and providing clear error messages.",
            proposed_change_summary="Convert data models to Pydantic BaseModel classes with field validators for required fields, data types, string lengths, and business logic constraints.",
            test_plan=[
                "Add Pydantic BaseModel inheritance",
                "Add Field validators for constraints",
                "Add custom validators for business logic",
                "Write unit tests for valid and invalid data",
                "Verify validation errors are clear",
            ],
            workflow="Review model structure -> Add Pydantic validators -> Add constraint checks -> Write validation tests -> Verify error messages",
            confidence=0.80,
        ))
    
    # Recommendation 4: Document API endpoints
    if backend_routes and routes:
        readme_files = [f.path for f in snapshot.files if f.name.lower() == "readme.md" and not f.skipped]
        readme_file = readme_files[0] if readme_files else "README.md"
        
        recommendations.append(CodeRecommendation(
            title="Generate comprehensive API documentation",
            category="documentation",
            priority="medium",
            files=[readme_file] + backend_routes[:2],
            evidence=[
                f"Detected {len(routes)} API routes",
                f"Route files: {', '.join(backend_routes[:2])}",
                "README exists but lacks API documentation section",
            ],
            rationale="The API currently lacks comprehensive documentation. Adding detailed endpoint documentation helps developers understand available endpoints, request/response formats, and usage examples, reducing integration time.",
            proposed_change_summary="Add an 'API Documentation' section to README.md with all endpoints, HTTP methods, request parameters, response schemas, and example curl commands.",
            test_plan=[
                "Document each endpoint with method and path",
                "Add request parameter descriptions",
                "Add response schema examples",
                "Add curl example for each endpoint",
                "Review for accuracy and completeness",
            ],
            workflow="Extract route details -> Document request/response schemas -> Add examples -> Update README -> Review",
            confidence=0.75,
        ))
    
    # Recommendation 5: Add integration tests
    if backend_routes and test_files:
        recommendations.append(CodeRecommendation(
            title="Add end-to-end integration tests",
            category="testing",
            priority="medium",
            files=test_files[:2] + backend_routes[:2],
            evidence=[
                f"Found {len(test_files)} test files",
                "Unit tests exist but no integration tests detected",
                "Multiple routes that interact with each other",
            ],
            rationale="While unit tests exist, integration tests are needed to verify that components work together correctly. This catches issues that only appear when the full system is running.",
            proposed_change_summary="Add integration test suite that starts the application, makes real HTTP requests to endpoints, and verifies end-to-end behavior including database interactions.",
            test_plan=[
                "Set up test database/fixtures",
                "Create integration test file",
                "Add tests for common user workflows",
                "Test error scenarios across components",
                "Verify cleanup after tests",
            ],
            workflow="Design test scenarios -> Set up test environment -> Write integration tests -> Run and verify -> Add to CI",
            confidence=0.70,
        ))
    
    # Validate all recommendations
    validated = validate_recommendations(recommendations, snapshot)
    
    return AIRecommendationResult(
        recommendations=validated,
        provider="mock",
        model="deterministic-v1",
        context_pack=context_pack,
        warnings=[],
    )


def create_recommendation_prompt(
    context_pack: ContextPack,
    work_plan: WorkPlan,
) -> str:
    """
    Create a prompt for AI recommendation generation.

    Args:
        context_pack: Bounded context pack
        work_plan: Generated work plan

    Returns:
        Prompt string for AI model
    """
    lines = [
        "# Code Recommendation Task",
        "",
        "You are an expert software engineer reviewing a codebase.",
        "",
        "## Repository Context",
        "",
        f"**Project Summary**: {context_pack.project_summary}",
        "",
        f"**Frameworks**: {', '.join(context_pack.frameworks)}",
        "",
        f"**Entry Points**: {', '.join(context_pack.entry_points[:5])}",
        "",
        "## Detected Components",
        "",
        context_pack.component_summary,
        "",
        "## Detected Routes",
        "",
        context_pack.routes_summary,
        "",
        "## Test Coverage",
        "",
        context_pack.test_summary,
        "",
        "## Deterministic Work Plan",
        "",
        context_pack.workflow_summary,
        "",
        "## Your Task",
        "",
        "Generate 3-5 high-value code recommendations that:",
        "",
        "1. Are grounded in the evidence above",
        "2. Reference specific files from the repository",
        "3. Provide clear rationale and proposed changes",
        "4. Include actionable test plans",
        "5. Suggest practical workflows",
        "",
        "## Output Format",
        "",
        "Return a JSON array of recommendations with this schema:",
        "",
        "```json",
        "[",
        "  {",
        '    "title": "Clear, specific title",',
        '    "category": "testing|documentation|api|frontend|backend|data_model|error_handling|refactor|developer_experience",',
        '    "priority": "high|medium|low",',
        '    "files": ["file1.py", "file2.ts"],',
        '    "evidence": ["Evidence item 1", "Evidence item 2"],',
        '    "rationale": "Why this matters",',
        '    "proposed_change_summary": "What to change",',
        '    "test_plan": ["Step 1", "Step 2"],',
        '    "workflow": "Brief workflow description",',
        '    "confidence": 0.85',
        "  }",
        "]",
        "```",
        "",
        "## Important Constraints",
        "",
        "- Only reference files that exist in the evidence",
        "- Do not generate code patches",
        "- Do not claim tests pass without verification",
        "- Mark confidence honestly (0.0 to 1.0)",
        "- Focus on high-impact improvements",
        "",
    ]
    
    return "\n".join(lines)


def parse_ai_recommendations(
    response_text: str,
    snapshot: RepositorySnapshot,
) -> list[CodeRecommendation]:
    """
    Parse AI response into CodeRecommendation objects.

    Args:
        response_text: Raw AI response text
        snapshot: Repository snapshot for validation

    Returns:
        List of parsed and validated recommendations
    """
    import json
    import re
    
    recommendations = []
    
    # Try to extract JSON from response
    # Look for JSON array in code blocks or raw text
    json_match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', response_text, re.DOTALL)
    if json_match:
        json_text = json_match.group(1)
    else:
        # Try to find raw JSON array
        json_match = re.search(r'\[.*?\]', response_text, re.DOTALL)
        if json_match:
            json_text = json_match.group(0)
        else:
            return []
    
    try:
        data = json.loads(json_text)
        if not isinstance(data, list):
            return []
        
        for item in data:
            if not isinstance(item, dict):
                continue
            
            try:
                rec = CodeRecommendation.from_dict(item)
                recommendations.append(rec)
            except (KeyError, ValueError, TypeError):
                continue
    
    except json.JSONDecodeError:
        return []
    
    # Validate all recommendations
    return validate_recommendations(recommendations, snapshot)


def generate_recommendation_summary(result: AIRecommendationResult) -> str:
    """
    Generate a text summary of recommendations.

    Args:
        result: AI recommendation result

    Returns:
        Markdown summary string
    """
    lines = [
        "# AI Code Recommendations",
        "",
        f"**Provider**: {result.provider}",
        f"**Model**: {result.model}",
        f"**Generated**: {result.timestamp}",
        "",
        f"**Total Recommendations**: {len(result.recommendations)}",
        f"**Valid**: {len(result.valid_recommendations)}",
        f"**Trusted**: {len(result.trusted_recommendations)}",
        "",
    ]
    
    if result.warnings:
        lines.extend([
            "## Warnings",
            "",
        ])
        for warning in result.warnings:
            lines.append(f"- {warning}")
        lines.append("")
    
    # Group by priority
    high_priority = [r for r in result.trusted_recommendations if r.priority == "high"]
    medium_priority = [r for r in result.trusted_recommendations if r.priority == "medium"]
    low_priority = [r for r in result.trusted_recommendations if r.priority == "low"]
    
    if high_priority:
        lines.extend([
            "## High Priority",
            "",
        ])
        for rec in high_priority:
            lines.append(f"- **{rec.title}** ({rec.category})")
        lines.append("")
    
    if medium_priority:
        lines.extend([
            "## Medium Priority",
            "",
        ])
        for rec in medium_priority:
            lines.append(f"- **{rec.title}** ({rec.category})")
        lines.append("")
    
    if low_priority:
        lines.extend([
            "## Low Priority",
            "",
        ])
        for rec in low_priority:
            lines.append(f"- **{rec.title}** ({rec.category})")
        lines.append("")
    
    return "\n".join(lines)
