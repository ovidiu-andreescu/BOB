"""Deterministic indicator rules for RepoQuest.

This module keeps "what to look for" separate from the evaluator code. The
scanner and detector modules should consume these rules instead of embedding
large role/framework branches inline.
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class FrameworkRule:
  """A rule for detecting a framework."""

  name: str
  category: str # "frontend", "backend", "testing", "tooling", "package"

  required_files: list[str] | None = None
  indicator_files: list[str] | None = None
  content_patterns: list[str] | None = None
  indicator_paths: list[str] | None = None

  base_confidence: float = 0.5
  file_match_boost: float = 0.2
  content_match_boost: float = 0.15
  path_match_boost: float = 0.1


@dataclass(frozen=True)
class EntryPointRule:
  """Rule for identifying likely application entry points."""

  pattern: str
  description: str
  priority: int


@dataclass(frozen=True)
class FolderRule:
  """Rule for identifying important project folders."""

  folder: str
  purpose: str


@dataclass(frozen=True)
class RoleIndicatorRule:
  """Path/name/suffix indicators for classifying file roles."""

  role: str
  priority: int
  names: tuple[str, ...] = ()
  suffixes: tuple[str, ...] = ()
  path_parts: tuple[str, ...] = ()
  path_contains: tuple[str, ...] = ()
  name_prefixes: tuple[str, ...] = ()
  name_suffixes: tuple[str, ...] = ()


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
  ],
  indicator_paths=[
    "src/App.tsx",
    "src/App.jsx",
  ],
  base_confidence=0.3,
  file_match_boost=0.3,
  content_match_boost=0.2,
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
    "from 'next",
    'from "next',
  ],
  indicator_paths=[
    "page.tsx",
    "layout.tsx",
  ],
  base_confidence=0.4,
  file_match_boost=0.35,
  content_match_boost=0.2,
)

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
  ],
  indicator_paths=[
    "app.py",
  ],
  base_confidence=0.3,
  content_match_boost=0.3,
)

EXPRESS_RULE = FrameworkRule(
  name="Express",
  category="backend",
  content_patterns=[
    "express()",
    "require('express')",
    'require("express")',
    "from 'express'",
    'from "express"',
    "const express = require",
    "import express from",
  ],
  indicator_paths=[
    "server.js",
    "app.js",
  ],
  base_confidence=0.3,
  content_match_boost=0.25,
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

PYTHON_PACKAGE_RULE = FrameworkRule(
  name="Python Package",
  category="package",
  indicator_files=[
    "setup.py",
    "setup.cfg",
  ],
  content_patterns=[
    "from setuptools import setup",
    "from distutils.core import setup",
  ],
  base_confidence=0.4,
  file_match_boost=0.3,
  content_match_boost=0.2,
)

CLI_TOOLING_RULE = FrameworkRule(
  name="CLI/Tooling",
  category="tooling",
  content_patterns=[
    "import argparse",
    "import click",
    "import typer",
    ' if __name__ == "__main__"',
  ],
  indicator_paths=[
    "cli.py",
  ],
  base_confidence=0.3,
  content_match_boost=0.2,
)

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

FRONTEND_FRAMEWORKS = ("React + Vite", "Next.js")
BACKEND_FRAMEWORKS = ("FastAPI", "Flask", "Express", "Django")

ENTRY_POINT_RULES = [
  EntryPointRule("backend/main.py", "Backend FastAPI entry point", 0),
  EntryPointRule("main.py", "Python entry point", 1),
  EntryPointRule("app.py", "Python/Flask entry point", 2),
  EntryPointRule("server.js", "Node.js server entry point", 3),
  EntryPointRule("index.js", "JavaScript entry point", 4),
  EntryPointRule("manage.py", "Django management entry point", 5),
  EntryPointRule("frontend/src/App.tsx", "React frontend entry point", 10),
  EntryPointRule("frontend/src/App.jsx", "React frontend entry point", 10),
  EntryPointRule("src/App.tsx", "React entry point", 11),
  EntryPointRule("src/App.jsx", "React entry point", 11),
  EntryPointRule("src/main.tsx", "React/Vite entry point", 12),
  EntryPointRule("src/main.jsx", "React/Vite entry point", 12),
  EntryPointRule("src/index.tsx", "React entry point", 13),
  EntryPointRule("src/index.jsx", "React entry point", 13),
  EntryPointRule("app/streamlit_app.py", "Streamlit app entry point", 20),
  EntryPointRule("streamlit_app.py", "Streamlit app entry point", 21),
]

# Compatibility shape for older imports/tests.
ENTRY_POINT_PATTERNS = [(rule.pattern, rule.description) for rule in ENTRY_POINT_RULES]

KEY_FOLDER_RULES = [
  FolderRule("frontend/", "Frontend code"),
  FolderRule("backend/", "Backend code"),
  FolderRule("src/", "Source code"),
  FolderRule("components/", "UI components"),
  FolderRule("pages/", "Page components"),
  FolderRule("routes/", "API routes"),
  FolderRule("services/", "Business logic"),
  FolderRule("models/", "Data models"),
  FolderRule("tests/", "Test suite"),
  FolderRule("docs/", "Documentation"),
  FolderRule("api/", "API code"),
  FolderRule("app/", "Application code"),
]

KEY_FOLDERS = {rule.folder: rule.purpose for rule in KEY_FOLDER_RULES}

FILE_ROLE_RULES = [
  RoleIndicatorRule("documentation", 0, names=("readme.md", "readme.txt", "readme")),
  RoleIndicatorRule(
    "config",
    10,
    names=(
      "package.json",
      "requirements.txt",
      "pyproject.toml",
      "vite.config.ts",
      "vite.config.js",
    ),
  ),
  RoleIndicatorRule(
    "entrypoint",
    20,
    names=("main.py", "app.py", "index.js", "index.ts", "app.tsx", "app.jsx"),
  ),
  RoleIndicatorRule(
    "test",
    30,
    path_parts=("tests", "__tests__"),
    name_prefixes=("test_",),
    name_suffixes=("_test.py", ".test.ts", ".test.tsx", ".spec.ts", ".spec.tsx"),
  ),
  RoleIndicatorRule(
    "frontend_component",
    40,
    suffixes=(".tsx", ".jsx"),
    path_parts=("components",),
  ),
  RoleIndicatorRule(
    "frontend_page",
    50,
    suffixes=(".tsx", ".jsx"),
    path_parts=("pages",),
  ),
  RoleIndicatorRule(
    "api_client",
    60,
    suffixes=(".ts", ".js", ".tsx", ".jsx"),
    path_parts=("api", "services"),
    path_contains=("client", "api"),
  ),
  RoleIndicatorRule("backend_service", 70, path_parts=("services",)),
  RoleIndicatorRule("backend_route", 80, path_parts=("routes",)),
  RoleIndicatorRule("model", 90, path_parts=("models",)),
]


def normalize_repo_path(path: str | Path) -> str:
  """Normalize a file path for deterministic repo-relative matching."""
  return str(path).replace("\\", "/")


def format_evidence(file_path: str, signal: str) -> str:
  """Format evidence consistently for UI/report consumers."""
  return f"{file_path}: {signal}"


def split_evidence(evidence: str) -> tuple[str, str]:
  """Split formatted evidence into source path and signal text."""
  if ":" not in evidence:
    return "Project files", evidence
  source, signal = evidence.split(":", 1)
  return source.strip().strip("`"), signal.strip()


def entry_point_priority(path: str) -> int:
  """Return a deterministic sort priority for an entry point path."""
  normalized = normalize_repo_path(path).lower()
  matching = [
    rule.priority
    for rule in ENTRY_POINT_RULES
    if normalized.endswith(rule.pattern.lower()) or rule.pattern.lower() in normalized
  ]
  return min(matching) if matching else 99


def match_role_rule(file_path: Path, rule: RoleIndicatorRule) -> bool:
  """Return whether a file path matches a role indicator rule."""
  normalized = normalize_repo_path(file_path).lower()
  parts = tuple(part.lower() for part in Path(normalized).parts)
  name = Path(normalized).name
  suffix = Path(normalized).suffix

  if rule.suffixes and suffix not in rule.suffixes:
    return False

  checks = [
    bool(rule.names and name in rule.names),
    bool(rule.path_parts and any(part in parts for part in rule.path_parts)),
    bool(rule.path_contains and any(token in normalized for token in rule.path_contains)),
    bool(rule.name_prefixes and any(name.startswith(prefix) for prefix in rule.name_prefixes)),
    bool(rule.name_suffixes and any(name.endswith(suffix) for suffix in rule.name_suffixes)),
  ]
  return any(checks)


def classify_file_role(file_path: Path) -> str:
  """Classify a file role from declarative path/name indicators."""
  for rule in sorted(FILE_ROLE_RULES, key=lambda item: item.priority):
    if match_role_rule(file_path, rule):
      return rule.role
  return "unknown"


def classify_project_type(frameworks: list[str], entry_points: list[str]) -> tuple[str, float]:
  """Classify project type based on detected frameworks and entry points."""
  framework_set = set(frameworks)

  has_frontend = any(name in framework_set for name in FRONTEND_FRAMEWORKS)
  has_backend = any(name in framework_set for name in BACKEND_FRAMEWORKS)

  project_rules = [
    (has_frontend and has_backend, "Full-stack web application", 0.9 if len(frameworks) >= 2 else 0.75),
    (has_frontend and not has_backend, "Frontend web application", 0.8),
    (has_backend and not has_frontend, "Backend API", 0.8),
    ("Streamlit" in framework_set, "Streamlit data app", 0.85),
    ("Python Package" in framework_set, "Python package/library", 0.75),
    ("CLI/Tooling" in framework_set, "CLI/tooling project", 0.7),
    (
      not frameworks and any("README" in ep.upper() for ep in entry_points),
      "Documentation-heavy repo",
      0.5,
    ),
  ]

  for matched, project_type, confidence in project_rules:
    if matched:
      return project_type, confidence

  if frameworks:
    return "Unknown/mixed repo", 0.4
  return "Unknown/mixed repo", 0.3

# Made with Bob
