"""Tests for component cards and quiz generation."""


from repoquest.sample_loader import load_demo_repo
from repoquest.detectors import generate_fingerprint
from repoquest.route_extractors import extract_all_routes
from repoquest.quest import generate_component_cards, generate_quiz


def test_component_cards_generated():
    """Test that component cards are generated for demo repo."""
    snapshot = load_demo_repo()
    fingerprint = generate_fingerprint(snapshot)
    routes = extract_all_routes(snapshot.files)
    
    cards = generate_component_cards(snapshot, fingerprint, routes)
    
    assert len(cards) > 0


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
    
    for card in cards:
        assert card.path
        assert card.title
        assert card.role
        assert card.why_it_matters
        assert isinstance(card.connected_to, list)
        assert isinstance(card.detected_items, list)
        assert isinstance(card.suggested_test_ideas, list)
        assert card.suggested_bob_prompt
        assert len(card.suggested_bob_prompt) > 20  # Should be meaningful


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
        # Bob prompt should mention the file path
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
        assert len(question.question) > 10  # Should be meaningful
        assert len(question.options) >= 2  # At least 2 options
        assert question.correct_answer
        assert question.correct_answer in question.options
        assert question.explanation
        assert len(question.explanation) > 10  # Should be meaningful


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
    
    assert sum(patterns) >= 3  # At least 3 different types of questions

# Made with Bob
