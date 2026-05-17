"""RepoQuest - Turn unfamiliar repos into guided onboarding journeys."""

import streamlit as st
import pandas as pd
from pathlib import Path
import tempfile
from html import escape
import re
import json
import streamlit.components.v1 as components

from repoquest.sample_loader import load_demo_repo
from repoquest.scanner import scan_zip
from repoquest.zip_safety import ZIPSafetyError
from repoquest.detectors import generate_fingerprint
from repoquest.route_extractors import extract_all_routes
from repoquest.import_graph import build_import_graph
from repoquest.architecture import (
  generate_architecture_map,
  generate_dependency_graph,
  generate_simple_graph,
  build_graph_data,
  graph_data_to_dot,
  get_node_details,
)
from repoquest.reading_path import (
  generate_reading_path,
  get_language_for_st_code,
  get_understand_points,
  get_improvement_ideas,
)
from repoquest.quest import generate_component_cards, generate_quiz
from repoquest.config import MAX_ZIP_SIZE_MB, MAX_TEXT_PREVIEW_CHARS
from repoquest.report import (
  generate_markdown_report,
  extract_code_snippet,
  get_test_files,
  get_doc_files,
)
from repoquest.workflows import generate_work_plan, export_workflows_markdown
from repoquest.test_intelligence import generate_test_intelligence
from repoquest.assistant_provider import get_assistant_provider
from repoquest.assistant_validation import (
    validate_assistant_response,
    format_validation_message,
    format_recommendation_validation,
)
from repoquest.assistant_context import (
  build_overview_context,
  build_file_context,
  build_component_context,
  build_test_context,
  build_workflow_context,
  build_documentation_context,
)
from repoquest.assistant_models import AssistantRunResult
from repoquest.assistant_state import (
  get_ai_status,
  format_ai_status_for_shell,
  format_ai_status_for_sidebar,
  format_ai_status_for_tab,
)
from repoquest.ai_fusion import run_ai_fusion
from repoquest.indicator_rules import split_evidence
from repoquest.workspace_state import (
  WorkspaceState,
  detect_source_change,
)
from repoquest.models import ProjectFingerprint


def get_workspace() -> WorkspaceState:
  """Get or create workspace state from session."""
  if "workspace" not in st.session_state:
    st.session_state["workspace"] = WorkspaceState()
  return st.session_state["workspace"]


def save_workspace(workspace: WorkspaceState) -> None:
  """Save workspace state to session."""
  st.session_state["workspace"] = workspace
  # Also update individual keys for backward compatibility
  for key, value in workspace.to_dict().items():
    st.session_state[key] = value


def build_display_fingerprint(
    fingerprint: ProjectFingerprint,
    fused_analysis,
) -> ProjectFingerprint:
  """Return the fingerprint that should be shown/exported for this workspace."""
  if not fused_analysis:
    return fingerprint

  warnings = list(fingerprint.warnings)
  if fused_analysis.report and fused_analysis.report.warnings:
    warnings.extend(f"AI Fusion: {warning}" for warning in fused_analysis.report.warnings)

  return ProjectFingerprint(
    project_type=fused_analysis.final_project_type,
    confidence=fused_analysis.final_confidence,
    frameworks=fingerprint.frameworks,
    entry_points=fused_analysis.final_entry_points,
    key_folders=fingerprint.key_folders,
    summary=fused_analysis.final_summary,
    warnings=warnings,
  )


def reset_analysis():
  """Reset all analysis state."""
  workspace = get_workspace()
  workspace.clear_all()
  save_workspace(workspace)





def run_assistant(section_id: str, section_title: str, request_builder, snapshot):
  """Run AI assistant for a section and store result."""
  workspace = get_workspace()
  
  if "assistant_outputs" not in st.session_state:
    st.session_state["assistant_outputs"] = {}

  provider = get_assistant_provider()
  request = request_builder()

  with st.spinner("AI Assistant job running..."):
    response = provider.generate(request)
    validated_response = validate_assistant_response(response, snapshot)

  # Get source_id from workspace metadata
  source_id = workspace.source_metadata.source_id if workspace.source_metadata else ""

  result = AssistantRunResult(
    section_id=section_id,
    section_title=section_title,
    request=request,
    response=validated_response,
    source_id=source_id,
  )

  st.session_state["assistant_outputs"][section_id] = result
  workspace.assistant_outputs[section_id] = result
  save_workspace(workspace)
  return result


def render_assistant_result(result: AssistantRunResult, success_label: str = "AI-assisted response"):
  """Render an assistant run result with status, provider info, and citations."""
  if result.response.status == "ok":
    # Show success with provider/model info
    provider_info = f" ({result.response.provider}/{result.response.model})" if result.response.provider != "unknown" else ""
    st.success(f"✨ {success_label}{provider_info}")
    st.markdown(result.response.response_text)
    if result.response.citations:
      st.caption("📋 Evidence paths")
      citation_data = [
        {
          "File": citation.file_path,
          "Relevance": citation.relevance or "Referenced by assistant",
        }
        for citation in result.response.citations
      ]
      st.dataframe(pd.DataFrame(citation_data), use_container_width=True, hide_index=True)
  else:
    validation_msg = format_validation_message(result.response)
    if validation_msg:
      if result.response.status == "invalid":
        st.error(validation_msg)
        st.info("💡 Deterministic analysis is still available in other tabs.")
      else:
        st.warning(validation_msg)
        if result.response.status == "disabled":
          st.info("💡 Deterministic analysis is available without AI assistance.")


ICON_SVG = {
  "overview": """<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="4" y="4" width="16" height="16" rx="2"></rect><path d="M8 9h8"></path><path d="M8 13h5"></path><path d="M8 17h8"></path></svg>""",
  "architecture": """<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="6" cy="6" r="2"></circle><circle cx="18" cy="6" r="2"></circle><circle cx="12" cy="18" r="2"></circle><path d="M8 7l3 8"></path><path d="M16 7l-3 8"></path><path d="M8 6h8"></path></svg>""",
  "reading": """<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v16H6.5A2.5 2.5 0 0 0 4 21.5z"></path><path d="M4 5.5v16"></path><path d="M8 7h8"></path><path d="M8 11h6"></path></svg>""",
  "components": """<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="4" y="4" width="7" height="7" rx="1.5"></rect><rect x="13" y="4" width="7" height="7" rx="1.5"></rect><rect x="4" y="13" width="7" height="7" rx="1.5"></rect><rect x="13" y="13" width="7" height="7" rx="1.5"></rect></svg>""",
  "tests": """<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 3h6"></path><path d="M10 3v5l-5 9a3 3 0 0 0 2.6 4.5h8.8A3 3 0 0 0 19 17l-5-9V3"></path><path d="M8 15h8"></path></svg>""",
  "workplans": """<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="4" y="4" width="16" height="16" rx="2"></rect><path d="M8 8h8"></path><path d="M8 12h8"></path><path d="M8 16h5"></path></svg>""",
  "quiz": """<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"></circle><path d="M9.5 9a2.5 2.5 0 0 1 4.5 1.5c0 1.7-2 2.1-2 3.5"></path><path d="M12 17h.01"></path></svg>""",
  "docs": """<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 3h8l4 4v14H6z"></path><path d="M14 3v5h4"></path><path d="M9 13h6"></path><path d="M9 17h6"></path></svg>""",
  "export": """<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3v12"></path><path d="M8 11l4 4 4-4"></path><path d="M5 19h14"></path></svg>""",
  "bob": """<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="5" y="6" width="14" height="12" rx="3"></rect><path d="M12 3v3"></path><path d="M9 11h.01"></path><path d="M15 11h.01"></path><path d="M9 15h6"></path></svg>""",
  "assistant": """<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3l1.4 4.2L18 9l-4.6 1.8L12 15l-1.4-4.2L6 9l4.6-1.8z"></path><path d="M5 17l.7 2 2.3.8-2.3.8-.7 2-.7-2-2.3-.8 2.3-.8z"></path></svg>""",
  "folder": """<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 6.5A2.5 2.5 0 0 1 5.5 4H10l2 2h6.5A2.5 2.5 0 0 1 21 8.5v8A2.5 2.5 0 0 1 18.5 19h-13A2.5 2.5 0 0 1 3 16.5z"></path></svg>""",
  "file": """<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 3h8l4 4v14H6z"></path><path d="M14 3v5h4"></path></svg>""",
  "route": """<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h11"></path><path d="M12 4l3 3-3 3"></path><path d="M20 17H9"></path><path d="M12 14l-3 3 3 3"></path></svg>""",
  "shield": """<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3l7 3v5c0 4.5-2.7 8.3-7 10-4.3-1.7-7-5.5-7-10V6z"></path><path d="M9 12l2 2 4-4"></path></svg>""",
  "warning": """<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 4l9 16H3z"></path><path d="M12 9v4"></path><path d="M12 17h.01"></path></svg>""",
}


def render_ui_styles():
  """Render shared UI styling for RepoQuest."""
  st.markdown(
    """
    <style>
      .rq-hero {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        padding: 0.7rem 0.95rem;
        border: 1px solid #d8dee9;
        border-radius: 8px;
        background: #ffffff;
        margin: 0.05rem 0 0.75rem;
      }
      .rq-hero h1 {
        margin: 0;
        color: #1f2937;
        font-size: 1.35rem;
        letter-spacing: 0;
      }
      .rq-hero p {
        margin: 0.1rem 0 0;
        color: #536173;
        font-size: 0.86rem;
      }
      .rq-hero-main,
      .rq-hero-meta {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        min-width: 0;
      }
      .rq-hero-copy {
        min-width: 0;
      }
      .rq-hero-meta {
        flex-wrap: wrap;
        justify-content: flex-end;
      }
      .rq-brand-icon,
      .rq-icon {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        flex: 0 0 auto;
        border-radius: 8px;
      }
      .rq-brand-icon {
        width: 2.45rem;
        height: 2.45rem;
        color: #1f4f7a;
        background: #e8f1fb;
        border: 1px solid #cfe0f4;
      }
      .rq-brand-icon svg {
        width: 1.35rem;
        height: 1.35rem;
        stroke: currentColor;
        fill: none;
        stroke-width: 2;
        stroke-linecap: round;
        stroke-linejoin: round;
      }
      .rq-section {
        display: flex;
        position: relative;
        align-items: center;
        gap: 0.9rem;
        padding: 0.95rem 1.1rem;
        border: 1px solid #dbe3ef;
        border-left: 6px solid #3b82f6;
        border-radius: 8px;
        background: #f8fbff;
        margin: 0.15rem 0 1rem;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
      }
      .rq-section .rq-icon {
        width: 2.35rem;
        height: 2.35rem;
        color: #1f4f7a;
        background: #eef5ff;
        border: 1px solid #cfe0f4;
      }
      .rq-section-title {
        display: block;
        color: #1f2937;
        font-weight: 700;
        font-size: 1.12rem;
        line-height: 1.25;
      }
      .rq-section-subtitle {
        display: block;
        color: #5b6472;
        font-size: 0.92rem;
        margin-top: 0.18rem;
      }
      .rq-mini-label {
        display: flex;
        align-items: center;
        gap: 0.45rem;
        color: #263241;
        font-weight: 700;
        font-size: 0.9rem;
        margin: 0.55rem 0 0.35rem;
      }
      .rq-mini-label .rq-icon {
        width: 1.6rem;
        height: 1.6rem;
        color: #1f4f7a;
        background: #eef5ff;
      }
      .rq-icon svg,
      .rq-mini-label svg {
        width: 1rem;
        height: 1rem;
        stroke: currentColor;
        fill: none;
        stroke-width: 2;
        stroke-linecap: round;
        stroke-linejoin: round;
      }
      .rq-badge {
        display: inline-flex;
        align-items: center;
        min-height: 1.35rem;
        padding: 0.12rem 0.55rem;
        border-radius: 999px;
        border: 1px solid #d7dee9;
        background: #f8fafc;
        color: #334155;
        font-size: 0.78rem;
        font-weight: 700;
        line-height: 1.2;
        white-space: nowrap;
      }
      .rq-shell-chip {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        min-height: 1.75rem;
        padding: 0.24rem 0.6rem;
        border-radius: 999px;
        border: 1px solid #d7dee9;
        background: #f8fafc;
        color: #334155;
        font-size: 0.78rem;
        font-weight: 700;
        white-space: nowrap;
      }
      .rq-shell-chip strong {
        color: #64748b;
        font-size: 0.68rem;
        text-transform: uppercase;
        letter-spacing: 0.02em;
      }
      .rq-focus-panel {
        padding: 0.85rem 0.95rem;
        border: 1px solid #dbe3ef;
        border-radius: 8px;
        background: #fbfdff;
        margin: 0.25rem 0 0.85rem;
      }
      .rq-focus-panel h3 {
        margin: 0 0 0.35rem;
        font-size: 1.02rem;
        color: #1f2937;
      }
      .rq-focus-panel p {
        margin: 0;
        color: #536173;
        line-height: 1.4;
      }
      .rq-component-intro {
        padding: 0.75rem 0.85rem;
        border: 1px solid #e1e6ef;
        border-radius: 8px;
        background: #fbfdff;
        margin: 0.25rem 0 0.8rem;
      }
      .rq-component-intro p {
        margin: 0.55rem 0 0;
        color: #3f4b5c;
        line-height: 1.45;
      }
      .rq-meta-row {
        display: inline-grid;
        margin: 0.35rem 0 0.9rem;
        gap: 0.5rem;
        max-width: 100%;
      }
      .rq-meta-chip {
        display: block;
        box-sizing: border-box;
        min-width: 0;
        padding: 0.45rem 0.6rem;
        border: 1px solid #d7dee9;
        border-radius: 8px;
        background: #f8fafc;
        color: #334155;
        line-height: 1.2;
      }
      .rq-meta-chip strong {
        display: block;
        margin-bottom: 0.18rem;
        color: #64748b;
        font-size: 0.68rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.02em;
      }
      .rq-meta-chip .rq-meta-value {
        display: block;
        min-width: 0;
        overflow-wrap: anywhere;
        color: #1f2937;
        font-size: 0.9rem;
        font-weight: 700;
      }
      .rq-path-chip {
        margin-left: 0.45rem;
        color: #475569;
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        font-size: 0.82rem;
      }
      .rq-tone-blue { border-left-color: #2563eb; }
      .rq-tone-green { border-left-color: #16a34a; }
      .rq-tone-orange { border-left-color: #ea580c; }
      .rq-tone-purple { border-left-color: #7c3aed; }
      .rq-tone-red { border-left-color: #dc2626; }
      .rq-tone-slate { border-left-color: #475569; }
      .rq-tone-cyan { border-left-color: #0891b2; }
      .rq-section.rq-tone-blue { background: #f8fbff; border-color: #cfe0f4; border-left-color: #2563eb; }
      .rq-section.rq-tone-green { background: #f6fdf8; border-color: #ccefd6; border-left-color: #16a34a; }
      .rq-section.rq-tone-orange { background: #fff8f3; border-color: #fed7aa; border-left-color: #ea580c; }
      .rq-section.rq-tone-purple { background: #fbf8ff; border-color: #ddd6fe; border-left-color: #7c3aed; }
      .rq-section.rq-tone-red { background: #fff7f7; border-color: #fecaca; border-left-color: #dc2626; }
      .rq-section.rq-tone-slate { background: #f8fafc; border-color: #d8dee8; border-left-color: #475569; }
      .rq-section.rq-tone-cyan { background: #f7feff; border-color: #a5f3fc; border-left-color: #0891b2; }
      .rq-tone-blue .rq-icon, .rq-badge-blue { color: #1d4ed8; background: #eff6ff; border-color: #bfdbfe; }
      .rq-tone-green .rq-icon, .rq-badge-green { color: #15803d; background: #f0fdf4; border-color: #bbf7d0; }
      .rq-tone-orange .rq-icon, .rq-badge-orange { color: #c2410c; background: #fff7ed; border-color: #fed7aa; }
      .rq-tone-purple .rq-icon, .rq-badge-purple { color: #6d28d9; background: #f5f3ff; border-color: #ddd6fe; }
      .rq-tone-red .rq-icon, .rq-badge-red { color: #b91c1c; background: #fef2f2; border-color: #fecaca; }
      .rq-tone-slate .rq-icon, .rq-badge-slate { color: #334155; background: #f8fafc; border-color: #cbd5e1; }
      .rq-tone-cyan .rq-icon, .rq-badge-cyan { color: #0e7490; background: #ecfeff; border-color: #a5f3fc; }
      .rq-code-shell {
        border: 1px solid #d8dee9;
        border-radius: 8px;
        overflow: hidden;
        margin: 0.2rem 0 0.4rem;
      }
      .rq-code-body {
        margin: 0;
        padding: 0.95rem 1.05rem;
        overflow: auto;
        white-space: pre;
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
        font-size: 0.86rem;
        line-height: 1.55;
      }
      .rq-code-light .rq-code-body {
        color: #263241;
        background: #f8fafc;
      }
      .rq-code-dark .rq-code-body {
        color: #d8dee9;
        background: #101827;
      }
      .rq-code-light .rq-syn-heading { color: #b91c1c; font-weight: 700; }
      .rq-code-dark .rq-syn-heading { color: #f87171; font-weight: 700; }
      .rq-code-light .rq-syn-keyword { color: #1d4ed8; font-weight: 700; }
      .rq-code-dark .rq-syn-keyword { color: #93c5fd; font-weight: 700; }
      .rq-code-light .rq-syn-string { color: #047857; }
      .rq-code-dark .rq-syn-string { color: #86efac; }
      .rq-code-light .rq-syn-comment { color: #64748b; font-style: italic; }
      .rq-code-dark .rq-syn-comment { color: #94a3b8; font-style: italic; }
      .rq-code-light .rq-syn-bullet { color: #9333ea; }
      .rq-code-dark .rq-syn-bullet { color: #c4b5fd; }
      iframe[title="st.iframe"] {
        width: 100% !important;
        max-width: 100% !important;
        border: 0;
      }
      div[data-testid="stGraphVizChart"] {
        display: flex;
        justify-content: center;
        align-items: flex-start;
        max-width: 100%;
        overflow-x: auto;
      }
      div[data-testid="stGraphVizChart"] svg {
        width: 900px !important;
        height: auto !important;
        max-height: 520px !important;
        max-width: 100% !important;
      }
    </style>
    """,
    unsafe_allow_html=True,
  )


def _icon(icon_name: str) -> str:
  """Return a static SVG icon."""
  return ICON_SVG.get(icon_name, ICON_SVG["file"])


def render_hero():
  """Render the product header."""
  workspace = get_workspace()
  ai_status = get_ai_status()
  shell_status = format_ai_status_for_shell(ai_status)

  if workspace.source_metadata:
    source_label = escape(workspace.source_metadata.source_name)
    files_label = f"{workspace.source_metadata.file_count} scanned"
  else:
    source_label = "No source analyzed"
    files_label = "Ready"

  ai_label = shell_status["label"]
  ai_title = shell_status.get("title", "")

  st.markdown(
    f"""
    <div class="rq-hero">
      <div class="rq-hero-main">
        <span class="rq-brand-icon">{_icon("architecture")}</span>
        <div class="rq-hero-copy">
          <h1>RepoQuest</h1>
          <p>Focused repository onboarding workspace.</p>
        </div>
      </div>
      <div class="rq-hero-meta">
        <span class="rq-shell-chip"><strong>Source</strong>{source_label}</span>
        <span class="rq-shell-chip"><strong>Scan</strong>{escape(files_label)}</span>
        <span class="rq-shell-chip" title="{escape(ai_title)}"><strong>Mode</strong>{escape(ai_label)}</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
  )


def render_section_header(title: str, subtitle: str = "", icon: str = "file", tone: str = "blue"):
  """Render an iconized section header."""
  subtitle_html = f'<span class="rq-section-subtitle">{escape(subtitle)}</span>' if subtitle else ""
  st.markdown(
    f"""
    <div class="rq-section rq-tone-{escape(tone)}">
      <span class="rq-icon">{_icon(icon)}</span>
      <span>
        <span class="rq-section-title">{escape(title)}</span>
        {subtitle_html}
      </span>
    </div>
    """,
    unsafe_allow_html=True,
  )


def render_mini_label(title: str, icon: str = "file", tone: str = "blue"):
  """Render a compact label for repeated subsections."""
  st.markdown(
    f"""
    <div class="rq-mini-label rq-tone-{escape(tone)}">
      <span class="rq-icon">{_icon(icon)}</span>
      <span>{escape(title)}</span>
    </div>
    """,
    unsafe_allow_html=True,
  )


def role_badge_html(label: str, tone: str = "slate") -> str:
  """Return a small escaped badge."""
  return f'<span class="rq-badge rq-badge-{escape(tone)}">{escape(label)}</span>'


def render_component_intro(role: str, path: str, description: str, tone: str = "blue"):
  """Render a component card intro block."""
  role_label = role.replace("_", " ").title()
  st.markdown(
    f"""
    <div class="rq-component-intro rq-tone-{escape(tone)}">
      {role_badge_html(role_label, tone)}
      <span class="rq-path-chip">{escape(path)}</span>
      <p>{escape(description)}</p>
    </div>
    """,
    unsafe_allow_html=True,
  )


def render_metadata_chips(items: list[tuple[str, str | int]]):
  """Render compact metadata chips that do not truncate long values."""
  chip_html = "\n".join(
    f"""
    <div class="rq-meta-chip">
      <strong>{escape(str(label))}</strong>
      <span class="rq-meta-value">{escape(str(value))}</span>
    </div>
    """
    for label, value in items
  )
  st.markdown(
    f"""
    <div class="rq-meta-row" style="grid-template-columns: repeat({len(items)}, minmax(8.5rem, 12rem));">
      {chip_html}
    </div>
    """,
    unsafe_allow_html=True,
  )


def render_sidebar_about():
  """Render product/about content in the persistent sidebar."""
  with st.expander("About RepoQuest"):
    st.markdown("**RepoQuest** turns a small repo into an onboarding workspace.")
    st.caption("Core analysis is deterministic static analysis. AI Review is optional, manual, evidence-cited, and validation-gated.")

  with st.expander("Built with IBM Bob"):
    st.markdown("IBM Bob helped build the scanner, framework rules, graphing, tests, docs, and UI.")
    st.caption("IBM Bob is a development partner here, not a runtime dependency.")
    st.caption("Session reports belong in `bob_sessions/` before final submission.")


def build_conceptual_architecture_dot(snapshot, fingerprint, routes) -> str:
  """Build a high-level architecture graph with generic system names."""
  roles = {file.role for file in snapshot.files if not file.skipped}
  has_frontend = bool(roles & {"frontend_page", "frontend_component", "api_client"})
  has_backend = bool(roles & {"backend_route", "backend_service"})
  has_models = "model" in roles or "data" in roles
  has_tests = "test" in roles
  has_docs = "documentation" in roles

  lines = [
    "digraph ConceptualArchitecture {",
    " rankdir=LR;",
    ' graph [pad="0.25", nodesep="0.45", ranksep="0.55"];',
    ' node [shape=box, style="rounded,filled", fontcolor="#111827", color="#334155", fillcolor="#F8FAFC"];',
    ' edge [color="#64748B", fontcolor="#475569"];',
    "",
  ]

  lines.append(' "Contributor" [fillcolor="#EFF6FF"];')
  if has_docs:
    lines.append(' "Docs / README" [fillcolor="#F8FAFC"];')
    lines.append(' "Contributor" -> "Docs / README" [label="starts with"];')

  if has_frontend:
    lines.append(' "Browser / User" [fillcolor="#ECFEFF"];')
    lines.append(' "Frontend App" [fillcolor="#DCFCE7"];')
    lines.append(' "Pages" [fillcolor="#DCFCE7"];')
    lines.append(' "UI Components" [fillcolor="#DCFCE7"];')
    lines.append(' "API Client" [fillcolor="#FEF9C3"];')
    lines.append(' "Browser / User" -> "Frontend App";')
    lines.append(' "Frontend App" -> "Pages";')
    lines.append(' "Pages" -> "UI Components";')
    lines.append(' "Pages" -> "API Client";')
    if has_docs:
      lines.append(' "Docs / README" -> "Frontend App" [style=dashed];')

  if has_backend or routes:
    gateway_label = f"API Routes / Gateway\\n{len(routes)} detected route(s)" if routes else "API Routes / Gateway"
    lines.append(f' "API Routes / Gateway" [label="{gateway_label}", fillcolor="#FFEDD5"];')
    if has_frontend:
      lines.append(' "API Client" -> "API Routes / Gateway" [label="HTTP/API", color="#2563EB"];')
    else:
      lines.append(' "Contributor" -> "API Routes / Gateway";')
    if has_docs:
      lines.append(' "Docs / README" -> "API Routes / Gateway" [style=dashed];')

  if "backend_service" in roles:
    lines.append(' "Services / Business Logic" [fillcolor="#FFEDD5"];')
    lines.append(' "API Routes / Gateway" -> "Services / Business Logic";')

  if has_models:
    storage_label = "Models / Storage Boundary"
    lines.append(f' "{storage_label}" [fillcolor="#E0F2FE"];')
    if "backend_service" in roles:
      lines.append(f' "Services / Business Logic" -> "{storage_label}";')
    elif has_backend or routes:
      lines.append(f' "API Routes / Gateway" -> "{storage_label}";')

  if has_tests:
    lines.append(' "Test Suite" [fillcolor="#F3E8FF"];')
    if has_backend or routes:
      lines.append(' "Test Suite" -> "API Routes / Gateway" [style=dashed, label="validates"];')
    elif has_frontend:
      lines.append(' "Test Suite" -> "Frontend App" [style=dashed, label="validates"];')

  framework_label = "\\n".join(f.name for f in fingerprint.frameworks[:4]) if fingerprint else ""
  if framework_label:
    lines.append(f' "Detected Frameworks" [label="Detected Frameworks\\n{framework_label}", fillcolor="#F1F5F9"];')
    lines.append(' "Contributor" -> "Detected Frameworks" [style=dashed];')

  lines.append("}")
  return "\n".join(lines)


def build_file_tree_text(files) -> str:
  """Build a compact ASCII tree from scanned file paths."""
  root: dict[str, dict] = {}
  for file in sorted(files, key=lambda item: item.path):
    parts = file.path.split("/")
    cursor = root
    for part in parts:
      cursor = cursor.setdefault(part, {})

  lines: list[str] = []

  def walk(node: dict[str, dict], prefix: str = "") -> None:
    entries = sorted(node.items(), key=lambda item: (bool(item[1]), item[0].lower()))
    for index, (name, child) in enumerate(entries):
      connector = "`-- " if index == len(entries) - 1 else "|-- "
      lines.append(f"{prefix}{connector}{name}")
      extension = "    " if index == len(entries) - 1 else "|   "
      if child:
        walk(child, prefix + extension)

  walk(root)
  return "\n".join(lines[:450])


def render_file_analysis_panel(file_info, snapshot, edges, routes, key_prefix: str):
  """Render a focused file analysis surface."""
  render_metadata_chips([
    ("Role", file_info.role.replace("_", " ").title()),
    ("Language", file_info.language),
    ("Lines", file_info.line_count),
    ("Size", format_file_size(file_info.size_bytes)),
  ])

  render_mini_label("Deterministic Analysis", "overview", tone_for_role(file_info.role))
  st.markdown(f"**Path:** `{file_info.path}`")
  if file_info.skipped:
    st.warning(file_info.skip_reason or "This file was skipped.")
  elif file_info.role == "entrypoint":
    st.markdown("Likely application startup or app shell.")
  elif file_info.role == "backend_route":
    st.markdown("Likely API route/controller layer where requests enter the backend.")
  elif file_info.role == "api_client":
    st.markdown("Likely frontend-to-backend API client boundary.")
  elif file_info.role == "backend_service":
    st.markdown("Likely business logic or orchestration layer.")
  elif file_info.role in {"frontend_page", "frontend_component"}:
    st.markdown("Likely frontend UI surface.")
  elif file_info.role == "test":
    st.markdown("Likely test coverage for app behavior.")
  else:
    st.markdown("RepoQuest classified this file from its path, extension, and content hints.")

  incoming = sorted({edge.source for edge in edges if edge.target == file_info.path})
  outgoing = sorted({edge.target for edge in edges if edge.source == file_info.path})
  related_routes = [route for route in routes if route.file_path == file_info.path]

  dep_col, route_col = st.columns(2)
  with dep_col:
    render_mini_label("Dependencies", "architecture", "blue")
    dep_rows = [{"Direction": "Imported by", "File": path} for path in incoming[:8]]
    dep_rows += [{"Direction": "Imports", "File": path} for path in outgoing[:8]]
    if dep_rows:
      st.dataframe(pd.DataFrame(dep_rows), use_container_width=True, hide_index=True)
    else:
      st.caption("No local dependency edges detected.")

  with route_col:
    render_mini_label("Routes", "route", "orange")
    if related_routes:
      st.dataframe(
        pd.DataFrame([
          {"Method": route.method, "Path": route.path, "Function": route.function_name or "N/A"}
          for route in related_routes
        ]),
        use_container_width=True,
        hide_index=True,
      )
    else:
      st.caption("No API routes detected in this file.")

  if file_info.text_preview and not file_info.skipped:
    render_mini_label("Code View", "file", tone_for_role(file_info.role))
    render_code_viewer(
      file_info.text_preview,
      get_language_for_st_code(file_info),
      key=f"{key_prefix}_{file_info.path}",
      title=file_info.path,
      compact_chars=8_000,
      expanded_chars=MAX_TEXT_PREVIEW_CHARS,
      compact_height=430,
      expanded_height=720,
    )

  render_mini_label("AI Review", "assistant", "purple")
  ai_status = get_ai_status()
  if ai_status.is_ready:
    section_key = f"{key_prefix}_ai_{file_info.path}"
    if st.button(f"Review {file_info.name}", key=section_key):
      def build_request():
        return build_file_context(file_info, snapshot, routes) # type: ignore
      result = run_assistant(section_key, f"File: {file_info.name}", build_request, snapshot)

    if "assistant_outputs" in st.session_state and section_key in st.session_state["assistant_outputs"]:
      result = st.session_state["assistant_outputs"][section_key]
      render_assistant_result(result, "AI-assisted file review")
  else:
    tab_caption = format_ai_status_for_tab(ai_status)
    if tab_caption:
      st.caption(tab_caption)


def format_file_size(size_bytes: int) -> str:
  """Format file size without rounding small files down to 0 KB."""
  if size_bytes < 1024:
    return f"{size_bytes} B"
  if size_bytes < 1024 * 1024:
    return f"{size_bytes / 1024:.1f} KB"
  return f"{size_bytes / (1024 * 1024):.1f} MB"


def tone_for_role(role: str) -> str:
  """Map file roles to visual tones."""
  if role in {"entrypoint", "api_client"}:
    return "blue"
  if role in {"frontend_component", "frontend_page", "style"}:
    return "green"
  if role in {"backend_route", "backend_service"}:
    return "orange"
  if role == "test":
    return "purple"
  if role in {"model", "data"}:
    return "cyan"
  if role in {"config", "documentation"}:
    return "slate"
  return "slate"


def safe_widget_key(value: str) -> str:
  """Create a stable Streamlit widget key fragment."""
  return re.sub(r"[^A-Za-z0-9_]+", "_", value).strip("_")[:100] or "code"


def _highlight_code_line(line: str, language: str) -> str:
  """Apply lightweight deterministic syntax highlighting to one escaped line."""
  normalized_language = (language or "text").lower()
  escaped_line = escape(line)

  if normalized_language in {"markdown", "md"}:
    stripped = line.lstrip()
    if stripped.startswith("#"):
      return f'<span class="rq-syn-heading">{escaped_line}</span>'
    if stripped.startswith(("-", "*", "+")):
      return f'<span class="rq-syn-bullet">{escaped_line}</span>'
    return escaped_line

  keyword_pattern = (
    r"\b("
    r"async|await|break|case|class|const|def|elif|else|except|export|False|for|from|"
    r"function|if|import|in|interface|let|None|return|try|True|type|while|with"
    r")\b"
  )
  highlighted = re.sub(
    keyword_pattern,
    r'<span class="rq-syn-keyword">\1</span>',
    escaped_line,
  )
  highlighted = re.sub(
    r"(&quot;.*?&quot;|&#x27;.*?&#x27;)",
    r'<span class="rq-syn-string">\1</span>',
    highlighted,
  )

  if normalized_language in {"python", "py", "toml", "yaml", "yml"}:
    highlighted = re.sub(r"(#.*)$", r'<span class="rq-syn-comment">\1</span>', highlighted)
  elif normalized_language in {"javascript", "typescript", "js", "ts", "tsx", "jsx", "css"}:
    highlighted = re.sub(r"(//.*)$", r'<span class="rq-syn-comment">\1</span>', highlighted)

  return highlighted


def highlight_code_html(text: str, language: str) -> str:
  """Return syntax-highlighted HTML for a code buffer."""
  if not text:
    return ""
  return "<br>".join(_highlight_code_line(line, language) for line in text.splitlines())


def json_for_inline_script(value: str) -> str:
  """Serialize text for a JS string inside a script tag without closing it early."""
  return json.dumps(value).replace("</", "<\\/")


def render_code_viewer(
  text: str,
  language: str | None,
  key: str,
  title: str = "File preview",
  compact_chars: int = 8_000,
  expanded_chars: int = MAX_TEXT_PREVIEW_CHARS,
  compact_height: int = 360,
  expanded_height: int = 680,
):
  """Render a bounded, scrollable source preview with inline controls."""
  if not text:
    st.info("No preview available.")
    return

  key_fragment = safe_widget_key(key)
  language_label = language or "text"
  compact_limit = min(compact_chars, MAX_TEXT_PREVIEW_CHARS)
  expanded_limit = min(expanded_chars, MAX_TEXT_PREVIEW_CHARS)
  compact_text = text[:compact_limit]
  expanded_text = text[:expanded_limit]
  compact_html = highlight_code_html(compact_text, language_label)
  expanded_html = highlight_code_html(expanded_text, language_label)
  notice_html = ""
  if len(text) > compact_limit:
    notice_html = (
      f'<div class="rq-code-notice">Showing first {compact_limit:,} characters. '
      f'Open fullscreen to use the {expanded_limit:,}-character buffer.</div>'
    )

  viewer_id = f"rq-code-{key_fragment}"
  popup_html = f"""
  <!doctype html>
  <html>
    <head>
      <meta charset="utf-8">
      <title>{escape(title)} - RepoQuest code viewer</title>
      <style>
        :root {{
          color-scheme: light dark;
          font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }}
        body {{
          margin: 0;
          background: #101827;
        }}
        .rq-popup-shell {{
          min-height: 100vh;
          color: #d8dee9;
          background: #101827;
        }}
        .rq-popup-shell.rq-code-light {{
          color: #263241;
          background: #f8fafc;
        }}
        .rq-popup-bar {{
          position: sticky;
          top: 0;
          z-index: 2;
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 1rem;
          min-height: 3rem;
          padding: 0.55rem 0.8rem;
          border-bottom: 1px solid #263447;
          background: rgba(15, 23, 42, 0.96);
        }}
        .rq-code-light .rq-popup-bar {{
          border-bottom-color: #d8dee9;
          background: rgba(248, 250, 252, 0.96);
        }}
        .rq-popup-title {{
          min-width: 0;
          overflow: hidden;
          color: inherit;
          font-size: 0.86rem;
          font-weight: 700;
          text-overflow: ellipsis;
          white-space: nowrap;
        }}
        .rq-popup-actions {{
          display: flex;
          gap: 0.4rem;
          flex: 0 0 auto;
        }}
        .rq-popup-action {{
          border: 1px solid #334155;
          border-radius: 7px;
          background: #1e293b;
          color: #e2e8f0;
          cursor: pointer;
          font-size: 0.8rem;
          font-weight: 700;
          height: 2rem;
          padding: 0 0.7rem;
        }}
        .rq-code-light .rq-popup-action {{
          border-color: #cbd5e1;
          background: #ffffff;
          color: #263241;
        }}
        .rq-popup-body {{
          box-sizing: border-box;
          min-height: calc(100vh - 3.2rem);
          margin: 0;
          padding: 1rem 1.15rem 2rem;
          overflow: auto;
          white-space: pre;
          font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
          font-size: 0.9rem;
          line-height: 1.55;
        }}
        .rq-syn-heading {{ color: #f87171; font-weight: 700; }}
        .rq-code-light .rq-syn-heading {{ color: #b91c1c; }}
        .rq-syn-keyword {{ color: #93c5fd; font-weight: 700; }}
        .rq-code-light .rq-syn-keyword {{ color: #1d4ed8; }}
        .rq-syn-string {{ color: #86efac; }}
        .rq-code-light .rq-syn-string {{ color: #047857; }}
        .rq-syn-comment {{ color: #94a3b8; font-style: italic; }}
        .rq-code-light .rq-syn-comment {{ color: #64748b; }}
        .rq-syn-bullet {{ color: #c4b5fd; }}
        .rq-code-light .rq-syn-bullet {{ color: #9333ea; }}
      </style>
    </head>
    <body>
      <main class="rq-popup-shell" id="viewer">
        <div class="rq-popup-bar">
          <div class="rq-popup-title">{escape(title)} | {escape(language_label)}</div>
          <div class="rq-popup-actions">
            <button class="rq-popup-action" type="button" id="theme">Dark</button>
            <button class="rq-popup-action" type="button" onclick="window.close()">Close</button>
          </div>
        </div>
        <pre class="rq-popup-body">{expanded_html}</pre>
      </main>
      <script>
        const shell = document.getElementById("viewer");
        const themeButton = document.getElementById("theme");
        themeButton.addEventListener("click", () => {{
          const light = shell.classList.toggle("rq-code-light");
          themeButton.textContent = light ? "Light" : "Dark";
        }});
      </script>
    </body>
  </html>
  """
  html = f"""
  <!doctype html>
  <html>
    <head>
      <meta charset="utf-8">
      <style>
        :root {{
          color-scheme: light dark;
          font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }}
        body {{
          margin: 0;
          background: transparent;
        }}
        .rq-code-card {{
          position: relative;
          overflow: hidden;
          border: 1px solid #d8dee9;
          border-radius: 8px;
          background: #f8fafc;
        }}
        .rq-code-card.rq-code-dark {{
          background: #101827;
          border-color: #263447;
        }}
        .rq-code-label {{
          position: absolute;
          z-index: 3;
          top: 0.65rem;
          left: 0.75rem;
          max-width: calc(100% - 11rem);
          padding: 0.2rem 0.45rem;
          border-radius: 6px;
          background: rgba(248, 250, 252, 0.9);
          color: #64748b;
          font-size: 0.76rem;
          line-height: 1.2;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }}
        .rq-code-dark .rq-code-label {{
          background: rgba(15, 23, 42, 0.9);
          color: #aab6c7;
        }}
        .rq-code-actions {{
          position: absolute;
          z-index: 4;
          top: 0.55rem;
          right: 0.55rem;
          display: flex;
          gap: 0.35rem;
          align-items: center;
        }}
        .rq-code-action {{
          display: inline-flex;
          align-items: center;
          justify-content: center;
          min-width: 2.25rem;
          height: 2rem;
          padding: 0 0.55rem;
          border: 1px solid #cbd5e1;
          border-radius: 7px;
          background: rgba(255, 255, 255, 0.92);
          color: #263241;
          font-size: 0.78rem;
          font-weight: 700;
          cursor: pointer;
          box-shadow: 0 1px 4px rgba(15, 23, 42, 0.08);
        }}
        .rq-code-dark .rq-code-action {{
          border-color: #334155;
          background: rgba(30, 41, 59, 0.94);
          color: #e2e8f0;
        }}
        .rq-code-action:hover {{
          border-color: #2563eb;
        }}
        .rq-code-action svg {{
          width: 1rem;
          height: 1rem;
          stroke: currentColor;
          fill: none;
          stroke-width: 2;
          stroke-linecap: round;
          stroke-linejoin: round;
        }}
        .rq-code-body {{
          max-height: {compact_height}px;
          min-height: 7rem;
          margin: 0;
          padding: 3.2rem 1.05rem 1rem;
          overflow: auto;
          white-space: pre;
          color: #263241;
          background: #f8fafc;
          font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
          font-size: 0.86rem;
          line-height: 1.55;
        }}
        .rq-code-dark .rq-code-body {{
          color: #d8dee9;
          background: #101827;
        }}
        .rq-code-expanded-fallback .rq-code-body {{
          max-height: {expanded_height}px;
        }}
        .rq-code-notice {{
          padding: 0.5rem 0.8rem;
          border-top: 1px solid #e1e6ef;
          color: #64748b;
          background: #ffffff;
          font-size: 0.76rem;
        }}
        .rq-code-dark .rq-code-notice {{
          border-top-color: #263447;
          color: #aab6c7;
          background: #101827;
        }}
        .rq-code-expanded-fallback .rq-code-notice {{
          display: none;
        }}
        .rq-code-light .rq-syn-heading {{ color: #b91c1c; font-weight: 700; }}
        .rq-code-dark .rq-syn-heading {{ color: #f87171; font-weight: 700; }}
        .rq-code-light .rq-syn-keyword {{ color: #1d4ed8; font-weight: 700; }}
        .rq-code-dark .rq-syn-keyword {{ color: #93c5fd; font-weight: 700; }}
        .rq-code-light .rq-syn-string {{ color: #047857; }}
        .rq-code-dark .rq-syn-string {{ color: #86efac; }}
        .rq-code-light .rq-syn-comment {{ color: #64748b; font-style: italic; }}
        .rq-code-dark .rq-syn-comment {{ color: #94a3b8; font-style: italic; }}
        .rq-code-light .rq-syn-bullet {{ color: #9333ea; }}
        .rq-code-dark .rq-syn-bullet {{ color: #c4b5fd; }}
      </style>
    </head>
    <body>
      <div id="{viewer_id}" class="rq-code-card rq-code-dark">
        <div class="rq-code-label">{escape(title)} | {escape(language_label)}</div>
        <div class="rq-code-actions" aria-label="Code viewer controls">
          <button type="button" class="rq-code-action" data-theme-toggle title="Toggle light or dark code theme">Dark</button>
          <button type="button" class="rq-code-action" data-expand title="Open fullscreen code viewer" aria-label="Open fullscreen code viewer">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 3H3v5"></path><path d="M16 3h5v5"></path><path d="M21 16v5h-5"></path><path d="M3 16v5h5"></path></svg>
          </button>
        </div>
        <pre class="rq-code-body">{compact_html}</pre>
        {notice_html}
      </div>
      <script>
        (() => {{
          const card = document.getElementById({json.dumps(viewer_id)});
          const body = card.querySelector(".rq-code-body");
          const themeButton = card.querySelector("[data-theme-toggle]");
          const expandButton = card.querySelector("[data-expand]");
          const compactHtml = {json_for_inline_script(compact_html)};
          const expandedHtml = {json_for_inline_script(expanded_html)};
          const popupHtml = {json_for_inline_script(popup_html)};

          themeButton.addEventListener("click", () => {{
            const isDark = card.classList.toggle("rq-code-dark");
            card.classList.toggle("rq-code-light", !isDark);
            themeButton.textContent = isDark ? "Dark" : "Light";
          }});

          expandButton.addEventListener("click", () => {{
            const width = window.screen && window.screen.availWidth ? window.screen.availWidth : 1280;
            const height = window.screen && window.screen.availHeight ? window.screen.availHeight : 820;
            const popup = window.open(
              "",
              "_blank",
              `popup=yes,width=${{width}},height=${{height}},left=0,top=0,menubar=no,toolbar=no,location=no,status=no,scrollbars=yes,resizable=yes`
            );
            if (popup) {{
              popup.document.open();
              popup.document.write(popupHtml);
              popup.document.close();
              popup.focus();
            }} else {{
              body.innerHTML = expandedHtml;
              card.classList.add("rq-code-expanded-fallback");
            }}
          }});
        }})();
      </script>
    </body>
  </html>
  """

  components.html(
    html,
    height=min(compact_height + (84 if notice_html else 52), 780),
    scrolling=False,
  )





def main():
  st.set_page_config(
    page_title="RepoQuest",
    layout="wide",
  )
  render_ui_styles()

  # Header
  render_hero()

  # Sidebar
  with st.sidebar:
    workspace = get_workspace()
    
    render_mini_label("Workspace", "overview", "slate")
    if workspace.source_metadata:
      st.success(f"Analyzing: {workspace.source_metadata.source_name}")
      st.caption(f"{workspace.source_metadata.file_count} files scanned")
      
      # Show source type and timestamp
      source_type_label = "Bundled demo" if workspace.source_metadata.source_type == "demo" else "Uploaded ZIP"
      st.caption(f"Source: {source_type_label}")
      
      # Show analysis timestamp
      from datetime import datetime
      try:
        ts = workspace.source_metadata.timestamp
        if isinstance(ts, str):
          ts = datetime.fromisoformat(ts.replace('Z', '+00:00'))
        st.caption(f"Analyzed: {ts.strftime('%Y-%m-%d %H:%M UTC')}")
      except (ValueError, AttributeError):
        pass
      
      # Show AI outputs count if any
      if workspace.assistant_outputs:
        st.caption(f"AI outputs: {len(workspace.assistant_outputs)}")
    else:
      st.info("No repository analyzed yet.")

    st.markdown("---")
    render_mini_label("Input Source", "folder", "blue")
    st.caption("Source controls remain available after analysis. Switch sources or re-analyze anytime.")

    input_mode = st.radio(
      "Choose input:",
      ["Use demo repo", "Upload ZIP"],
      help="Select how to provide the repository"
    )

    uploaded_file = None
    if input_mode == "Upload ZIP":
      st.info(f"Max ZIP size: {MAX_ZIP_SIZE_MB} MB")
      uploaded_file = st.file_uploader(
        "Choose a ZIP file",
        type=["zip"],
        help=f"Upload a repository ZIP file (max {MAX_ZIP_SIZE_MB} MB)"
      )

    generate_disabled = input_mode == "Upload ZIP" and uploaded_file is None

    st.markdown("---")
    
    # AI Assistant status
    ai_status = get_ai_status()
    sidebar_status = format_ai_status_for_sidebar(ai_status)
    render_mini_label("AI Review", "assistant", "purple")
    
    if sidebar_status["type"] == "success":
      st.success(sidebar_status["message"])
    elif sidebar_status["type"] == "warning":
      st.warning(sidebar_status["message"])
    else:
      st.info(sidebar_status["message"])
    
    if sidebar_status.get("caption"):
      st.caption(sidebar_status["caption"])
    
    if ai_status.is_ready:
      st.caption("AI reviews are manual, evidence-cited, and validation-gated.")
    
    # Deployment profile info
    from repoquest.config import get_deployment_profile, get_profile_description
    profile = get_deployment_profile()
    profile_desc = get_profile_description(profile)
    
    with st.expander("Deployment Profile", expanded=False):
      st.caption(f"**{profile}**")
      st.caption(profile_desc)
      
      if profile == "deterministic":
        st.info("✓ No secrets required\n✓ No external calls\n✓ Fully offline")
      elif profile == "mock_assistant":
        st.info("✓ Testing mode\n✓ No network calls\n✓ No API costs")
      elif profile == "cloud_assistant":
        st.warning("⚠ Sends code snippets to Claude API\n⚠ API costs apply")
      elif profile == "local_model":
        st.info("✓ Private/offline AI\n✓ No cloud calls\n⚠ Requires local model server")
      elif profile == "service_assistant":
        st.info("✓ Async processing\n⚠ Requires assistant service")

    # App limits info
    with st.expander("App Limits"):
      limits_df = pd.DataFrame([
        {"Limit": "ZIP size", "Value": f"{MAX_ZIP_SIZE_MB} MB"},
        {"Limit": "Files scanned", "Value": "600"},
        {"Limit": "File size", "Value": "512 KB"},
        {"Limit": "Graph nodes", "Value": "80"},
        {"Limit": "Reading path items", "Value": "9"},
        {"Limit": "Component cards", "Value": "30"},
        {"Limit": "Quiz questions", "Value": "8"},
      ])
      st.dataframe(limits_df, use_container_width=True, hide_index=True)

    render_sidebar_about()

  # Main content area - Generate/Reset buttons
  workspace = get_workspace()
  
  # Show generate/reset controls prominently
  col1, col2 = st.columns(2)

  with col1:
    if st.button(
      "Generate Quest",
      type="primary",
      use_container_width=True,
      disabled=generate_disabled,
      help="Analyze the repository and generate onboarding quest"
    ):
      workspace = get_workspace()
      snapshot = None
      new_source_type = "demo" if input_mode == "Use demo repo" else "upload"

      if input_mode == "Use demo repo":
        with st.spinner("Scanning demo repository..."):
          try:
            snapshot = load_demo_repo()
          except Exception as e:
            st.error(f"Error loading demo repository: {e}")
            return

      elif input_mode == "Upload ZIP" and uploaded_file:
        with st.spinner("Validating and scanning ZIP file..."):
          try:
            # Save uploaded file to temporary location
            with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_file:
              tmp_file.write(uploaded_file.getvalue())
              tmp_path = Path(tmp_file.name)

            try:
              # Scan the ZIP file
              snapshot = scan_zip(tmp_path)
            finally:
              # Clean up temp file
              tmp_path.unlink(missing_ok=True)

          except ZIPSafetyError as e:
            st.error(f"ZIP Safety Error: {e}")
            st.warning("The uploaded ZIP file failed security validation. Please ensure it contains only safe paths and is under the size limit.")
            return
          except Exception as e:
            st.error(f"Error processing ZIP file: {e}")
            import traceback
            with st.expander("Show error details"):
              render_code_viewer(
                traceback.format_exc(),
                "python",
                key="zip_error_traceback",
                title="Error details",
                compact_chars=4_000,
                expanded_chars=MAX_TEXT_PREVIEW_CHARS,
                compact_height=260,
                expanded_height=680,
              )
            return

      # Continue with analysis if we have a snapshot
      if snapshot:
        # Detect source change and handle stale state
        source_changed, new_metadata = detect_source_change(
          workspace.source_metadata,
          snapshot,
          new_source_type,
        )

        if source_changed:
          st.info(f"Source changed. Clearing previous analysis for: {workspace.source_metadata.source_name if workspace.source_metadata else 'unknown'}")
          workspace.clear_analysis()

        # Update workspace with new source
        workspace.source_metadata = new_metadata
        workspace.snapshot = snapshot

        # Save to session state for backward compatibility
        st.session_state["snapshot"] = snapshot
        st.session_state["source_type"] = new_source_type
        st.session_state["source_metadata"] = new_metadata
        try:
          # Generate fingerprint
          with st.spinner("Detecting frameworks and project type..."):
            fingerprint = generate_fingerprint(snapshot)
            workspace.fingerprint = fingerprint
            st.session_state["fingerprint"] = fingerprint

          # Extract routes
          with st.spinner("Extracting API routes..."):
            routes = extract_all_routes(snapshot.files)
            workspace.routes = routes
            st.session_state["routes"] = routes

          # Build import graph
          with st.spinner("Building dependency graph..."):
            edges = build_import_graph(snapshot.files, "")
            workspace.import_edges = edges
            st.session_state["import_edges"] = edges

          # Generate graphs
          with st.spinner("Generating architecture maps..."):
            arch_map = generate_architecture_map(snapshot.files, routes)
            workspace.arch_map = arch_map
            st.session_state["arch_map"] = arch_map

            # Filter out test files from dependency graph
            test_files = get_test_files(snapshot)
            test_paths = {f.path for f in test_files}
            non_test_edges = [e for e in edges if e.source not in test_paths and e.target not in test_paths]
            non_test_files = [f for f in snapshot.files if f.path not in test_paths]

            if non_test_edges:
              dep_graph = generate_dependency_graph(non_test_files, non_test_edges)
            else:
              dep_graph = generate_simple_graph(non_test_files)
            workspace.dep_graph = dep_graph
            st.session_state["dep_graph"] = dep_graph

          # Generate reading path
          with st.spinner("Creating reading path..."):
            reading_path = generate_reading_path(snapshot, fingerprint)
            workspace.reading_path = reading_path
            st.session_state["reading_path"] = reading_path

          # Generate component cards
          with st.spinner("Generating component cards..."):
            component_cards = generate_component_cards(snapshot, fingerprint, routes)
            workspace.component_cards = component_cards
            st.session_state["component_cards"] = component_cards

          # Generate quiz
          with st.spinner("Creating quiz questions..."):
            quiz = generate_quiz(snapshot, fingerprint, routes)
            workspace.quiz = quiz
            st.session_state["quiz"] = quiz

          # Generate work plan
          with st.spinner("Generating work plan and workflows..."):
            work_plan = generate_work_plan(
              snapshot, fingerprint, routes, edges, reading_path, component_cards
            )
            workspace.work_plan = work_plan
            st.session_state["work_plan"] = work_plan

          # Generate test intelligence
          with st.spinner("Analyzing test coverage..."):
            test_intelligence = generate_test_intelligence(
              snapshot, routes, edges, component_cards
            )
            workspace.test_intelligence = test_intelligence
            st.session_state["test_intelligence"] = test_intelligence

          # Run AI Fusion automatically when a configured provider is ready.
          ai_status = get_ai_status()
          workspace.fused_analysis = None
          st.session_state.pop("fused_analysis", None)
          if ai_status.is_ready:
            with st.spinner("Running AI Fusion analyzer..."):
              try:
                fused_analysis = run_ai_fusion(
                  provider=get_assistant_provider(),
                  snapshot=snapshot,
                  fingerprint=fingerprint,
                  routes=routes,
                  import_edges=edges,
                  reading_path=reading_path,
                  component_cards=component_cards,
                  work_plan=work_plan,
                  test_intelligence=test_intelligence,
                  source_id=new_metadata.source_id,
                )
                workspace.fused_analysis = fused_analysis
                st.session_state["fused_analysis"] = fused_analysis
              except Exception as fusion_error:
                st.warning(f"AI Fusion was unavailable: {fusion_error}")

          # Save workspace
          save_workspace(workspace)

          st.success("Onboarding Quest generated successfully!")
          st.rerun()
        except Exception as e:
          st.error(f"Error analyzing repository: {e}")
          import traceback
          with st.expander("Show error details"):
            render_code_viewer(
              traceback.format_exc(),
              "python",
              key="analysis_error_traceback",
              title="Error details",
              compact_chars=4_000,
              expanded_chars=MAX_TEXT_PREVIEW_CHARS,
              compact_height=260,
              expanded_height=680,
            )

  with col2:
    if st.button(
      "Reset",
      use_container_width=True,
      help="Clear current analysis and start fresh"
    ):
      reset_analysis()
      st.rerun()

  st.markdown("---")

  # Main content
  if workspace.has_analysis():
    snapshot = workspace.snapshot
    fingerprint = workspace.fingerprint
    fused_analysis = workspace.fused_analysis
    source_type = workspace.source_metadata.source_type if workspace.source_metadata else "unknown"
    final_project_type = (
      fused_analysis.final_project_type
      if fused_analysis
      else fingerprint.project_type
    )
    final_confidence = (
      fused_analysis.final_confidence
      if fused_analysis
      else fingerprint.confidence
    )
    final_summary = (
      fused_analysis.final_summary
      if fused_analysis
      else fingerprint.summary
    )
    final_entry_points = (
      fused_analysis.final_entry_points
      if fused_analysis
      else fingerprint.entry_points
    )
    display_fingerprint = build_display_fingerprint(fingerprint, fused_analysis)

    # Source info with refresh capability
    st.info(f"📊 **Current Analysis:** {workspace.source_metadata.source_name if workspace.source_metadata else 'Unknown'} ({source_type})")
    
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
      if st.button("🔄 Refresh Analysis", use_container_width=True, help="Re-run analysis on the same source"):
        # Keep source, clear derived analysis
        workspace.clear_analysis()
        workspace.snapshot = snapshot
        save_workspace(workspace)
        st.rerun()
    with col2:
      if st.button("📥 Switch Source", use_container_width=True, help="Go back to source selection"):
        st.info("Use the sidebar to select a new source and click 'Generate Quest'")

    # Create grouped workspace tabs. The legacy sections below are intentionally
    # mapped into fewer top-level groups so the app feels like a focused workbench.
    workspace_tabs = st.tabs([
      "Overview",
      "Architecture",
      "Files",
      "API Routes",
      "Read",
      "Components",
      "Work Plans",
      "Agent Workflows",
      "AI Analyzer",
      "Improve",
      "Export",
    ])
    tabs = [
      workspace_tabs[0], # Overview
      workspace_tabs[1], # Architecture
      workspace_tabs[4], # Reading Path
      workspace_tabs[5], # Components
      workspace_tabs[9], # Tests
      workspace_tabs[6], # Work Plans
      workspace_tabs[9], # Quest & Quiz
      workspace_tabs[10], # Documentation
      workspace_tabs[10], # Export
    ]
    files_tab = workspace_tabs[2]
    routes_tab = workspace_tabs[3]
    workflows_tab = workspace_tabs[7]
    recommendations_tab = workspace_tabs[8]

    # Tab 1: Overview
    with tabs[0]:
      render_section_header(
        "Repository Overview",
        "Project type, framework evidence, entry points, folders, and scan health.",
        "overview",
        "blue",
      )

      if fingerprint:
        reading_path = st.session_state.get("reading_path", [])
        next_read = reading_path[0].path if reading_path else "No reading path generated"
        framework_names = ", ".join(f.name for f in fingerprint.frameworks[:3]) or "No confident framework"
        entry_preview = final_entry_points[0] if final_entry_points else "No entry point detected"

        render_mini_label("Focus Board", "overview", "blue")
        focus_col1, focus_col2, focus_col3, focus_col4 = st.columns(4)
        with focus_col1:
          st.metric("Project", final_project_type)
        with focus_col2:
          st.metric("Confidence", f"{final_confidence * 100:.0f}%")
        with focus_col3:
          st.metric("Frameworks", len(fingerprint.frameworks))
          st.caption(framework_names)
        with focus_col4:
          st.metric("Next Read", "Start here")
          st.caption(next_read)

        with st.container():
          st.markdown(
            f"""
            <div class="rq-focus-panel">
              <h3>Entry point in focus</h3>
              <p>{escape(entry_preview)}</p>
            </div>
            """,
            unsafe_allow_html=True,
          )

        if "arch_map" in st.session_state:
          with st.expander("Architecture preview", expanded=True):
            try:
              st.graphviz_chart(st.session_state["arch_map"], use_container_width=False)
            except Exception:
              st.caption("Architecture preview is available in the Map workspace.")

        # Project type and confidence
        col1, col2 = st.columns([2, 1])
        with col1:
          render_mini_label("Analyzer Mode", "assistant", "purple")
          if fused_analysis and fused_analysis.is_ai_enhanced:
            st.markdown("**AI-first hybrid**")
            st.caption(f"Final answer: {fused_analysis.mode.replace('-', ' ')}")
          else:
            st.markdown("**Deterministic**")
            st.caption("AI Fusion is not active for this workspace.")

          render_mini_label("Project Type", "overview", "blue")
          st.markdown(f"**{final_project_type}**")
          st.markdown(final_summary)
        with col2:
          st.metric("Confidence", f"{final_confidence * 100:.0f}%")

        if fused_analysis and fused_analysis.report:
          report = fused_analysis.report
          with st.expander("Why AI changed or confirmed this", expanded=bool(fused_analysis.applied_overrides)):
            st.markdown(report.summary or "AI Fusion completed without a summary.")
            if fused_analysis.applied_overrides:
              override_rows = [
                {
                  "Target": override.target,
                  "Original": str(override.original_value),
                  "AI Proposal": str(override.proposed_value),
                  "Confidence": f"{override.confidence:.0%}",
                  "Why": override.rationale,
                }
                for override in fused_analysis.applied_overrides
              ]
              st.dataframe(pd.DataFrame(override_rows), use_container_width=True, hide_index=True)
            if report.warnings:
              for warning in report.warnings:
                st.warning(warning)
            st.markdown("**Deterministic audit trail**")
            st.markdown(f"Original project type: `{fingerprint.project_type}`")
            st.markdown(f"Original confidence: `{fingerprint.confidence:.0%}`")
            st.markdown(fingerprint.summary)

        # Frameworks
        if fingerprint.frameworks:
          render_mini_label("Detected Frameworks", "shield", "blue")

          for framework in fingerprint.frameworks:
            with st.expander(f"**{framework.name}** ({framework.category}) - {framework.confidence * 100:.0f}% confidence"):
              # Create evidence table
              evidence_data = []
              for evidence_item in framework.evidence:
                source, signal = split_evidence(evidence_item)

                evidence_data.append({
                  "Evidence": signal,
                  "Source": source
                })

              if evidence_data:
                evidence_df = pd.DataFrame(evidence_data)
                st.dataframe(evidence_df, use_container_width=True, hide_index=True)

        # Entry points
        if final_entry_points:
          render_mini_label("Entry Points", "route", "green")

          # Build entry points table with type and reason
          entry_data = []
          for entry_point in final_entry_points:
            # Determine type and reason based on path
            file_info = next((f for f in snapshot.files if f.path == entry_point), None)

            if file_info:
              if file_info.role == "entrypoint":
                if "backend" in entry_point.lower() or entry_point.endswith("main.py"):
                  entry_type = "Backend entry"
                  reason = "Application initialization and configuration"
                elif "frontend" in entry_point.lower() or "App.tsx" in entry_point or "App.jsx" in entry_point:
                  entry_type = "Frontend app shell"
                  reason = "Main React component"
                elif "main.tsx" in entry_point or "main.jsx" in entry_point or "index.tsx" in entry_point:
                  entry_type = "Frontend entry"
                  reason = "React/Vite render entry point"
                else:
                  entry_type = "Entry point"
                  reason = "Application startup"
              else:
                entry_type = file_info.role.replace("_", " ").title()
                reason = "Detected as entry point"
            else:
              entry_type = "Entry point"
              reason = "Application startup"

            entry_data.append({
              "File": entry_point,
              "Type": entry_type,
              "Why Selected": reason
            })

          entry_df = pd.DataFrame(entry_data)
          st.dataframe(entry_df, use_container_width=True, hide_index=True)

        # Key folders
        if fingerprint.key_folders:
          render_mini_label("Key Folders", "folder", "orange")

          # Build key folders table
          folder_data = []
          for folder in fingerprint.key_folders:
            # Clean folder path (remove trailing slash if present)
            clean_folder = folder.rstrip("/")

            # Determine purpose based on folder name
            folder_lower = clean_folder.lower()
            if "backend" in folder_lower:
              purpose = "Backend code"
            elif "frontend" in folder_lower:
              purpose = "Frontend code"
            elif "component" in folder_lower:
              purpose = "UI components"
            elif "page" in folder_lower:
              purpose = "Application pages"
            elif "route" in folder_lower:
              purpose = "API routes"
            elif "service" in folder_lower:
              purpose = "Business logic"
            elif "model" in folder_lower:
              purpose = "Data models"
            elif "test" in folder_lower:
              purpose = "Test files"
            elif "src" in folder_lower:
              purpose = "Source code"
            elif "api" in folder_lower:
              purpose = "API client"
            else:
              purpose = "Project files"

            folder_data.append({
              "Folder": clean_folder,
              "Purpose": purpose
            })

          folder_df = pd.DataFrame(folder_data)
          st.dataframe(folder_df, use_container_width=True, hide_index=True)

        # Warnings
        if fingerprint.warnings:
          render_mini_label("Warnings", "warning", "red")
          for warning in fingerprint.warnings:
            st.warning(warning)

      # Summary metrics
      render_mini_label("Scan Summary", "overview", "slate")
      col1, col2, col3 = st.columns(3)
      with col1:
        st.metric("Total Files Seen", snapshot.total_files_seen)
      with col2:
        st.metric("Files Scanned", snapshot.total_files_scanned)
      with col3:
        scanned_files = [f for f in snapshot.files if not f.skipped]
        st.metric("Analyzed Files", len(scanned_files))

      # AI Review section
      st.markdown("---")
      render_mini_label("AI Review", "assistant", "purple")

      ai_status = get_ai_status()
      if ai_status.is_ready and fingerprint:
        st.caption("Adds an evidence-cited review on top of the deterministic overview.")
        if st.button("Generate Overview Review", key="ai_overview"):
          def build_request():
            return build_overview_context(snapshot, fingerprint) # type: ignore
          result = run_assistant("overview", "Repository Overview", build_request, snapshot)

        # Display result if exists
        if "assistant_outputs" in st.session_state and "overview" in st.session_state["assistant_outputs"]:
          result = st.session_state["assistant_outputs"]["overview"]
          render_assistant_result(result, "AI-assisted overview")
      else:
        st.caption("AI review is disabled for this workspace. Deterministic findings are complete and usable.")

    # Tab 2: Architecture Map
    with tabs[1]:
      render_section_header(
        "Architecture Map",
        "Conceptual system overview plus interactive application dependency graph.",
        "architecture",
        "purple",
      )

      render_mini_label("System Overview", "architecture", "purple")
      conceptual_dot = build_conceptual_architecture_dot(
        snapshot,
        st.session_state.get("fingerprint"),
        st.session_state.get("routes", []),
      )
      st.graphviz_chart(conceptual_dot, use_container_width=False)

      layer_rows = [
        {"Layer": "Docs / README", "Meaning": "Contributor-facing starting context"},
        {"Layer": "Frontend App", "Meaning": "Browser UI, pages, components, and API client when detected"},
        {"Layer": "API Routes / Gateway", "Meaning": "Detected HTTP route boundary"},
        {"Layer": "Services / Business Logic", "Meaning": "Backend service modules and orchestration"},
        {"Layer": "Models / Storage Boundary", "Meaning": "Schemas, models, data files, or storage-facing code when detected"},
        {"Layer": "Test Suite", "Meaning": "Validation surface shown separately from production graph"},
      ]
      with st.expander("Layer definitions", expanded=False):
        st.dataframe(pd.DataFrame(layer_rows), use_container_width=True, hide_index=True)

      if fused_analysis and fused_analysis.report and fused_analysis.report.architecture_summary:
        render_mini_label("AI Fusion Architecture Summary", "assistant", "purple")
        st.info(fused_analysis.report.architecture_summary)
        with st.expander("Architecture audit trail", expanded=False):
          st.caption("The graphs below remain generated from deterministic routes, imports, and file roles.")

      if "import_edges" in st.session_state and "snapshot" in st.session_state:
        edges = st.session_state["import_edges"]

        # Compact graph controls
        with st.expander("Graph Controls", expanded=False):
          col1, col2 = st.columns([2, 1])

          with col1:
            view_mode = st.selectbox(
              "View Mode",
              options=["application", "tests", "all_debug"],
              index=0,
              help="application: production code only | tests: test files and coverage | all_debug: everything including test edges",
              format_func=lambda x: {
                "application": "Application (default)",
                "tests": "Tests & Coverage",
                "all_debug": "All Files (debug)"
              }[x]
            )

          with col2:
            max_nodes = st.number_input(
              "Max Nodes",
              min_value=10,
              max_value=150,
              value=80,
              step=10,
              help="Maximum number of nodes to display"
            )

        graph_data = build_graph_data(
          files=snapshot.files,
          edges=edges,
          routes=st.session_state.get("routes", []),
          view_mode=view_mode, # type: ignore
          role_filter=None,
          max_nodes=int(max_nodes),
        )

        # Application Graph section
        render_mini_label("Application Graph", "architecture", "purple")
        st.caption(f"Showing {len(graph_data.nodes)} nodes and {len(graph_data.edges)} edges in **{view_mode}** mode")

        # Render graph in full width
        if graph_data.nodes:
          dot_string = graph_data_to_dot(graph_data)
          try:
            st.graphviz_chart(dot_string, use_container_width=False)
          except Exception as e:
            st.error(f"Error rendering graph: {e}")
            # Show DOT source for debugging
            with st.expander("Graph DOT Source (for debugging)", expanded=False):
              render_code_viewer(
                dot_string,
                "dot",
                key="graph_dot_source",
                title="Graph DOT source",
                compact_chars=4_000,
                expanded_chars=MAX_TEXT_PREVIEW_CHARS,
                compact_height=300,
                expanded_height=680,
              )
        else:
          st.warning("No connected files were found for this graph view. Try another view mode.")

        # Node inspection panel
        st.markdown("---")
        render_mini_label("Inspect File or Component", "components", "orange")

        if graph_data.nodes:
          # Create selectbox with node paths
          node_options = {node.path: f"{node.label} ({node.role})" for node in graph_data.nodes}

          selected_node_path = st.selectbox(
            "Select a file to inspect:",
            options=list(node_options.keys()),
            format_func=lambda x: node_options[x],
            help="Choose a file to see detailed information"
          )

          if selected_node_path:
            # Get node details
            routes = st.session_state.get("routes", [])
            node_details = get_node_details(
              node_path=selected_node_path,
              files=snapshot.files,
              edges=edges,
              routes=routes,
            )

            if node_details and "file_info" in node_details:
              file_info = node_details["file_info"]

              render_metadata_chips([
                ("Role", file_info.role.replace("_", " ").title()),
                ("Language", file_info.language),
                ("Lines", file_info.line_count),
                ("Size", format_file_size(file_info.size_bytes)),
              ])

              # Why it matters
              render_mini_label("Why this file matters", "file", tone_for_role(file_info.role))
              if file_info.role == "entrypoint":
                st.markdown("This is an application entry point where the app initializes.")
              elif file_info.role == "backend_route":
                st.markdown("This file defines API endpoints that the frontend calls.")
              elif file_info.role == "frontend_page":
                st.markdown("This is a main page component in the frontend application.")
              elif file_info.role == "frontend_component":
                st.markdown("This is a reusable UI component.")
              elif file_info.role == "api_client":
                st.markdown("This file handles communication between frontend and backend.")
              elif file_info.role == "backend_service":
                st.markdown("This contains business logic and data processing.")
              elif file_info.role == "model":
                st.markdown("This defines data structures and schemas.")
              elif file_info.role == "test":
                st.markdown("This is a test file that validates application behavior.")
              else:
                st.markdown(f"This file plays a {file_info.role} role in the application.")

              # Dependencies
              col1, col2 = st.columns(2)

              with col1:
                render_mini_label("Incoming Dependencies", "architecture", "blue")
                if node_details["incoming_deps"]:
                  incoming_data = []
                  for dep in node_details["incoming_deps"][:5]:
                    dep_file = next((f for f in snapshot.files if f.path == dep), None)
                    if dep_file:
                      incoming_data.append({
                        "File": dep_file.name,
                        "Role": dep_file.role.replace("_", " ").title()
                      })
                  if incoming_data:
                    incoming_df = pd.DataFrame(incoming_data)
                    st.dataframe(incoming_df, use_container_width=True, hide_index=True)
                  if len(node_details["incoming_deps"]) > 5:
                    st.caption(f"*...and {len(node_details['incoming_deps']) - 5} more*")
                else:
                  st.caption("*No incoming dependencies detected*")

              with col2:
                render_mini_label("Outgoing Dependencies", "architecture", "purple")
                if node_details["outgoing_deps"]:
                  outgoing_data = []
                  for dep in node_details["outgoing_deps"][:5]:
                    dep_file = next((f for f in snapshot.files if f.path == dep), None)
                    if dep_file:
                      outgoing_data.append({
                        "File": dep_file.name,
                        "Role": dep_file.role.replace("_", " ").title()
                      })
                  if outgoing_data:
                    outgoing_df = pd.DataFrame(outgoing_data)
                    st.dataframe(outgoing_df, use_container_width=True, hide_index=True)
                  if len(node_details["outgoing_deps"]) > 5:
                    st.caption(f"*...and {len(node_details['outgoing_deps']) - 5} more*")
                else:
                  st.caption("*No outgoing dependencies detected*")

              # Related routes
              if node_details["related_routes"]:
                render_mini_label("API Routes defined in this file", "route", "orange")
                routes_data = []
                for route in node_details["related_routes"]:
                  routes_data.append({
                    "Method": route.method,
                    "Path": route.path,
                    "Function": route.function_name or "N/A"
                  })
                routes_df = pd.DataFrame(routes_data)
                st.dataframe(routes_df, use_container_width=True, hide_index=True)

              # Related tests
              if node_details["related_tests"]:
                render_mini_label("Related Test Files", "tests", "purple")
                tests_data = []
                for test_path in node_details["related_tests"]:
                  test_file = next((f for f in snapshot.files if f.path == test_path), None)
                  if test_file:
                    tests_data.append({
                      "File": test_file.name,
                      "Role": test_file.role.replace("_", " ").title()
                    })
                if tests_data:
                  tests_df = pd.DataFrame(tests_data)
                  st.dataframe(tests_df, use_container_width=True, hide_index=True)

              # AI Review
              st.markdown("---")
              render_mini_label("AI Review", "assistant", "purple")

              ai_status = get_ai_status()
              if ai_status.is_ready:
                if st.button(f"Review {file_info.name}", key=f"ai_file_{selected_node_path}"):
                  routes = st.session_state.get("routes", [])
                  def build_request():
                    return build_file_context(file_info, snapshot, routes) # type: ignore
                  result = run_assistant(f"file_{selected_node_path}", f"File: {file_info.name}", build_request, snapshot)

                # Display result if exists
                section_key = f"file_{selected_node_path}"
                if "assistant_outputs" in st.session_state and section_key in st.session_state["assistant_outputs"]:
                  result = st.session_state["assistant_outputs"][section_key]
                  render_assistant_result(result, "AI-assisted file review")
              else:
                tab_caption = format_ai_status_for_tab(ai_status)
                if tab_caption:
                  st.caption(tab_caption)

        else:
          st.info("Select a file from the graph above to see detailed information.")

      else:
        st.info("Architecture map will appear here after generating the quest.")

      # Detected Routes
      if False and "routes" in st.session_state:
        routes = st.session_state["routes"]

        if routes:
          st.markdown("---")
          render_mini_label("Detected API Routes", "route", "orange")

          st.markdown(f"Found **{len(routes)}** API endpoints:")

          # Group routes: feature routes first, then utility routes
          feature_routes = []
          utility_routes = []

          for route in routes:
            if route.path in ["/", "/health", "/healthz", "/ping", "/status"]:
              utility_routes.append(route)
            else:
              feature_routes.append(route)

          sorted_routes = feature_routes + utility_routes

          routes_data = []
          for route in sorted_routes:
            routes_data.append({
              "Method": route.method,
              "Path": route.path,
              "File": route.file_path,
              "Function": route.function_name or "N/A",
              "Framework": route.framework.upper()
            })

          routes_df = pd.DataFrame(routes_data)
          st.dataframe(
            routes_df,
            use_container_width=True,
            height=min(400, len(routes) * 35 + 38)
          )

    # File explorer workspace
    with files_tab:
      render_section_header(
        "File Explorer",
        "Browse the scanned repo structure and inspect one file at a time.",
        "folder",
        "blue",
      )

      active_files = [file for file in snapshot.files if not file.skipped]
      col_tree, col_file = st.columns([1, 2])

      with col_tree:
        render_mini_label("Repository Tree", "folder", "blue")
        tree_text = build_file_tree_text(snapshot.files)
        render_code_viewer(
          tree_text or "No files scanned.",
          "text",
          key="repository_tree",
          title="Repository tree",
          compact_chars=12_000,
          expanded_chars=20_000,
          compact_height=520,
          expanded_height=760,
        )

      with col_file:
        render_mini_label("Open File", "file", "orange")
        role_filter_options = ["All"] + sorted({file.role for file in active_files})
        selected_file_role = st.selectbox("Role filter:", role_filter_options, key="file_explorer_role")
        filtered_files = active_files
        if selected_file_role != "All":
          filtered_files = [file for file in active_files if file.role == selected_file_role]

        if filtered_files:
          selected_file_path = st.selectbox(
            "File:",
            [file.path for file in filtered_files],
            key="file_explorer_selected_path",
          )
          selected_file = next(file for file in filtered_files if file.path == selected_file_path)
          render_file_analysis_panel(
            selected_file,
            snapshot,
            st.session_state.get("import_edges", []),
            st.session_state.get("routes", []),
            "file_explorer",
          )
        else:
          st.warning("No files match that role filter.")

    # API route workspace
    with routes_tab:
      render_section_header(
        "API Routes",
        "Detected HTTP endpoints with linked files and focused route analysis.",
        "route",
        "orange",
      )

      routes = st.session_state.get("routes", [])
      if routes:
        route_options = {
          idx: f"{route.method} {route.path} - {route.file_path}"
          for idx, route in enumerate(routes)
        }
        selected_route_idx = st.selectbox(
          "Choose one route:",
          list(route_options.keys()),
          format_func=lambda idx: route_options[idx],
          key="selected_api_route",
        )
        route = routes[selected_route_idx]

        render_metadata_chips([
          ("Method", route.method),
          ("Path", route.path),
          ("Framework", route.framework.upper()),
          ("Function", route.function_name or "N/A"),
        ])
        st.markdown(f"**Route file:** `{route.file_path}`")

        route_file = next((file for file in snapshot.files if file.path == route.file_path), None)
        if route_file:
          render_file_analysis_panel(
            route_file,
            snapshot,
            st.session_state.get("import_edges", []),
            routes,
            "api_route_file",
          )

        with st.expander("All detected routes", expanded=False):
          routes_df = pd.DataFrame([
            {
              "Method": item.method,
              "Path": item.path,
              "File": item.file_path,
              "Function": item.function_name or "N/A",
              "Framework": item.framework.upper(),
            }
            for item in routes
          ])
          st.dataframe(routes_df, use_container_width=True, hide_index=True)
      else:
        st.info("No API routes were detected in this repository.")

    # Tab 3: Reading Path
    with tabs[2]:
      render_section_header(
        "Reading & Evidence Workbench",
        "A guided file sequence with previews, role context, improvement ideas, and AI review.",
        "reading",
        "green",
      )

      if "reading_path" in st.session_state:
        reading_path = st.session_state["reading_path"]

        if reading_path:
          total_minutes = sum(item.estimated_minutes for item in reading_path)

          st.info(f"Suggested reading path with {len(reading_path)} files (~{total_minutes} minutes). Code previews are buffered and scroll inside each reader.")

          reading_options = {
            idx: f"{item.order}. {item.path} ({item.estimated_minutes} min)"
            for idx, item in enumerate(reading_path)
          }
          selected_reading_idx = st.selectbox(
            "Choose one file to read:",
            options=list(reading_options.keys()),
            format_func=lambda idx: reading_options[idx],
            key="selected_reading_item",
          )

          item = reading_path[selected_reading_idx]
          file_info = next((f for f in snapshot.files if f.path == item.path), None)

          if file_info:
            render_metadata_chips([
              ("Step", item.order),
              ("Role", file_info.role.replace("_", " ").title()),
              ("Language", file_info.language),
              ("Time", f"{item.estimated_minutes} min"),
            ])

            render_mini_label("Why read this", "reading", "green")
            st.markdown(item.reason)
            if (
                fused_analysis
                and fused_analysis.report
                and item.path in fused_analysis.report.reading_path_notes
            ):
              render_mini_label("AI Fusion Note", "assistant", "purple")
              st.info(fused_analysis.report.reading_path_notes[item.path])
              with st.expander("Reading path audit trail", expanded=False):
                st.markdown(f"Deterministic reason: {item.reason}")

            if file_info.text_preview and not file_info.skipped:
              render_mini_label("Read", "file", tone_for_role(file_info.role))
              is_truncated = (
                len(file_info.text_preview) >= MAX_TEXT_PREVIEW_CHARS or
                file_info.size_bytes > len(file_info.text_preview.encode("utf-8"))
              )
              render_code_viewer(
                file_info.text_preview,
                get_language_for_st_code(file_info),
                key=f"reading_{item.order}_{file_info.path}",
                title=file_info.path,
              )
              if is_truncated:
                st.caption(f"Preview is partial - file has {file_info.line_count} lines ({file_info.size_bytes:,} bytes)")

            col_understand, col_improve = st.columns(2)
            with col_understand:
              render_mini_label("Understand", "overview", "blue")
              understand_df = pd.DataFrame({"Focus": get_understand_points(file_info)})
              st.dataframe(understand_df, use_container_width=True, hide_index=True)
            with col_improve:
              render_mini_label("Improve", "workplans", "orange")
              improvement_df = pd.DataFrame({"Idea": get_improvement_ideas(file_info)})
              st.dataframe(improvement_df, use_container_width=True, hide_index=True)

            render_mini_label("AI Review", "assistant", "purple")
            ai_status = get_ai_status()
            if ai_status.is_ready:
              if st.button(f"Review {file_info.name}", key=f"ai_reading_{item.order}_{file_info.path}"):
                routes = st.session_state.get("routes", [])
                def build_request():
                  return build_file_context(file_info, snapshot, routes) # type: ignore
                result = run_assistant(f"reading_{file_info.path}", f"Reading: {file_info.name}", build_request, snapshot)

              section_key = f"reading_{file_info.path}"
              if "assistant_outputs" in st.session_state and section_key in st.session_state["assistant_outputs"]:
                result = st.session_state["assistant_outputs"][section_key]
                render_assistant_result(result, "AI-assisted file review")
            else:
              tab_caption = format_ai_status_for_tab(ai_status)
              if tab_caption:
                st.caption(tab_caption)

        else:
          st.warning("No reading path generated")
      else:
        st.info("Generate an onboarding quest to see the reading workbench.")
        reading_features_df = pd.DataFrame([
          {"Section": "Read", "Purpose": "Syntax-highlighted code previews"},
          {"Section": "Understand", "Purpose": "What to look for in each file"},
          {"Section": "Improve", "Purpose": "Concrete improvement suggestions"},
          {"Section": "AI Review", "Purpose": "Optional evidence-cited reviewer notes"},
        ])
        st.dataframe(reading_features_df, use_container_width=True, hide_index=True)

    # Tab 4: Components
    with tabs[3]:
      render_section_header(
        "Component Cards",
        "Important files grouped by role with evidence, connections, test ideas, and next actions.",
        "components",
        "orange",
      )

      if "component_cards" in st.session_state:
        component_cards = st.session_state["component_cards"]

        if component_cards:
          st.info(f" {len(component_cards)} important components identified")

          # Filter by role
          all_roles = sorted(set(card.role for card in component_cards))
          selected_role = st.selectbox(
            "Filter by role:",
            ["All"] + all_roles,
            index=0
          )

          filtered_cards = component_cards
          if selected_role != "All":
            filtered_cards = [c for c in component_cards if c.role == selected_role]

          if filtered_cards:
            selected_card_idx = st.selectbox(
              "Choose one component:",
              range(len(filtered_cards)),
              format_func=lambda idx: f"{filtered_cards[idx].title} - {filtered_cards[idx].path}",
              key=f"selected_component_{selected_role}",
            )
            card = filtered_cards[selected_card_idx]

            render_component_intro(
              card.role,
              card.path,
              card.why_it_matters,
              tone_for_role(card.role),
            )
            if (
                fused_analysis
                and fused_analysis.report
                and card.path in fused_analysis.report.component_notes
            ):
              render_mini_label("AI Fusion Note", "assistant", "purple")
              st.info(fused_analysis.report.component_notes[card.path])
              with st.expander("Component audit trail", expanded=False):
                st.markdown(f"Deterministic note: {card.why_it_matters}")

            if card.detected_items:
              render_mini_label("Detected Evidence", "shield", "blue")
              evidence_df = pd.DataFrame({"Evidence": card.detected_items})
              st.dataframe(evidence_df, use_container_width=True, hide_index=True)

              with st.expander("Code evidence", expanded=False):
                file_info = next((f for f in snapshot.files if f.path == card.path), None)
                if file_info and file_info.text_preview:
                  first_item = card.detected_items[0]
                  pattern = first_item.split("(")[0] if "(" in first_item else first_item
                  snippet = extract_code_snippet(file_info, pattern)
                  if snippet:
                    render_code_viewer(
                      snippet,
                      get_language_for_st_code(file_info),
                      key=f"component_snippet_{card.path}",
                      title=card.path,
                      compact_chars=2_000,
                      expanded_chars=6_000,
                      compact_height=240,
                      expanded_height=520,
                    )
                  else:
                    st.caption("No compact snippet matched the detected evidence.")

            col_connections, col_tests = st.columns(2)
            with col_connections:
              render_mini_label("Connected Files", "architecture", "purple")
              if card.connected_to:
                connected_df = pd.DataFrame({"File": card.connected_to})
                st.dataframe(connected_df, use_container_width=True, hide_index=True)
              else:
                st.caption("No direct connections detected.")
            with col_tests:
              render_mini_label("Suggested Test Ideas", "tests", "purple")
              if card.suggested_test_ideas:
                test_df = pd.DataFrame({"Idea": card.suggested_test_ideas})
                st.dataframe(test_df, use_container_width=True, hide_index=True)
              else:
                st.caption("No test ideas generated for this card.")

            render_mini_label("AI Review", "assistant", "purple")
            ai_status = get_ai_status()
            if ai_status.is_ready:
              if st.button("Review risks and tests", key=f"ai_component_{card.path}"):
                def build_request():
                  return build_component_context(card, snapshot)
                result = run_assistant(f"component_{card.path}", f"Component: {card.title}", build_request, snapshot)

              section_key = f"component_{card.path}"
              if "assistant_outputs" in st.session_state and section_key in st.session_state["assistant_outputs"]:
                result = st.session_state["assistant_outputs"][section_key]
                render_assistant_result(result, "AI-assisted component review")
            else:
              tab_caption = format_ai_status_for_tab(ai_status)
              if tab_caption:
                st.caption(tab_caption)

          else:
            st.warning("No component cards match the selected role")
        else:
          st.warning("No component cards generated")
      else:
        st.info("Generate an onboarding quest to see component cards.")
        component_features_df = pd.DataFrame([
          {"Card Area": "Role", "Purpose": "Shows what the file appears to do"},
          {"Card Area": "Connections", "Purpose": "Shows related imports and linked files"},
          {"Card Area": "Evidence", "Purpose": "Shows deterministic signals found in the file"},
          {"Card Area": "Suggested tests", "Purpose": "Offers next checks based on the file role"},
        ])
        st.dataframe(component_features_df, use_container_width=True, hide_index=True)

    # Tab 5: Tests
    with tabs[4]:
      render_section_header(
        "Test Intelligence",
        "Test inventory, impact mapping, coverage gaps, quality signals, and suggested next tests.",
        "tests",
        "purple",
      )

      if "test_intelligence" in st.session_state:
        test_intel = st.session_state["test_intelligence"]

        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
          st.metric("Test Files", len(test_intel.test_insights))
        with col2:
          total_targets = sum(len(t.likely_targets) for t in test_intel.test_insights)
          st.metric("Targets Covered", total_targets)
        with col3:
          total_routes = sum(len(t.covered_routes) for t in test_intel.test_insights)
          st.metric("Routes Tested", total_routes)
        with col4:
          st.metric("Missing Coverage", len(test_intel.missing_coverage))

        st.markdown("---")

        # Test Inventory
        render_mini_label("Test Inventory", "tests", "purple")

        if test_intel.test_insights:
          inventory_data = []
          for insight in test_intel.test_insights:
            inventory_data.append({
              "Test File": insight.test_file,
              "Framework": insight.framework or "unknown",
              "Targets": len(insight.likely_targets),
              "Routes": len(insight.covered_routes),
              "Assertions": insight.quality_signals.get("assertion_count", 0),
            })

          inventory_df = pd.DataFrame(inventory_data)
          st.dataframe(inventory_df, use_container_width=True, hide_index=True)
        else:
          st.info("No test files detected in this repository.")

        st.markdown("---")

        # Impact Table
        render_mini_label("Test Impact Map", "architecture", "blue")
        st.caption("Shows which test files likely cover which application files")

        if test_intel.test_insights:
          impact_data = []
          for insight in test_intel.test_insights:
            if insight.likely_targets:
              for target in insight.likely_targets[:5]: # Limit to top 5 per test
                impact_data.append({
                  "Test File": insight.test_file,
                  "Likely Covers": target,
                  "Routes Tested": ", ".join(insight.covered_routes[:3]) if insight.covered_routes else "None",
                })

          if impact_data:
            impact_df = pd.DataFrame(impact_data)
            st.dataframe(impact_df, use_container_width=True, hide_index=True)
          else:
            st.info("Could not infer test-to-target mappings from available evidence.")
        else:
          st.info("No test impact data available.")

        st.markdown("---")

        # Missing Coverage
        render_mini_label("Missing Coverage", "warning", "red")
        st.caption("Application files and routes that appear untested")

        if test_intel.missing_coverage:
          missing_data = []
          for item in test_intel.missing_coverage[:20]: # Limit display
            missing_data.append({
              "Untested Item": item,
              "Type": "Route" if item.startswith(("GET ", "POST ", "PUT ", "DELETE ", "PATCH ")) else "File",
            })

          missing_df = pd.DataFrame(missing_data)
          st.dataframe(missing_df, use_container_width=True, hide_index=True)
        else:
          st.success("No obvious coverage gaps detected!")

        st.markdown("---")

        # Quality Signals
        render_mini_label("Test Quality Signals", "shield", "green")

        if test_intel.test_insights:
          quality_data = []
          for insight in test_intel.test_insights:
            signals = insight.quality_signals
            quality_data.append({
              "Test File": insight.test_file,
              "Assertions": signals.get("assertion_count", 0),
              "Fixtures": "Yes" if signals.get("has_fixtures") else "None",
              "Mocks": "Yes" if signals.get("has_mocks") else "None",
              "TestClient": "Yes" if signals.get("has_test_client") else "None",
              "Skipped": signals.get("skipped_count", 0),
            })

          quality_df = pd.DataFrame(quality_data)
          st.dataframe(quality_df, use_container_width=True, hide_index=True)

        st.markdown("---")

        # Suggested Next Tests
        render_mini_label("Suggested Next Tests", "workplans", "orange")
        st.caption("Concrete test cases to add based on detected evidence")

        if test_intel.suggested_tests:
          suggested_data = []
          for suggestion in test_intel.suggested_tests[:15]: # Limit display
            suggested_data.append({
              "Suggested Test": suggestion,
            })

          suggested_df = pd.DataFrame(suggested_data)
          st.dataframe(suggested_df, use_container_width=True, hide_index=True)
        else:
          st.info("No specific test suggestions generated.")

        st.markdown("---")

        # AI Test Review
        render_mini_label("AI Test Review", "assistant", "purple")
        st.caption("Evidence-cited AI review of the deterministic test intelligence.")

        ai_status = get_ai_status()
        if ai_status.is_ready:
          if st.button("Generate Test Review", key="ai_test_plan"):
            def build_request():
              return build_test_context(test_intel, snapshot)
            result = run_assistant("test_plan", "Test Intelligence", build_request, snapshot)

          # Display result if exists
          if "assistant_outputs" in st.session_state and "test_plan" in st.session_state["assistant_outputs"]:
            result = st.session_state["assistant_outputs"]["test_plan"]
            render_assistant_result(result, "AI-assisted test review")
        else:
          tab_caption = format_ai_status_for_tab(ai_status)
          if tab_caption:
            st.caption(tab_caption)

      else:
        st.info("Generate an onboarding quest to see test intelligence.")
        test_features_df = pd.DataFrame([
          {"Section": "Test Inventory", "Purpose": "What test files exist and their frameworks"},
          {"Section": "Impact Map", "Purpose": "Which tests likely cover which application files"},
          {"Section": "Missing Coverage", "Purpose": "Routes and components that appear untested"},
          {"Section": "Quality Signals", "Purpose": "Assertions, fixtures, mocks, and test patterns"},
          {"Section": "Suggested Tests", "Purpose": "Concrete next test cases to add"},
          {"Section": "AI Test Review", "Purpose": "Optional evidence-cited coverage review"},
        ])
        st.dataframe(test_features_df, use_container_width=True, hide_index=True)

    # Tab 6: Work Plans
    with tabs[5]:
      render_section_header(
        "Work Plans",
        "Evidence-backed epics, tasks, and milestones for follow-up development.",
        "workplans",
        "slate",
      )

      if "work_plan" in st.session_state:
        work_plan = st.session_state["work_plan"]

        # Summary metrics
        col1, col2, col3 = st.columns(3)
        with col1:
          st.metric("Epics", len(work_plan.epics))
        with col2:
          st.metric("Tasks", len(work_plan.tasks))
        with col3:
          st.metric("Milestones", len(work_plan.milestones))

        if fused_analysis and fused_analysis.report:
          report = fused_analysis.report
          if report.risks or report.recommendations:
            render_mini_label("AI Fusion Priorities", "assistant", "purple")
            if report.risks:
              st.dataframe(
                pd.DataFrame({"Risk": report.risks}),
                use_container_width=True,
                hide_index=True,
              )
            if report.recommendations:
              st.dataframe(
                pd.DataFrame({"Recommendation": report.recommendations}),
                use_container_width=True,
                hide_index=True,
              )
            with st.expander("Work plan audit trail", expanded=False):
              st.caption("The task list below is generated from deterministic RepoQuest evidence.")

        st.markdown("---")

        # Suggested Milestones
        render_mini_label("Suggested Milestones", "workplans", "slate")

        for milestone in work_plan.milestones:
          with st.expander(f"**{milestone.title}** ({len(milestone.tasks)} tasks)", expanded=False):
            st.markdown(f"**Goal:** {milestone.goal}")
            st.markdown("")

            # Tasks in this milestone
            for task in milestone.tasks:
              st.markdown(f"**[{task.priority.upper()}]** {task.why}")

        st.markdown("---")

        # Tasks Table
        render_mini_label("All Tasks", "overview", "blue")

        task_data = []
        for task in work_plan.tasks:
          task_data.append({
            "Epic": task.epic,
            "Priority": task.priority.upper(),
            "Description": task.why[:80] + "..." if len(task.why) > 80 else task.why,
            "Files": len(task.files),
          })

        task_df = pd.DataFrame(task_data)
        st.dataframe(task_df, use_container_width=True, hide_index=True)

        # Task details
        render_mini_label("Task Details", "file", "orange")
        selected_task_idx = st.selectbox(
          "Select a task to view details:",
          range(len(work_plan.tasks)),
          format_func=lambda i: f"{work_plan.tasks[i].epic}: {work_plan.tasks[i].why[:60]}..."
        )

        if selected_task_idx is not None:
          task = work_plan.tasks[selected_task_idx]

          with st.container():
            st.markdown(f"**Epic:** {task.epic}")
            st.markdown(f"**Priority:** {task.priority.upper()}")
            st.markdown(f"**Why it matters:** {task.why}")
            st.markdown("")

            render_mini_label("Files involved", "file", "blue")
            files_df = pd.DataFrame({"File": task.files[:10]})
            st.dataframe(files_df, use_container_width=True, hide_index=True)

            st.markdown("")
            render_mini_label("Evidence", "shield", "green")
            evidence_df = pd.DataFrame({"Evidence": task.evidence})
            st.dataframe(evidence_df, use_container_width=True, hide_index=True)

            st.markdown("")
            render_mini_label("Acceptance Criteria", "workplans", "orange")
            criteria_df = pd.DataFrame({"Criterion": task.acceptance_criteria})
            st.dataframe(criteria_df, use_container_width=True, hide_index=True)

      else:
        st.info("Generate an onboarding quest to see work plans.")
        work_plan_features_df = pd.DataFrame([
          {"Area": "Epics", "Purpose": "High-level categories of work"},
          {"Area": "Tasks", "Purpose": "Specific improvements with evidence and acceptance criteria"},
          {"Area": "Milestones", "Purpose": "Grouped tasks for phased implementation"},
        ])
        st.dataframe(work_plan_features_df, use_container_width=True, hide_index=True)
        st.caption("Agent workflows have their own workspace tab.")

    # Agent Workflows tab
    with workflows_tab:
      render_section_header(
        "Agent Workflows",
        "Step-by-step workflows ready to hand to IBM Bob or another coding assistant.",
        "workplans",
        "slate",
      )

      if "work_plan" in st.session_state:
        work_plan = st.session_state["work_plan"]
        st.metric("Workflows", len(work_plan.workflows))
        st.info("Each workflow is generated deterministically from the repo analysis and can be reviewed with optional AI.")

        if work_plan.workflows:
          workflow_idx = st.selectbox(
            "Choose one workflow:",
            range(len(work_plan.workflows)),
            format_func=lambda idx: work_plan.workflows[idx].title,
            key="selected_workflow",
          )
          workflow = work_plan.workflows[workflow_idx]
          st.markdown(f"**Goal:** {workflow.goal}")

          col1, col2 = st.columns(2)
          with col1:
            render_mini_label("Files to read", "reading", "green")
            read_df = pd.DataFrame({"File": workflow.files_to_read})
            st.dataframe(read_df, use_container_width=True, hide_index=True)
          with col2:
            render_mini_label("Files likely to change", "file", "orange")
            change_df = pd.DataFrame({"File": workflow.files_to_change})
            st.dataframe(change_df, use_container_width=True, hide_index=True)

          render_mini_label("Ordered steps", "workplans", "slate")
          steps_df = pd.DataFrame({
            "Step": range(1, len(workflow.ordered_steps) + 1),
            "Action": workflow.ordered_steps,
          })
          st.dataframe(steps_df, use_container_width=True, hide_index=True)

          render_mini_label("Validation steps", "shield", "green")
          validation_df = pd.DataFrame({"Validation": workflow.validation_steps})
          st.dataframe(validation_df, use_container_width=True, hide_index=True)

          st.markdown(f"**Expected output:** {workflow.expected_output}")

          render_mini_label("AI Workflow Review", "assistant", "purple")
          ai_status = get_ai_status()
          section_key = f"workflow_{workflow_idx}"
          if ai_status.is_ready:
            if st.button("Review this workflow", key=f"ai_workflow_{workflow_idx}"):
              def build_request():
                return build_workflow_context(work_plan, snapshot)
              result = run_assistant(section_key, f"Workflow: {workflow.title}", build_request, snapshot)

            if "assistant_outputs" in st.session_state and section_key in st.session_state["assistant_outputs"]:
              result = st.session_state["assistant_outputs"][section_key]
              render_assistant_result(result, "AI-assisted workflow review")
          else:
            tab_caption = format_ai_status_for_tab(ai_status)
            if tab_caption:
              st.caption(tab_caption)
        else:
          st.caption("No agent workflows generated.")

        st.markdown("---")
        render_mini_label("Export Workflows", "export", "blue")
        if st.button("Generate Workflow Markdown", type="primary"):
          work_plan_md = export_workflows_markdown(work_plan, snapshot.source_name)
          st.session_state["work_plan_md"] = work_plan_md
          st.success("Workflow Markdown generated!")

        if "work_plan_md" in st.session_state and not isinstance(st.session_state["work_plan_md"], str):
          st.session_state["work_plan_md"] = export_workflows_markdown(work_plan, snapshot.source_name)

        if "work_plan_md" in st.session_state:
          workflow_markdown = st.session_state["work_plan_md"]
          if workflow_markdown and isinstance(workflow_markdown, str):
            st.download_button(
              label="Download Workflows",
              data=workflow_markdown.encode("utf-8"),
              file_name=f"{snapshot.source_name}_agent_workflows.md",
              mime="text/markdown",
            )
          else:
            st.error("Workflow markdown is not available or invalid.")

          with st.expander("Preview Workflow Markdown"):
            render_code_viewer(
              workflow_markdown,
              "markdown",
              key="work_plan_markdown",
              title="Workflow Markdown",
              compact_chars=2_000,
              expanded_chars=MAX_TEXT_PREVIEW_CHARS,
              compact_height=320,
              expanded_height=680,
            )
      else:
        st.info("Generate an onboarding quest to see agent workflows.")

    # AI Analyzer Tab
    with recommendations_tab:
      render_section_header(
        "AI Analyzer",
        "AI Fusion output, trust gates, and code recommendations grounded in repository evidence.",
        "assistant",
        "purple",
      )

      ai_status = get_ai_status()

      if fused_analysis and fused_analysis.report:
        report = fused_analysis.report
        render_mini_label("AI Fusion Result", "assistant", "purple")
        col1, col2, col3 = st.columns(3)
        with col1:
          st.metric("Mode", fused_analysis.mode.replace("-", " ").title())
        with col2:
          st.metric("Validation", report.validation_status.title())
        with col3:
          st.metric("Applied Overrides", len(fused_analysis.applied_overrides))

        st.markdown(report.summary or fused_analysis.final_summary)

        if report.claims:
          claims_df = pd.DataFrame([
            {
              "Claim": claim.claim_type,
              "Value": claim.value,
              "Confidence": f"{claim.confidence:.0%}",
              "Evidence": ", ".join(claim.evidence[:3]),
            }
            for claim in report.claims
          ])
          st.dataframe(claims_df, use_container_width=True, hide_index=True)

        if report.overrides:
          with st.expander("Override validation details", expanded=bool(fused_analysis.applied_overrides)):
            override_df = pd.DataFrame([
              {
                "Target": override.target,
                "Status": override.status,
                "Confidence": f"{override.confidence:.0%}",
                "Evidence": ", ".join(override.evidence[:3]),
                "Warnings": "; ".join(override.warnings),
              }
              for override in report.overrides
            ])
            st.dataframe(override_df, use_container_width=True, hide_index=True)

        if report.warnings:
          with st.expander("Fusion warnings", expanded=False):
            for warning in report.warnings:
              st.warning(warning)
      else:
        st.info("AI Fusion has not run for this workspace. Deterministic analysis remains available.")

      if not ai_status.is_ready:
        st.info("AI Assistant is disabled. Enable it to generate code recommendations.")
        tab_caption = format_ai_status_for_tab(ai_status)
        if tab_caption:
          st.caption(tab_caption)
      else:
        if "work_plan" in st.session_state:
          work_plan = st.session_state["work_plan"]
          
          # Generate recommendations button
          if st.button("Generate AI Recommendations", type="primary"):
            from repoquest.assistant_context import build_context_pack
            from repoquest.recommendation_generator import generate_recommendation_summary
            
            with st.spinner("Generating AI recommendations..."):
              # Build context pack
              context_pack = build_context_pack(
                snapshot=snapshot,
                fingerprint=fingerprint,
                routes=routes,
                component_cards=component_cards,
                test_intelligence=st.session_state.get("test_intelligence"),
                work_plan=work_plan,
              )
              
              # Get provider and generate recommendations
              provider = get_assistant_provider()
              result = provider.generate_recommendations(
                snapshot, fingerprint, routes, component_cards, work_plan, context_pack
              )
              
              st.session_state["ai_recommendations"] = result
              st.success(f"Generated {len(result.trusted_recommendations)} trusted recommendations")
          
          # Display recommendations if available
          if "ai_recommendations" in st.session_state:
            result = st.session_state["ai_recommendations"]
            
            # Provider info
            col1, col2, col3 = st.columns(3)
            with col1:
              st.metric("Provider", result.provider)
            with col2:
              st.metric("Model", result.model)
            with col3:
              st.metric("Trusted Recommendations", len(result.trusted_recommendations))
            
            if result.warnings:
              with st.expander("⚠️ Warnings"):
                for warning in result.warnings:
                  st.warning(warning)
            
            st.markdown("---")
            
            # Group by priority
            from repoquest.recommendation_validator import (
              sort_recommendations_by_priority,
            )
            
            trusted = result.trusted_recommendations
            if not trusted:
              st.info("No trusted recommendations generated. Try adjusting your repository or AI provider settings.")
            else:
              # Sort by priority
              sorted_recs = sort_recommendations_by_priority(trusted)
              
              # Display by priority
              for priority in ["high", "medium", "low"]:
                priority_recs = [r for r in sorted_recs if r.priority == priority]
                if not priority_recs:
                  continue
                
                priority_color = {"high": "red", "medium": "orange", "low": "blue"}[priority]
                render_mini_label(f"{priority.upper()} Priority", "shield", priority_color)
                
                for rec in priority_recs:
                  with st.expander(f"**{rec.title}** ({rec.category})"):
                    # Validation status with standardized formatting
                    validation_msg = format_recommendation_validation(rec)
                    if rec.validation_status == "valid":
                      st.success(validation_msg)
                    elif rec.validation_status == "downgraded":
                      st.warning(validation_msg)
                    elif rec.validation_status == "invalid":
                      st.error(validation_msg)
                    
                    if rec.validation_warnings and len(rec.validation_warnings) > 2:
                      with st.expander("All Validation Warnings"):
                        for warning in rec.validation_warnings:
                          st.caption(f"• {warning}")
                    
                    # Confidence
                    st.progress(rec.confidence, text=f"Confidence: {rec.confidence:.0%}")
                    
                    # Files
                    if rec.files:
                      render_mini_label("Files", "file", "blue")
                      files_df = pd.DataFrame({"File": rec.files})
                      st.dataframe(files_df, use_container_width=True, hide_index=True)
                    
                    # Evidence
                    if rec.evidence:
                      render_mini_label("Evidence", "shield", "green")
                      evidence_df = pd.DataFrame({"Evidence": rec.evidence})
                      st.dataframe(evidence_df, use_container_width=True, hide_index=True)
                    
                    # Rationale
                    st.markdown("**Why it matters:**")
                    st.markdown(rec.rationale)
                    
                    # Proposed change
                    st.markdown("**Proposed change:**")
                    st.markdown(rec.proposed_change_summary)
                    
                    # Test plan
                    if rec.test_plan:
                      render_mini_label("Test Plan", "test", "cyan")
                      test_df = pd.DataFrame({"Step": rec.test_plan})
                      st.dataframe(test_df, use_container_width=True, hide_index=True)
                    
                    # Workflow
                    st.markdown("**Workflow:**")
                    st.markdown(rec.workflow)
                    
                    # Copyable prompt
                    render_mini_label("AI Assistant Action", "assistant", "purple")
                    prompt = f"""Implement: {rec.title}

Category: {rec.category}
Priority: {rec.priority}

Files to review:
{chr(10).join(f'- {f}' for f in rec.files[:5])}

Rationale:
{rec.rationale}

Proposed change:
{rec.proposed_change_summary}

Test plan:
{chr(10).join(f'{i+1}. {step}' for i, step in enumerate(rec.test_plan))}

Workflow:
{rec.workflow}

IMPORTANT: Do not execute uploaded code. Only analyze and generate improvements."""
                    
                    st.code(prompt, language="text")
                    if prompt and isinstance(prompt, str):
                      st.download_button(
                        "Copy Prompt",
                        prompt,
                        file_name=f"{rec.title.lower().replace(' ', '_')}_prompt.txt",
                        key=f"download_rec_{rec.title}",
                      )
              
              # Summary export
              st.markdown("---")
              render_mini_label("Export Recommendations", "export", "blue")
              
              if st.button("Generate Recommendations Summary"):
                from repoquest.recommendation_generator import generate_recommendation_summary
                summary = generate_recommendation_summary(result)
                st.session_state["recommendations_summary"] = summary
                st.success("Summary generated!")
              
              if "recommendations_summary" in st.session_state:
                summary_data = st.session_state["recommendations_summary"]
                if summary_data and isinstance(summary_data, str):
                  st.download_button(
                    "Download Recommendations",
                    summary_data,
                    file_name=f"{snapshot.source_name}_ai_recommendations.md",
                    mime="text/markdown",
                  )
                else:
                  st.error("Recommendations summary is not available or invalid.")
                
                with st.expander("Preview Summary"):
                  st.markdown(st.session_state["recommendations_summary"])
        else:
          st.info("Generate an onboarding quest first to see AI recommendations.")

    # Tab 7: Quest & Quiz
    with tabs[6]:
      render_section_header(
        "Onboarding Quest & Quiz",
        "Checklist and quiz flow for confirming a new contributor understands the repo.",
        "quiz",
        "cyan",
      )

      # Onboarding checklist in a compact container
      with st.container():
        render_mini_label("Onboarding Checklist", "shield", "green")

        checklist_items = [
          "Read the README to understand project purpose",
          "Identify the main entry points",
          "Understand the project structure and key folders",
          "Review the architecture map",
          "Follow the suggested reading path",
          "Explore component cards for important files",
          "Review test files and coverage",
          "Complete the quiz to verify understanding"
        ]

        # Use columns for compact layout
        col1, col2 = st.columns(2)
        for i, item in enumerate(checklist_items):
          with col1 if i % 2 == 0 else col2:
            st.checkbox(item, key=f"checklist_{item}")

      st.markdown("---")

      # Quiz - Stepper Style
      render_mini_label("Knowledge Check Quiz", "quiz", "cyan")

      if "quiz" in st.session_state:
        quiz = st.session_state["quiz"]

        if quiz:
          # Initialize quiz state
          if "quiz_answers" not in st.session_state:
            st.session_state["quiz_answers"] = {}
          if "quiz_submitted" not in st.session_state:
            st.session_state["quiz_submitted"] = False
          if "quiz_current_question" not in st.session_state:
            st.session_state["quiz_current_question"] = 0

          current_idx = st.session_state["quiz_current_question"]
          total_questions = len(quiz)

          # Quiz not submitted - show stepper
          if not st.session_state["quiz_submitted"]:
            # Progress indicator
            st.progress((current_idx + 1) / total_questions)
            st.markdown(f"**Question {current_idx + 1} of {total_questions}**")
            st.markdown("")

            # Current question
            question = quiz[current_idx]

            with st.container():
              st.markdown(f"### {question.question}")
              st.markdown("")

              # Answer options with radio buttons
              answer = st.radio(
                "Select your answer:",
                question.options,
                key=f"quiz_q{current_idx}_stepper",
                index=question.options.index(st.session_state["quiz_answers"].get(current_idx))
                   if current_idx in st.session_state["quiz_answers"]
                   else None,
                label_visibility="collapsed"
              )

              if answer:
                st.session_state["quiz_answers"][current_idx] = answer

            st.markdown("")

            # Navigation buttons
            col1, col2, col3 = st.columns([1, 1, 2])

            with col1:
              if st.button("Previous", disabled=(current_idx == 0), use_container_width=True):
                st.session_state["quiz_current_question"] = max(0, current_idx - 1)
                st.rerun()

            with col2:
              if current_idx < total_questions - 1:
                if st.button("Next", use_container_width=True):
                  st.session_state["quiz_current_question"] = min(total_questions - 1, current_idx + 1)
                  st.rerun()
              else:
                if st.button("Submit Quiz", type="primary", use_container_width=True):
                  st.session_state["quiz_submitted"] = True
                  st.rerun()

          # Quiz submitted - show results
          else:
            # Calculate score
            correct_count = sum(
              1 for i, q in enumerate(quiz)
              if st.session_state["quiz_answers"].get(i) == q.correct_answer
            )
            total = len(quiz)
            percentage = (correct_count / total * 100) if total > 0 else 0

            # Score summary
            st.markdown("### Quiz Results")
            col1, col2, col3 = st.columns(3)
            with col1:
              st.metric("Score", f"{correct_count}/{total}")
            with col2:
              st.metric("Percentage", f"{percentage:.0f}%")
            with col3:
              if percentage >= 80:
                st.metric("Grade", "Excellent")
              elif percentage >= 60:
                st.metric("Grade", "Good")
              else:
                st.metric("Grade", "Keep Learning")

            st.markdown("")

            if percentage >= 80:
              st.success("Excellent! You have a strong understanding of this codebase.")
            elif percentage >= 60:
              st.info("Good job! Review the areas you missed to strengthen your understanding.")
            else:
              st.warning("Keep learning! Review the reading path and component cards again.")

            st.markdown("---")
            st.markdown("### Answer Review")

            # Show all questions with answers
            for i, question in enumerate(quiz):
              user_answer = st.session_state["quiz_answers"].get(i)
              is_correct = user_answer == question.correct_answer

              with st.expander(
                f"{'' if is_correct else ''} Question {i + 1}: {question.question}",
                expanded=not is_correct
              ):
                st.markdown(f"**Your answer:** {user_answer if user_answer else '*Not answered*'}")
                st.markdown(f"**Correct answer:** {question.correct_answer}")
                st.markdown(f"**Explanation:** {question.explanation}")

            st.markdown("")

            # Reset button
            if st.button("Reset Quiz", type="primary"):
              st.session_state["quiz_submitted"] = False
              st.session_state["quiz_answers"] = {}
              st.session_state["quiz_current_question"] = 0
              st.rerun()

        else:
          st.warning("No quiz questions generated")
      else:
        st.info("Generate an onboarding quest to see the quiz.")
        st.caption("The quiz tests understanding of the codebase structure, key components, and architectural decisions.")

    # Tab 8: Documentation
    with tabs[7]:
      render_section_header(
        "Documentation",
        "Read existing docs, preview config files, and generate the onboarding guide.",
        "docs",
        "green",
      )

      doc_files = get_doc_files(snapshot)

      # README preview
      readme_file = next((f for f in doc_files if f.name.lower() == "readme.md"), None)
      if readme_file:
        render_mini_label("README Preview", "docs", "green")
        preview = readme_file.text_preview[:1000] if readme_file.text_preview else "No preview available"
        if len(readme_file.text_preview) > 1000:
          preview += "\n\n... (truncated)"
        st.markdown(preview)
      else:
        st.info("No README.md found in this repository.")

      st.markdown("---")

      # Documentation files table
      if doc_files:
        render_mini_label("Documentation & Config Files", "folder", "slate")

        doc_data = []
        for doc_file in doc_files:
          doc_data.append({
            "File": doc_file.path,
            "Type": doc_file.suffix,
            "Lines": doc_file.line_count,
            "Size": format_file_size(doc_file.size_bytes)
          })

        doc_df = pd.DataFrame(doc_data)
        st.dataframe(doc_df, use_container_width=True)

        # Preview selected doc file
        selected_doc = st.selectbox(
          "Preview file:",
          ["None"] + [f.path for f in doc_files],
          index=0
        )

        if selected_doc != "None":
          doc_file = next(f for f in doc_files if f.path == selected_doc)
          with st.expander(f" {doc_file.name}"):
            render_code_viewer(
              doc_file.text_preview or "No preview available",
              "markdown" if doc_file.suffix.lower() in {".md", "md"} else "text",
              key=f"doc_{doc_file.path}",
              title=doc_file.path,
              compact_chars=2_000,
              expanded_chars=MAX_TEXT_PREVIEW_CHARS,
              compact_height=320,
              expanded_height=680,
            )

      st.markdown("---")

      # Generated documentation
      render_mini_label("Generated Onboarding Guide", "docs", "green")

      if st.button("Generate Documentation", type="primary"):
        if "fingerprint" in st.session_state and "reading_path" in st.session_state:
          with st.spinner("Generating documentation..."):
            markdown_content = generate_markdown_report(
              snapshot=st.session_state["snapshot"],
              fingerprint=display_fingerprint,
              routes=st.session_state.get("routes", []),
              reading_path=st.session_state.get("reading_path", []),
              component_cards=st.session_state.get("component_cards", []),
              quiz=st.session_state.get("quiz", []),
              import_edges=st.session_state.get("import_edges", []),
              test_intelligence=st.session_state.get("test_intelligence")
            )
            st.session_state["generated_doc"] = markdown_content
            st.success("Documentation generated!")
        else:
          st.warning("Please generate an onboarding quest first.")

      if "generated_doc" in st.session_state and st.session_state["generated_doc"]:
        with st.expander("Preview Generated Guide"):
          doc = st.session_state["generated_doc"]
          if isinstance(doc, str):
            preview = doc[:3000]
            if len(doc) > 3000:
              preview += "\n\n... (truncated, see Export tab for full document)"
            st.markdown(preview)
          else:
            st.warning("Generated document is not in the expected format.")

      st.markdown("---")
      render_mini_label("AI Documentation Review", "assistant", "purple")
      st.caption("Generate optional evidence-cited notes for documentation improvements.")

      ai_status = get_ai_status()
      if ai_status.is_ready and "fingerprint" in st.session_state:
        if st.button("Generate Documentation Review", key="ai_documentation"):
          def build_request():
            return build_documentation_context(snapshot, st.session_state["fingerprint"]) # type: ignore
          result = run_assistant("documentation", "Documentation Notes", build_request, snapshot)

        if "assistant_outputs" in st.session_state and "documentation" in st.session_state["assistant_outputs"]:
          result = st.session_state["assistant_outputs"]["documentation"]
          render_assistant_result(result, "AI-assisted documentation review")
      else:
        tab_caption = format_ai_status_for_tab(ai_status)
        if tab_caption:
          st.caption(tab_caption)

    # Tab 9: Export
    with tabs[8]:
      render_section_header(
        "Export Onboarding Guide",
        "Download a Markdown onboarding guide generated from the deterministic analysis.",
        "export",
        "blue",
      )

      guide_sections_df = pd.DataFrame([
        {"Guide Section": "Project overview", "Includes": "Detected project type, frameworks, and evidence"},
        {"Guide Section": "Architecture summary", "Includes": "Application structure and dependency notes"},
        {"Guide Section": "Reading path", "Includes": "Ordered files with explanations"},
        {"Guide Section": "Component cards", "Includes": "Important files, connections, and test ideas"},
        {"Guide Section": "Quiz questions", "Includes": "Self-assessment questions for onboarding"},
      ])
      st.dataframe(guide_sections_df, use_container_width=True, hide_index=True)

      if "fingerprint" in st.session_state and "reading_path" in st.session_state:
        # Generate markdown report if not already generated
        if "generated_doc" not in st.session_state:
          markdown_content = generate_markdown_report(
            snapshot=st.session_state["snapshot"],
            fingerprint=display_fingerprint,
            routes=st.session_state.get("routes", []),
            reading_path=st.session_state.get("reading_path", []),
            component_cards=st.session_state.get("component_cards", []),
            quiz=st.session_state.get("quiz", []),
            import_edges=st.session_state.get("import_edges", []),
            test_intelligence=st.session_state.get("test_intelligence")
          )
          st.session_state["generated_doc"] = markdown_content

        markdown_content = st.session_state["generated_doc"]

        # Preview
        with st.expander("Preview Markdown Report"):
          st.markdown(markdown_content)

        # Download button
        if markdown_content and isinstance(markdown_content, str):
          st.download_button(
            label="Download Onboarding Guide",
            data=markdown_content,
            file_name=f"{snapshot.source_name}_onboarding_guide.md",
            mime="text/markdown",
            type="primary"
          )
        else:
          st.error("Generated document is not available or invalid.")

        st.markdown("---")
        render_mini_label("AI Export Review", "assistant", "purple")
        st.caption("Optional notes to help refine the exported onboarding guide.")

        ai_status = get_ai_status()
        if ai_status.is_ready and "fingerprint" in st.session_state:
          if st.button("Generate Export Review", key="ai_export_notes"):
            def build_request():
              return build_documentation_context(snapshot, st.session_state["fingerprint"]) # type: ignore
            result = run_assistant("export_notes", "Export Guide Notes", build_request, snapshot)

          if "assistant_outputs" in st.session_state and "export_notes" in st.session_state["assistant_outputs"]:
            result = st.session_state["assistant_outputs"]["export_notes"]
            render_assistant_result(result, "AI-assisted export review")
        else:
          tab_caption = format_ai_status_for_tab(ai_status)
          if tab_caption:
            st.caption(tab_caption)
      else:
        st.info("Generate an onboarding quest to export the guide.")
        guide_use_df = pd.DataFrame([
          {"Use": "Commit to repository", "Value": "Keeps onboarding context close to the code"},
          {"Use": "Share with new team members", "Value": "Gives contributors a starting path"},
          {"Use": "Use as onboarding documentation", "Value": "Captures deterministic findings in Markdown"},
          {"Use": "Reference during code reviews", "Value": "Helps reviewers understand file relationships"},
        ])
        st.dataframe(guide_use_df, use_container_width=True, hide_index=True)

    # About/Built with IBM Bob content moved to the persistent sidebar.
    if False:
      render_section_header(
        "Built with IBM Bob",
        "How the development partner helped scaffold, implement, test, and document RepoQuest.",
        "bob",
        "slate",
      )

      render_mini_label("How IBM Bob Helped Build RepoQuest", "bob", "slate")
      bob_work_df = pd.DataFrame([
        {"Area": "Project scaffolding", "Contribution": "Repository structure, dependency files, local and cloud deployment profiles"},
        {"Area": "Safe repository scanning", "Contribution": "ZIP validation, ignore rules, file limits, and binary detection"},
        {"Area": "Framework detection", "Contribution": "Deterministic rules, confidence scoring, and project type classification"},
        {"Area": "Graph generation", "Contribution": "Python import parsing, JS/TS import patterns, and architecture map generation"},
        {"Area": "Route extraction", "Contribution": "FastAPI route detection, router prefix handling, and route models"},
        {"Area": "Reading path and component cards", "Contribution": "Priority-based reading paths, component card generation, and quiz questions"},
        {"Area": "Streamlit UI", "Contribution": "Tabbed interface, graph visualization, file upload, and validation surfaces"},
        {"Area": "Tests and documentation", "Contribution": "Unit tests, deployment documentation, and milestone tracking"},
      ])
      st.dataframe(bob_work_df, use_container_width=True, hide_index=True)

      render_mini_label("Important Note", "shield", "green")
      st.markdown("**Core RepoQuest evidence does not depend on AI at runtime.** Repository scanning, detection, graphing, routes, imports, ZIP safety, and file limits are deterministic.")
      st.markdown("When optional AI is configured, AI Fusion runs after deterministic analysis and can reinterpret displayed conclusions only with cited evidence and validation. IBM Bob was used during development to help write code, tests, and documentation.")

      render_mini_label("Development Approach", "overview", "blue")
      approach_df = pd.DataFrame([
        {"Principle": "Deterministic evidence", "Why it matters": "The same repository produces repeatable facts and audit trails"},
        {"Principle": "AI-first hybrid mode", "Why it matters": "Configured AI can challenge and improve interpretation without inventing facts"},
        {"Principle": "Framework heuristics", "Why it matters": "Detection is based on visible files and patterns"},
        {"Principle": "Simple ranked priorities", "Why it matters": "Reading paths and cards stay transparent"},
        {"Principle": "No runtime LLM dependency", "Why it matters": "The core demo works without secrets or external APIs"},
        {"Principle": "No vector database or embeddings", "Why it matters": "The app remains small, auditable, and cloud-friendly"},
      ])
      st.dataframe(approach_df, use_container_width=True, hide_index=True)

      st.info("Exported Bob task session reports will be placed in the `bob_sessions/` directory before final submission.")

  else:
    # Welcome message
    st.info("Select a demo repo or upload a ZIP, then click 'Generate Onboarding Quest' to get started!")

    render_section_header(
      "What RepoQuest Does",
      "Converts repository structure into a guided onboarding journey for new contributors.",
      "overview",
      "blue",
    )
    overview_df = pd.DataFrame([
      {"Capability": "Scanning", "Outcome": "Builds a safe file inventory"},
      {"Capability": "Detection", "Outcome": "Finds frameworks, project type, and entry points"},
      {"Capability": "Mapping", "Outcome": "Shows architecture and dependency relationships"},
      {"Capability": "Reading path", "Outcome": "Creates a focused contributor path"},
      {"Capability": "Component cards", "Outcome": "Explains important files with evidence"},
      {"Capability": "Quiz", "Outcome": "Checks understanding before handoff"},
      {"Capability": "Export", "Outcome": "Downloads a Markdown onboarding guide"},
    ])
    st.dataframe(overview_df, use_container_width=True, hide_index=True)

    render_mini_label("How It Works", "workplans", "slate")
    flow_df = pd.DataFrame([
      {"Step": 1, "Action": "Select input", "Result": "Use the bundled demo or upload a ZIP"},
      {"Step": 2, "Action": "Generate quest", "Result": "Analyze the repository with static rules"},
      {"Step": 3, "Action": "Explore tabs", "Result": "Review overview, architecture, reading path, components, tests, quiz, docs, and export"},
      {"Step": 4, "Action": "Download guide", "Result": "Export a comprehensive Markdown document"},
    ])
    st.dataframe(flow_df, use_container_width=True, hide_index=True)

    render_mini_label("Security Features", "shield", "green")
    security_df = pd.DataFrame([
      {"Protection": "Path traversal", "Description": "Rejects ZIP slip attempts"},
      {"Protection": "Absolute paths", "Description": "Rejects paths that should not be extracted or scanned"},
      {"Protection": "Size limits", "Description": "Caps ZIP size and scanned file size"},
      {"Protection": "Binary files", "Description": "Skips binary and unsupported file types"},
      {"Protection": "Execution safety", "Description": "Never runs uploaded code or installs dependencies"},
    ])
    st.dataframe(security_df, use_container_width=True, hide_index=True)

    render_mini_label("Technology", "file", "cyan")
    st.markdown("RepoQuest uses **deterministic static analysis** - no runtime AI, no external APIs, no credentials required.")


if __name__ == "__main__":
  main()

# Made with Bob
