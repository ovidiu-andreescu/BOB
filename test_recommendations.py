#!/usr/bin/env python3
"""Test script for AI recommendations feature."""

from repoquest.sample_loader import load_demo_repo
from repoquest.detectors import generate_fingerprint
from repoquest.route_extractors import extract_all_routes
from repoquest.import_graph import build_import_graph
from repoquest.reading_path import generate_reading_path
from repoquest.quest import generate_component_cards
from repoquest.test_intelligence import generate_test_intelligence
from repoquest.workflows import generate_work_plan
from repoquest.assistant_context import build_context_pack
from repoquest.assistant_provider import MockAssistantProvider

# Load demo repo
print("Loading demo repo...")
snapshot = load_demo_repo()

print("Generating fingerprint...")
fingerprint = generate_fingerprint(snapshot)

print("Extracting routes...")
routes = extract_all_routes(snapshot.files)

print("Building import graph...")
import_edges = build_import_graph(snapshot.files, ".")

print("Generating reading path...")
reading_path = generate_reading_path(snapshot, fingerprint)

print("Generating component cards...")
component_cards = generate_component_cards(snapshot, fingerprint, routes)

print("Generating work plan...")
work_plan = generate_work_plan(snapshot, fingerprint, routes, import_edges, reading_path, component_cards)

print("Generating test intelligence...")
test_intelligence = generate_test_intelligence(snapshot, routes, import_edges, component_cards)

print("Building context pack...")
context_pack = build_context_pack(snapshot, fingerprint, routes, component_cards, test_intelligence, work_plan)

print("\nGenerating AI recommendations with mock provider...")
provider = MockAssistantProvider()
result = provider.generate_recommendations(
    snapshot, fingerprint, routes, component_cards, work_plan, context_pack
)

print("\n✓ Recommendations generated successfully!")
print(f"  Provider: {result.provider}")
print(f"  Model: {result.model}")
print(f"  Total recommendations: {len(result.recommendations)}")
print(f"  Trusted recommendations: {len(result.trusted_recommendations)}")
print(f"  Valid recommendations: {len(result.valid_recommendations)}")

# Check first recommendation
if result.trusted_recommendations:
    rec = result.trusted_recommendations[0]
    print("\n✓ First recommendation:")
    print(f"  Title: {rec.title}")
    print(f"  Category: {rec.category}")
    print(f"  Priority: {rec.priority}")
    print(f"  Files: {len(rec.files)}")
    print(f"  Evidence: {len(rec.evidence)}")
    print(f"  Validation: {rec.validation_status}")
    print(f"  Confidence: {rec.confidence:.0%}")
    
    # Verify files exist
    valid_files = {f.path for f in snapshot.files}
    for file_path in rec.files:
        if file_path not in valid_files:
            print(f"  ✗ ERROR: File {file_path} not in snapshot!")
        else:
            print(f"  ✓ File {file_path} validated")

print("\n✓ All tests passed!")
