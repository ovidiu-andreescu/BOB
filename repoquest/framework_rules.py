"""Framework detection rules for RepoQuest.

This module contains deterministic rules for detecting frameworks and technologies
in a codebase. Each rule specifies what evidence to look for and how to score it.
"""

from dataclasses import dataclass


@dataclass
class FrameworkRule:
    """A rule for detecting a framework."""
    name: str
    category: str  # "frontend", "backend", "testing", "tooling", "package"
    
    # File-based evidence
    required_files: list[str] = None  # Must have ALL of these
    indicator_files: list[str] = None  # Having ANY increases confidence
    
    # Content-based evidence
    content_patterns: list[str] = None  # Patterns to search for in file content
    
    # Path-based evidence
    indicator_paths: list[str] = None  # Paths that suggest this framework
    
    # Scoring
    base_confidence: float = 0.5  # Starting confidence if any evidence found
    file_match_boost: float = 0.2  # Boost per indicator file found
    content_match_boost: float = 0.15  # Boost per content pattern found
    path_match_boost: float = 0.1  # Boost per indicator path found


# Frontend frameworks
REACT_VITE_RULE = FrameworkRule(
    name="React + Vite",
    category="frontend",
    indicator_files=[
        "vite.config.ts",
        "vite.config.js",
        "vite.config.mjs",
    ],
    content_patterns=[
        "import React",
        "from 'react'",
        'from "react"',
        "react",  # in package.json
    ],
    indicator_paths=[
        "components/",
        "pages/",
        "src/App.tsx",
        "src/App.jsx",
    ],
    base_confidence=0.4,
    file_match_boost=0.25,
    content_match_boost=0.15,
)

NEXTJS_RULE = FrameworkRule(
    name="Next.js",
    category="frontend",
    indicator_files=[
        "next.config.js",
        "next.config.mjs",
        "next.config.ts",
    ],
    content_patterns=[
        "next",  # in package.json
        "from 'next",
        'from "next',
    ],
    indicator_paths=[
        "pages/",
        "app/",
        "page.tsx",
        "layout.tsx",
    ],
    base_confidence=0.5,
    file_match_boost=0.3,
)

# Backend frameworks
FASTAPI_RULE = FrameworkRule(
    name="FastAPI",
    category="backend",
    content_patterns=[
        "from fastapi import FastAPI",
        "from fastapi import",
        "APIRouter",
        "@app.get",
        "@app.post",
        "@router.get",
        "@router.post",
    ],
    indicator_paths=[
        "routes/",
        "api/",
        "main.py",
    ],
    base_confidence=0.3,
    content_match_boost=0.2,
    path_match_boost=0.15,
)

FLASK_RULE = FrameworkRule(
    name="Flask",
    category="backend",
    content_patterns=[
        "from flask import Flask",
        "from flask import",
        "@app.route",
        "flask",  # in requirements.txt
    ],
    indicator_paths=[
        "app.py",
        "routes/",
    ],
    base_confidence=0.3,
    content_match_boost=0.25,
)

EXPRESS_RULE = FrameworkRule(
    name="Express",
    category="backend",
    content_patterns=[
        "express()",
        "app.get",
        "app.post",
        "router.get",
        "router.post",
        '"express"',
        "'express'",
    ],
    indicator_paths=[
        "server.js",
        "app.js",
        "routes/",
    ],
    base_confidence=0.3,
    content_match_boost=0.2,
)

DJANGO_RULE = FrameworkRule(
    name="Django",
    category="backend",
    indicator_files=[
        "manage.py",
    ],
    content_patterns=[
        "django",
        "from django",
        "settings.py",
        "urls.py",
    ],
    indicator_paths=[
        "settings.py",
        "urls.py",
        "views.py",
    ],
    base_confidence=0.4,
    file_match_boost=0.3,
)

# Data/UI frameworks
STREAMLIT_RULE = FrameworkRule(
    name="Streamlit",
    category="frontend",
    content_patterns=[
        "import streamlit as st",
        "import streamlit",
        "st.title",
        "st.sidebar",
        "st.file_uploader",
        "st.button",
    ],
    indicator_paths=[
        "streamlit_app.py",
        "app.py",
    ],
    base_confidence=0.3,
    content_match_boost=0.25,
)

# Package/library indicators
PYTHON_PACKAGE_RULE = FrameworkRule(
    name="Python Package",
    category="package",
    indicator_files=[
        "pyproject.toml",
        "setup.py",
        "setup.cfg",
    ],
    indicator_paths=[
        "__init__.py",
        "tests/",
    ],
    base_confidence=0.4,
    file_match_boost=0.2,
)

# CLI/tooling indicators
CLI_TOOLING_RULE = FrameworkRule(
    name="CLI/Tooling",
    category="tooling",
    content_patterns=[
        "import argparse",
        "import click",
        "import typer",
        'if __name__ == "__main__"',
    ],
    indicator_paths=[
        "cli.py",
    ],
    base_confidence=0.3,
    content_match_boost=0.2,
)

# All rules in detection order
ALL_FRAMEWORK_RULES = [
    REACT_VITE_RULE,
    NEXTJS_RULE,
    FASTAPI_RULE,
    FLASK_RULE,
    EXPRESS_RULE,
    DJANGO_RULE,
    STREAMLIT_RULE,
    PYTHON_PACKAGE_RULE,
    CLI_TOOLING_RULE,
]


# Entry point detection patterns
ENTRY_POINT_PATTERNS = [
    # Backend entry points
    ("backend/main.py", "Backend FastAPI entry point"),
    ("main.py", "Python entry point"),
    ("app.py", "Python/Flask entry point"),
    ("server.js", "Node.js server entry point"),
    ("index.js", "JavaScript entry point"),
    ("manage.py", "Django management entry point"),
    
    # Frontend entry points
    ("frontend/src/App.tsx", "React frontend entry point"),
    ("frontend/src/App.jsx", "React frontend entry point"),
    ("src/App.tsx", "React entry point"),
    ("src/App.jsx", "React entry point"),
    ("src/main.tsx", "React/Vite entry point"),
    ("src/main.jsx", "React/Vite entry point"),
    ("src/index.tsx", "React entry point"),
    ("src/index.jsx", "React entry point"),
    
    # Streamlit
    ("app/streamlit_app.py", "Streamlit app entry point"),
    ("streamlit_app.py", "Streamlit app entry point"),
]


# Project type classification rules
def classify_project_type(frameworks: list[str], entry_points: list[str]) -> tuple[str, float]:
    """Classify project type based on detected frameworks and entry points.
    
    Args:
        frameworks: List of detected framework names
        entry_points: List of detected entry point paths
        
    Returns:
        Tuple of (project_type, confidence)
    """
    has_frontend = any(f in frameworks for f in ["React + Vite", "Next.js"])
    has_backend = any(f in frameworks for f in ["FastAPI", "Flask", "Express", "Django"])
    has_streamlit = "Streamlit" in frameworks
    has_package = "Python Package" in frameworks
    has_cli = "CLI/Tooling" in frameworks
    
    # Full-stack web application
    if has_frontend and has_backend:
        confidence = 0.9 if len(frameworks) >= 2 else 0.75
        return "Full-stack web application", confidence
    
    # Frontend-only
    if has_frontend and not has_backend:
        return "Frontend web application", 0.8
    
    # Backend API
    if has_backend and not has_frontend:
        return "Backend API", 0.8
    
    # Streamlit app
    if has_streamlit:
        return "Streamlit data app", 0.85
    
    # Python package
    if has_package:
        return "Python package/library", 0.75
    
    # CLI/tooling
    if has_cli:
        return "CLI/tooling project", 0.7
    
    # Check for documentation-heavy repos
    if not frameworks and any("README" in ep.upper() for ep in entry_points):
        return "Documentation-heavy repo", 0.5
    
    # Unknown/mixed
    if frameworks:
        return "Unknown/mixed repo", 0.4
    
    return "Unknown/mixed repo", 0.3


# Key folder detection
KEY_FOLDERS = {
    "frontend/": "Frontend code",
    "backend/": "Backend code",
    "src/": "Source code",
    "components/": "UI components",
    "pages/": "Page components",
    "routes/": "API routes",
    "services/": "Business logic",
    "models/": "Data models",
    "tests/": "Test suite",
    "docs/": "Documentation",
    "api/": "API code",
    "app/": "Application code",
}

# Made with Bob
