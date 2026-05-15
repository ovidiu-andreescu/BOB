"""Tests for framework detection and project fingerprinting."""

import pytest
from pathlib import Path

from repoquest.models import RepositorySnapshot, FileInfo, FrameworkFinding
from repoquest.detectors import (
    detect_framework,
    detect_entry_points,
    detect_key_folders,
    generate_fingerprint,
)
from repoquest.framework_rules import (
    REACT_VITE_RULE,
    FASTAPI_RULE,
    STREAMLIT_RULE,
)
from repoquest.sample_loader import load_demo_repo


def test_detect_react_vite_with_demo_repo():
    """Test that React + Vite is detected in the demo repo."""
    snapshot = load_demo_repo()
    finding = detect_framework(REACT_VITE_RULE, snapshot)
    
    assert finding is not None
    assert finding.name == "React + Vite"
    assert finding.category == "frontend"
    assert finding.confidence >= 0.5
    assert len(finding.evidence) > 0
    assert any("vite.config.ts" in e for e in finding.evidence)


def test_detect_fastapi_with_demo_repo():
    """Test that FastAPI is detected in the demo repo."""
    snapshot = load_demo_repo()
    finding = detect_framework(FASTAPI_RULE, snapshot)
    
    assert finding is not None
    assert finding.name == "FastAPI"
    assert finding.category == "backend"
    assert finding.confidence >= 0.3
    assert len(finding.evidence) > 0


def test_demo_repo_classified_as_fullstack():
    """Test that the demo repo is classified as a full-stack web application."""
    snapshot = load_demo_repo()
    fingerprint = generate_fingerprint(snapshot)
    
    assert fingerprint.project_type == "Full-stack web application"
    assert fingerprint.confidence >= 0.7
    
    # Check that both React and FastAPI are detected
    framework_names = [f.name for f in fingerprint.frameworks]
    assert "React + Vite" in framework_names
    assert "FastAPI" in framework_names


def test_demo_repo_entry_points():
    """Test that entry points are detected in the demo repo."""
    snapshot = load_demo_repo()
    fingerprint = generate_fingerprint(snapshot)
    
    # Should have at least one frontend and one backend entry point
    entry_point_str = " ".join(fingerprint.entry_points)
    
    assert len(fingerprint.entry_points) >= 2
    assert any("backend" in ep.lower() or "main.py" in ep.lower() for ep in fingerprint.entry_points)
    assert any("frontend" in ep.lower() or "App.tsx" in ep.lower() for ep in fingerprint.entry_points)


def test_streamlit_detection():
    """Test Streamlit detection with a minimal fixture."""
    files = [
        FileInfo(
            path="streamlit_app.py",
            name="streamlit_app.py",
            suffix=".py",
            size_bytes=500,
            language="Python",
            role="entrypoint",
            text_preview="import streamlit as st\n\nst.title('My App')\nst.sidebar.button('Click')",
            line_count=4,
            skipped=False,
        ),
    ]
    
    snapshot = RepositorySnapshot(
        source_name="streamlit_test",
        files=files,
        total_files_seen=1,
        total_files_scanned=1,
        warnings=[],
    )
    
    finding = detect_framework(STREAMLIT_RULE, snapshot)
    
    assert finding is not None
    assert finding.name == "Streamlit"
    assert finding.confidence >= 0.5
    assert any("streamlit" in e.lower() for e in finding.evidence)


def test_unknown_repo_fallback():
    """Test that unknown repos fall back gracefully without overclaiming."""
    files = [
        FileInfo(
            path="random.txt",
            name="random.txt",
            suffix=".txt",
            size_bytes=100,
            language="Text",
            role="unknown",
            text_preview="Just some random text",
            line_count=1,
            skipped=False,
        ),
    ]
    
    snapshot = RepositorySnapshot(
        source_name="unknown_test",
        files=files,
        total_files_seen=1,
        total_files_scanned=1,
        warnings=[],
    )
    
    fingerprint = generate_fingerprint(snapshot)
    
    assert fingerprint.project_type == "Unknown/mixed repo"
    assert fingerprint.confidence < 0.5
    assert len(fingerprint.warnings) > 0
    assert any("could not confidently" in w.lower() for w in fingerprint.warnings)


def test_detect_entry_points():
    """Test entry point detection."""
    files = [
        FileInfo(
            path="backend/main.py",
            name="main.py",
            suffix=".py",
            size_bytes=500,
            language="Python",
            role="entrypoint",
            text_preview="from fastapi import FastAPI",
            line_count=10,
            skipped=False,
        ),
        FileInfo(
            path="frontend/src/App.tsx",
            name="App.tsx",
            suffix=".tsx",
            size_bytes=800,
            language="TypeScript",
            role="entrypoint",
            text_preview="import React from 'react'",
            line_count=20,
            skipped=False,
        ),
    ]
    
    snapshot = RepositorySnapshot(
        source_name="test",
        files=files,
        total_files_seen=2,
        total_files_scanned=2,
        warnings=[],
    )
    
    entry_points = detect_entry_points(snapshot)
    
    assert len(entry_points) >= 2
    assert any("backend/main.py" in ep for ep in entry_points)
    assert any("frontend/src/App.tsx" in ep or "App.tsx" in ep for ep in entry_points)


def test_detect_key_folders():
    """Test key folder detection."""
    files = [
        FileInfo(
            path="frontend/src/components/Button.tsx",
            name="Button.tsx",
            suffix=".tsx",
            size_bytes=300,
            language="TypeScript",
            role="frontend_component",
            text_preview="export const Button = () => {}",
            line_count=5,
            skipped=False,
        ),
        FileInfo(
            path="backend/routes/api.py",
            name="api.py",
            suffix=".py",
            size_bytes=400,
            language="Python",
            role="backend_route",
            text_preview="@app.get('/api')",
            line_count=10,
            skipped=False,
        ),
        FileInfo(
            path="tests/test_api.py",
            name="test_api.py",
            suffix=".py",
            size_bytes=200,
            language="Python",
            role="test",
            text_preview="def test_api():",
            line_count=5,
            skipped=False,
        ),
    ]
    
    snapshot = RepositorySnapshot(
        source_name="test",
        files=files,
        total_files_seen=3,
        total_files_scanned=3,
        warnings=[],
    )
    
    key_folders = detect_key_folders(snapshot)
    
    assert len(key_folders) >= 3
    folder_str = " ".join(key_folders)
    assert "frontend/" in folder_str
    assert "backend/" in folder_str
    assert "components/" in folder_str or "routes/" in folder_str
    assert "tests/" in folder_str


def test_framework_confidence_scoring():
    """Test that framework confidence scoring works correctly."""
    # Create a snapshot with strong React + Vite evidence
    files = [
        FileInfo(
            path="vite.config.ts",
            name="vite.config.ts",
            suffix=".ts",
            size_bytes=200,
            language="TypeScript",
            role="config",
            text_preview="import { defineConfig } from 'vite'",
            line_count=5,
            skipped=False,
        ),
        FileInfo(
            path="package.json",
            name="package.json",
            suffix=".json",
            size_bytes=500,
            language="JSON",
            role="config",
            text_preview='{"dependencies": {"react": "^18.0.0"}}',
            line_count=10,
            skipped=False,
        ),
        FileInfo(
            path="src/App.tsx",
            name="App.tsx",
            suffix=".tsx",
            size_bytes=800,
            language="TypeScript",
            role="entrypoint",
            text_preview="import React from 'react'",
            line_count=20,
            skipped=False,
        ),
    ]
    
    snapshot = RepositorySnapshot(
        source_name="test",
        files=files,
        total_files_seen=3,
        total_files_scanned=3,
        warnings=[],
    )
    
    finding = detect_framework(REACT_VITE_RULE, snapshot)
    
    assert finding is not None
    assert finding.confidence >= 0.7  # Should have high confidence with multiple evidence


def test_no_false_positives():
    """Test that we don't detect frameworks when there's no evidence."""
    files = [
        FileInfo(
            path="README.md",
            name="README.md",
            suffix=".md",
            size_bytes=1000,
            language="Markdown",
            role="documentation",
            text_preview="# My Project\n\nThis is a documentation repo.",
            line_count=10,
            skipped=False,
        ),
    ]
    
    snapshot = RepositorySnapshot(
        source_name="docs_only",
        files=files,
        total_files_seen=1,
        total_files_scanned=1,
        warnings=[],
    )
    
    # Should not detect React, FastAPI, or Streamlit
    react_finding = detect_framework(REACT_VITE_RULE, snapshot)
    fastapi_finding = detect_framework(FASTAPI_RULE, snapshot)
    streamlit_finding = detect_framework(STREAMLIT_RULE, snapshot)
    
    assert react_finding is None
    assert fastapi_finding is None
    assert streamlit_finding is None


def test_fingerprint_includes_warnings():
    """Test that fingerprint includes warnings from snapshot."""
    files = [
        FileInfo(
            path="test.py",
            name="test.py",
            suffix=".py",
            size_bytes=100,
            language="Python",
            role="unknown",
            text_preview="print('hello')",
            line_count=1,
            skipped=False,
        ),
    ]
    
    snapshot = RepositorySnapshot(
        source_name="test",
        files=files,
        total_files_seen=100,
        total_files_scanned=1,
        warnings=["Reached max file limit (600). Some files were not scanned."],
    )
    
    fingerprint = generate_fingerprint(snapshot)
    
    assert len(fingerprint.warnings) > 0
    assert any("max file limit" in w.lower() for w in fingerprint.warnings)

# Made with Bob
