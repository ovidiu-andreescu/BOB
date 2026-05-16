"""Compatibility exports for deterministic indicator rules.

The framework and project indicator definitions live in
``repoquest.indicator_rules`` so detector code can stay focused on evaluation.
This module remains as a stable import path for tests and older call sites.
"""

from repoquest.indicator_rules import (
  ALL_FRAMEWORK_RULES,
  BACKEND_FRAMEWORKS,
  CLI_TOOLING_RULE,
  DJANGO_RULE,
  ENTRY_POINT_PATTERNS,
  ENTRY_POINT_RULES,
  EXPRESS_RULE,
  FASTAPI_RULE,
  FILE_ROLE_RULES,
  FLASK_RULE,
  FRONTEND_FRAMEWORKS,
  KEY_FOLDERS,
  KEY_FOLDER_RULES,
  NEXTJS_RULE,
  PYTHON_PACKAGE_RULE,
  REACT_VITE_RULE,
  STREAMLIT_RULE,
  EntryPointRule,
  FolderRule,
  FrameworkRule,
  RoleIndicatorRule,
  classify_file_role,
  classify_project_type,
  entry_point_priority,
  format_evidence,
  split_evidence,
)

__all__ = [
  "ALL_FRAMEWORK_RULES",
  "BACKEND_FRAMEWORKS",
  "CLI_TOOLING_RULE",
  "DJANGO_RULE",
  "ENTRY_POINT_PATTERNS",
  "ENTRY_POINT_RULES",
  "EXPRESS_RULE",
  "FASTAPI_RULE",
  "FILE_ROLE_RULES",
  "FLASK_RULE",
  "FRONTEND_FRAMEWORKS",
  "KEY_FOLDERS",
  "KEY_FOLDER_RULES",
  "NEXTJS_RULE",
  "PYTHON_PACKAGE_RULE",
  "REACT_VITE_RULE",
  "STREAMLIT_RULE",
  "EntryPointRule",
  "FolderRule",
  "FrameworkRule",
  "RoleIndicatorRule",
  "classify_file_role",
  "classify_project_type",
  "entry_point_priority",
  "format_evidence",
  "split_evidence",
]

# Made with Bob
