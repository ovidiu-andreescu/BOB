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
  generate_dependency_summary,
)
from repoquest.workflows import generate_work_plan, export_workflows_markdown
from repoquest.test_intelligence import generate_test_intelligence
from repoquest.assistant_provider import get_assistant_provider, get_assistant_config
from repoquest.assistant_validation import validate_assistant_response, format_validation_message
from repoquest.assistant_context import (
  build_overview_context,
  build_file_context,
  build_component_context,
  build_test_context,
  build_workflow_context,
  build_documentation_context,
)
from repoquest.assistant_models import AssistantRunResult
from repoquest.indicator_rules import split_evidence


def reset_analysis():
  """Reset all analysis state."""
  keys_to_remove = [
    "snapshot", "fingerprint", "routes", "import_edges",
    "arch_map", "dep_graph", "reading_path", "component_cards",
    "quiz", "source_type", "quiz_answers", "quiz_submitted",
    "quiz_current_question", "generated_doc", "work_plan", "work_plan_md",
    "test_intelligence", "assistant_outputs"
  ]
  for key in keys_to_remove:
    if key in st.session_state:
      del st.session_state[key]


def get_ai_status_info():
  """Get AI assistant status information."""
  ai_enabled, api_key, _model = get_assistant_config()
  has_key = bool(api_key)

  if not ai_enabled:
    return "disabled", "AI Assistant is disabled"
  elif not has_key:
    return "no_key", "AI Assistant enabled but no API key configured"
  else:
    return "ready", "AI Assistant ready"


def run_assistant(section_id: str, section_title: str, request_builder, snapshot):
  """Run AI assistant for a section and store result."""
  if "assistant_outputs" not in st.session_state:
    st.session_state["assistant_outputs"] = {}

  provider = get_assistant_provider()
  request = request_builder()

  with st.spinner("AI Assistant thinking..."):
    response = provider.generate(request)
    validated_response = validate_assistant_response(response, snapshot)

  result = AssistantRunResult(
    section_id=section_id,
    section_title=section_title,
    request=request,
    response=validated_response,
  )

  st.session_state["assistant_outputs"][section_id] = result
  return result


def render_assistant_result(result: AssistantRunResult, success_label: str = "AI-assisted response"):
  """Render an assistant run result with status and citations."""
  if result.response.status == "ok":
    st.success(f" {success_label}")
    st.markdown(result.response.response_text)
    if result.response.citations:
      st.caption("Evidence paths")
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
      st.warning(validation_msg)


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
        gap: 1rem;
        padding: 1.15rem 1.25rem;
        border: 1px solid #d8dee9;
        border-radius: 8px;
        background: linear-gradient(135deg, #ffffff 0%, #f7f9fc 100%);
        margin: 0.2rem 0 1rem;
      }
      .rq-hero h1 {
        margin: 0;
        color: #1f2937;
        font-size: 2.1rem;
        letter-spacing: 0;
      }
      .rq-hero p {
        margin: 0.25rem 0 0;
        color: #536173;
        font-size: 1rem;
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
        width: 3rem;
        height: 3rem;
        color: #1f4f7a;
        background: #e8f1fb;
        border: 1px solid #cfe0f4;
      }
      .rq-brand-icon svg {
        width: 1.65rem;
        height: 1.65rem;
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
  st.markdown(
    f"""
    <div class="rq-hero">
      <span class="rq-brand-icon">{_icon("architecture")}</span>
      <div>
        <h1>RepoQuest</h1>
        <p>Turn an unfamiliar repo into a guided onboarding journey.</p>
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
  analysis_ready = "snapshot" in st.session_state
  if analysis_ready:
    st.markdown(
      """
      <style>
        [data-testid="stSidebar"],
        [data-testid="collapsedControl"] {
          display: none !important;
        }
      </style>
      """,
      unsafe_allow_html=True,
    )

  # Header
  render_hero()
  st.caption("Detects project type, maps architecture, finds key files, and creates a 30-minute contributor path.")

  # Sidebar
  with st.sidebar:
    render_mini_label("Input Source", "folder", "blue")

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

    st.markdown("---")

    # AI Assistant status
    ai_status, ai_message = get_ai_status_info()
    with st.expander("AI Assistant"):
      if ai_status == "ready":
        st.success(ai_message)
        st.caption("AI features available in tabs after generating quest")
      elif ai_status == "no_key":
        st.warning(f"Warning: {ai_message}")
        st.caption("Set CLAUDE_API_KEY to enable AI features")
      else:
        st.info(f"Info: {ai_message}")
        st.caption("Set REPOQUEST_AI_ENABLED=true to enable")

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

    generate_disabled = input_mode == "Upload ZIP" and uploaded_file is None

    col1, col2 = st.columns(2)

    with col1:
      if st.button(
        "Generate Quest",
        type="primary",
        use_container_width=True,
        disabled=generate_disabled,
        help="Analyze the repository and generate onboarding quest"
      ):
        # Reset previous state
        reset_analysis()

        snapshot = None

        if input_mode == "Use demo repo":
          with st.spinner("Scanning demo repository..."):
            try:
              snapshot = load_demo_repo()
              st.session_state["snapshot"] = snapshot
              st.session_state["source_type"] = "demo"
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
                st.session_state["snapshot"] = snapshot
                st.session_state["source_type"] = "upload"
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
          try:
            # Generate fingerprint
            with st.spinner("Detecting frameworks and project type..."):
              fingerprint = generate_fingerprint(snapshot)
              st.session_state["fingerprint"] = fingerprint

            # Extract routes
            with st.spinner("Extracting API routes..."):
              routes = extract_all_routes(snapshot.files)
              st.session_state["routes"] = routes

            # Build import graph
            with st.spinner("Building dependency graph..."):
              edges = build_import_graph(snapshot.files, "")
              st.session_state["import_edges"] = edges

            # Generate graphs
            with st.spinner("Generating architecture maps..."):
              arch_map = generate_architecture_map(snapshot.files, routes)
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
              st.session_state["dep_graph"] = dep_graph

            # Generate reading path
            with st.spinner("Creating reading path..."):
              reading_path = generate_reading_path(snapshot, fingerprint)
              st.session_state["reading_path"] = reading_path

            # Generate component cards
            with st.spinner("Generating component cards..."):
              component_cards = generate_component_cards(snapshot, fingerprint, routes)
              st.session_state["component_cards"] = component_cards

            # Generate quiz
            with st.spinner("Creating quiz questions..."):
              quiz = generate_quiz(snapshot, fingerprint, routes)
              st.session_state["quiz"] = quiz

            # Generate work plan
            with st.spinner("Generating work plan and workflows..."):
              work_plan = generate_work_plan(
                snapshot, fingerprint, routes, edges, reading_path, component_cards
              )
              st.session_state["work_plan"] = work_plan

            # Generate test intelligence
            with st.spinner("Analyzing test coverage..."):
              test_intelligence = generate_test_intelligence(
                snapshot, routes, edges, component_cards
              )
              st.session_state["test_intelligence"] = test_intelligence

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

  # Main content
  if "snapshot" in st.session_state:
    snapshot = st.session_state["snapshot"]
    fingerprint = st.session_state.get("fingerprint")
    source_type = st.session_state.get("source_type", "unknown")

    # Source info
    source_col, refresh_col = st.columns([5, 1])
    with source_col:
      if source_type == "demo":
        st.info(f"Analyzing bundled demo: **{snapshot.source_name}**")
      elif source_type == "upload":
        st.info(f"Analyzing uploaded ZIP: **{snapshot.source_name}**")
    with refresh_col:
      if st.button("Refresh", use_container_width=True):
        st.rerun()

    # Create tabs
    tabs = st.tabs([
      "Overview",
      "Architecture Map",
      "Reading Path",
      "Components",
      "Tests",
      "Work Plans",
      "Quest & Quiz",
      "Documentation",
      "Export",
      "Built with IBM Bob"
    ])

    # Tab 1: Overview
    with tabs[0]:
      render_section_header(
        "Repository Overview",
        "Project type, framework evidence, entry points, folders, and scan health.",
        "overview",
        "blue",
      )

      if fingerprint:
        # Project type and confidence
        col1, col2 = st.columns([2, 1])
        with col1:
          render_mini_label("Project Type", "overview", "blue")
          st.markdown(f"**{fingerprint.project_type}**")
          st.markdown(fingerprint.summary)
        with col2:
          st.metric("Confidence", f"{fingerprint.confidence * 100:.0f}%")

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
        if fingerprint.entry_points:
          render_mini_label("Entry Points", "route", "green")

          # Build entry points table with type and reason
          entry_data = []
          for entry_point in fingerprint.entry_points:
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

      # AI Assistant section
      st.markdown("---")
      render_mini_label("AI Assistant", "assistant", "purple")

      ai_status, _ = get_ai_status_info()
      if ai_status == "ready" and fingerprint:
        if st.button("Get AI Insights on Overview", key="ai_overview"):
          def build_request():
            return build_overview_context(snapshot, fingerprint) # type: ignore
          result = run_assistant("overview", "Repository Overview", build_request, snapshot)

        # Display result if exists
        if "assistant_outputs" in st.session_state and "overview" in st.session_state["assistant_outputs"]:
          result = st.session_state["assistant_outputs"]["overview"]
          render_assistant_result(result, "AI-assisted overview")
      elif ai_status != "ready":
        st.info("AI Assistant is not enabled. See sidebar for configuration.")

    # Tab 2: Architecture Map
    with tabs[1]:
      render_section_header(
        "Architecture Map",
        "Interactive graph views for application structure, dependencies, routes, and file inspection.",
        "architecture",
        "purple",
      )

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

        # Build filtered graph data
        from repoquest.models import GraphViewMode
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

              # AI Assistant Action
              st.markdown("---")
              render_mini_label("AI Assistant Action", "assistant", "purple")

              ai_status, _ = get_ai_status_info()
              if ai_status == "ready":
                if st.button(f"Ask AI about {file_info.name}", key=f"ai_file_{selected_node_path}"):
                  routes = st.session_state.get("routes", [])
                  def build_request():
                    return build_file_context(file_info, snapshot, routes) # type: ignore
                  result = run_assistant(f"file_{selected_node_path}", f"File: {file_info.name}", build_request, snapshot)

                # Display result if exists
                section_key = f"file_{selected_node_path}"
                if "assistant_outputs" in st.session_state and section_key in st.session_state["assistant_outputs"]:
                  result = st.session_state["assistant_outputs"][section_key]
                  render_assistant_result(result, "AI-assisted file analysis")
              else:
                st.caption("AI Assistant not enabled")

        else:
          st.info("Select a file from the graph above to see detailed information.")

      else:
        st.info("Architecture map will appear here after generating the quest.")

      # Detected Routes
      if "routes" in st.session_state:
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

    # Tab 3: Reading Path
    with tabs[2]:
      render_section_header(
        "Reading & Evidence Workbench",
        "A guided file sequence with previews, role context, improvement ideas, and assistant actions.",
        "reading",
        "green",
      )

      if "reading_path" in st.session_state:
        reading_path = st.session_state["reading_path"]

        if reading_path:
          total_minutes = sum(item.estimated_minutes for item in reading_path)

          st.info(f"Suggested reading path with {len(reading_path)} files (~{total_minutes} minutes). Code previews are buffered and scroll inside each reader.")

          st.markdown("")

          for item in reading_path:
            # Get file info for role display
            file_info = next((f for f in snapshot.files if f.path == item.path), None)
            if not file_info:
              continue

            role_badge = f"*{file_info.role.replace('_', ' ').title()}*"

            with st.expander(f"**{item.order}. {item.path}** - {item.estimated_minutes} min {role_badge}", expanded=False):
              render_metadata_chips([
                ("Role", file_info.role.replace("_", " ").title()),
                ("Language", file_info.language),
                ("Lines", file_info.line_count),
                ("Time", f"{item.estimated_minutes} min"),
              ])

              st.markdown("---")

              # Why read this
              render_mini_label("Why read this", "reading", "green")
              st.markdown(item.reason)
              st.markdown("")

              # Read section - file preview
              if file_info.text_preview and not file_info.skipped:
                render_mini_label("Read", "file", tone_for_role(file_info.role))

                is_truncated = (
                  len(file_info.text_preview) >= MAX_TEXT_PREVIEW_CHARS or
                  file_info.size_bytes > len(file_info.text_preview.encode('utf-8'))
                )

                render_code_viewer(
                  file_info.text_preview,
                  get_language_for_st_code(file_info),
                  key=f"reading_{item.order}_{file_info.path}",
                  title=file_info.path,
                )

                if is_truncated:
                  st.caption(f"*Preview is partial - file has {file_info.line_count} lines ({file_info.size_bytes:,} bytes)*")

                st.markdown("")

              # Understand section
              render_mini_label("Understand", "overview", "blue")
              understand_points = get_understand_points(file_info)
              understand_df = pd.DataFrame({"Focus": understand_points})
              st.dataframe(understand_df, use_container_width=True, hide_index=True)
              st.markdown("")

              # Improve section
              render_mini_label("Improve", "workplans", "orange")
              improvement_ideas = get_improvement_ideas(file_info)
              improvement_df = pd.DataFrame({"Idea": improvement_ideas})
              st.dataframe(improvement_df, use_container_width=True, hide_index=True)
              st.markdown("")

              # AI Assistant Action
              render_mini_label("AI Assistant Action", "assistant", "purple")

              ai_status, _ = get_ai_status_info()
              if ai_status == "ready":
                if st.button(f"Ask AI to explain {file_info.name}", key=f"ai_reading_{item.order}_{file_info.path}"):
                  routes = st.session_state.get("routes", [])
                  def build_request():
                    return build_file_context(file_info, snapshot, routes) # type: ignore
                  result = run_assistant(f"reading_{file_info.path}", f"Reading: {file_info.name}", build_request, snapshot)

                # Display result if exists
                section_key = f"reading_{file_info.path}"
                if "assistant_outputs" in st.session_state and section_key in st.session_state["assistant_outputs"]:
                  result = st.session_state["assistant_outputs"][section_key]
                  render_assistant_result(result, "AI-assisted explanation")
              else:
                st.caption("AI Assistant not enabled")

        else:
          st.warning("No reading path generated")
      else:
        st.info("Generate an onboarding quest to see the reading workbench.")
        reading_features_df = pd.DataFrame([
          {"Section": "Read", "Purpose": "Syntax-highlighted code previews"},
          {"Section": "Understand", "Purpose": "What to look for in each file"},
          {"Section": "Improve", "Purpose": "Concrete improvement suggestions"},
          {"Section": "AI Assistant Action", "Purpose": "Optional AI-assisted explanations"},
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
            for card in filtered_cards:
              with st.expander(f"**{card.title}** - {card.path}"):
                # Role and why it matters
                render_component_intro(
                  card.role,
                  card.path,
                  card.why_it_matters,
                  tone_for_role(card.role),
                )

                # Detected items section (only if present)
                if card.detected_items:
                  render_mini_label("Detected Evidence", "shield", "blue")
                  evidence_df = pd.DataFrame({"Evidence": card.detected_items})
                  st.dataframe(evidence_df, use_container_width=True, hide_index=True)
                  st.markdown("")

                  # Try to show code snippet for first detected item
                  file_info = next((f for f in snapshot.files if f.path == card.path), None)
                  if file_info and file_info.text_preview:
                    first_item = card.detected_items[0]
                    # Extract pattern from detected item
                    pattern = first_item.split("(")[0] if "(" in first_item else first_item
                    snippet = extract_code_snippet(file_info, pattern)
                    if snippet:
                      render_mini_label("Code Snippet", "file", tone_for_role(file_info.role))
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
                      st.markdown("")

                # Connected files section (only if present)
                if card.connected_to:
                  render_mini_label("Connected Files", "architecture", "purple")
                  connected_df = pd.DataFrame({"File": card.connected_to})
                  st.dataframe(connected_df, use_container_width=True, hide_index=True)
                  st.markdown("")

                # Test ideas section (only if present)
                if card.suggested_test_ideas:
                  render_mini_label("Suggested Test Ideas", "tests", "purple")
                  test_df = pd.DataFrame({"Idea": card.suggested_test_ideas})
                  st.dataframe(test_df, use_container_width=True, hide_index=True)
                  st.markdown("")

                # AI Assistant Action
                render_mini_label("AI Assistant Action", "assistant", "purple")

                ai_status, _ = get_ai_status_info()
                if ai_status == "ready":
                  if st.button(f"Ask AI for risks/tests", key=f"ai_component_{card.path}"):
                    def build_request():
                      return build_component_context(card, snapshot)
                    result = run_assistant(f"component_{card.path}", f"Component: {card.title}", build_request, snapshot)

                  # Display result if exists
                  section_key = f"component_{card.path}"
                  if "assistant_outputs" in st.session_state and section_key in st.session_state["assistant_outputs"]:
                    result = st.session_state["assistant_outputs"][section_key]
                    render_assistant_result(result, "AI-assisted component analysis")
                else:
                  st.caption("AI Assistant not enabled")

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

        # AI Test Plan
        render_mini_label("AI Test Plan", "assistant", "purple")
        st.caption("AI-assisted test recommendations")

        ai_status, _ = get_ai_status_info()
        if ai_status == "ready":
          if st.button("Generate AI Test Plan", key="ai_test_plan"):
            def build_request():
              return build_test_context(test_intel, snapshot)
            result = run_assistant("test_plan", "Test Intelligence", build_request, snapshot)

          # Display result if exists
          if "assistant_outputs" in st.session_state and "test_plan" in st.session_state["assistant_outputs"]:
            result = st.session_state["assistant_outputs"]["test_plan"]
            render_assistant_result(result, "AI-assisted test plan")
        else:
          st.caption("AI Assistant not enabled")

      else:
        st.info("Generate an onboarding quest to see test intelligence.")
        test_features_df = pd.DataFrame([
          {"Section": "Test Inventory", "Purpose": "What test files exist and their frameworks"},
          {"Section": "Impact Map", "Purpose": "Which tests likely cover which application files"},
          {"Section": "Missing Coverage", "Purpose": "Routes and components that appear untested"},
          {"Section": "Quality Signals", "Purpose": "Assertions, fixtures, mocks, and test patterns"},
          {"Section": "Suggested Tests", "Purpose": "Concrete next test cases to add"},
          {"Section": "AI Test Plan", "Purpose": "Optional AI-assisted test recommendations"},
        ])
        st.dataframe(test_features_df, use_container_width=True, hide_index=True)

    # Tab 6: Work Plans
    with tabs[5]:
      render_section_header(
        "Work Plans & Agent Workflows",
        "Evidence-backed milestones, tasks, and guided workflows for follow-up development.",
        "workplans",
        "slate",
      )

      if "work_plan" in st.session_state:
        work_plan = st.session_state["work_plan"]

        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
          st.metric("Epics", len(work_plan.epics))
        with col2:
          st.metric("Tasks", len(work_plan.tasks))
        with col3:
          st.metric("Milestones", len(work_plan.milestones))
        with col4:
          st.metric("Workflows", len(work_plan.workflows))

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

        st.markdown("---")

        # Agent Workflows
        render_mini_label("Agent Workflows", "workplans", "slate")
        st.info("These workflows are ready to use with an AI coding assistant.")

        for workflow_idx, workflow in enumerate(work_plan.workflows):
          with st.expander(f"**{workflow.title}**", expanded=False):
            st.markdown(f"**Goal:** {workflow.goal}")
            st.markdown("")

            col1, col2 = st.columns(2)

            with col1:
              render_mini_label("Files to read", "reading", "green")
              read_df = pd.DataFrame({"File": workflow.files_to_read})
              st.dataframe(read_df, use_container_width=True, hide_index=True)

            with col2:
              render_mini_label("Files likely to change", "file", "orange")
              change_df = pd.DataFrame({"File": workflow.files_to_change})
              st.dataframe(change_df, use_container_width=True, hide_index=True)

            st.markdown("")
            render_mini_label("Ordered steps", "workplans", "slate")
            steps_df = pd.DataFrame({
              "Step": range(1, len(workflow.ordered_steps) + 1),
              "Action": workflow.ordered_steps
            })
            st.dataframe(steps_df, use_container_width=True, hide_index=True)

            st.markdown("")
            render_mini_label("Validation steps", "shield", "green")
            validation_df = pd.DataFrame({"Validation": workflow.validation_steps})
            st.dataframe(validation_df, use_container_width=True, hide_index=True)

            st.markdown("")
            st.markdown(f"**Expected output:** {workflow.expected_output}")

            st.markdown("")
            ai_status, _ = get_ai_status_info()
            section_key = f"workflow_{workflow_idx}"
            if ai_status == "ready":
              if st.button("Ask AI to refine this workflow", key=f"ai_workflow_{workflow_idx}"):
                def build_request():
                  return build_workflow_context(work_plan, snapshot)
                result = run_assistant(section_key, f"Workflow: {workflow.title}", build_request, snapshot)

              if "assistant_outputs" in st.session_state and section_key in st.session_state["assistant_outputs"]:
                result = st.session_state["assistant_outputs"][section_key]
                render_assistant_result(result, "AI-assisted workflow refinement")
            else:
              st.caption("AI Assistant not enabled")

        st.markdown("---")

        # Export work plan
        render_mini_label("Export Work Plan", "export", "blue")

        if st.button("Generate Work Plan Markdown", type="primary"):
          work_plan_md = export_workflows_markdown(work_plan, snapshot.source_name)
          st.session_state["work_plan_md"] = work_plan_md
          st.success("Work plan Markdown generated!")

        if "work_plan_md" in st.session_state:
          st.download_button(
            label="Download Work Plan",
            data=st.session_state["work_plan_md"],
            file_name=f"{snapshot.source_name}_work_plan.md",
            mime="text/markdown",
          )

          with st.expander("Preview Work Plan Markdown"):
            render_code_viewer(
              st.session_state["work_plan_md"],
              "markdown",
              key="work_plan_markdown",
              title="Work plan Markdown",
              compact_chars=2_000,
              expanded_chars=MAX_TEXT_PREVIEW_CHARS,
              compact_height=320,
              expanded_height=680,
            )

      else:
        st.info("Generate an onboarding quest to see work plans and agent workflows.")
        work_plan_features_df = pd.DataFrame([
          {"Area": "Epics", "Purpose": "High-level categories of work"},
          {"Area": "Tasks", "Purpose": "Specific improvements with evidence and acceptance criteria"},
          {"Area": "Milestones", "Purpose": "Grouped tasks for phased implementation"},
          {"Area": "Agent workflows", "Purpose": "Step-by-step instructions ready for an AI coding assistant"},
        ])
        st.dataframe(work_plan_features_df, use_container_width=True, hide_index=True)
        st.caption("These are generated deterministically from repo analysis and are ready to use with AI coding assistants.")

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
              fingerprint=st.session_state["fingerprint"],
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

      if "generated_doc" in st.session_state:
        with st.expander("Preview Generated Guide"):
          preview = st.session_state["generated_doc"][:3000]
          if len(st.session_state["generated_doc"]) > 3000:
            preview += "\n\n... (truncated, see Export tab for full document)"
          st.markdown(preview)

      st.markdown("---")
      render_mini_label("AI Assistant", "assistant", "purple")
      st.caption("Generate optional AI-assisted notes for documentation improvements.")

      ai_status, _ = get_ai_status_info()
      if ai_status == "ready" and "fingerprint" in st.session_state:
        if st.button("Generate AI-assisted guide notes", key="ai_documentation"):
          def build_request():
            return build_documentation_context(snapshot, st.session_state["fingerprint"]) # type: ignore
          result = run_assistant("documentation", "Documentation Notes", build_request, snapshot)

        if "assistant_outputs" in st.session_state and "documentation" in st.session_state["assistant_outputs"]:
          result = st.session_state["assistant_outputs"]["documentation"]
          render_assistant_result(result, "AI-assisted documentation notes")
      else:
        st.caption("AI Assistant not enabled")

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
            fingerprint=st.session_state["fingerprint"],
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
        st.download_button(
          label="Download Onboarding Guide",
          data=markdown_content,
          file_name=f"{snapshot.source_name}_onboarding_guide.md",
          mime="text/markdown",
          type="primary"
        )

        st.markdown("---")
        render_mini_label("AI-assisted Guide Notes", "assistant", "purple")
        st.caption("Optional notes to help refine the exported onboarding guide.")

        ai_status, _ = get_ai_status_info()
        if ai_status == "ready" and "fingerprint" in st.session_state:
          if st.button("Generate AI-assisted guide notes", key="ai_export_notes"):
            def build_request():
              return build_documentation_context(snapshot, st.session_state["fingerprint"]) # type: ignore
            result = run_assistant("export_notes", "Export Guide Notes", build_request, snapshot)

          if "assistant_outputs" in st.session_state and "export_notes" in st.session_state["assistant_outputs"]:
            result = st.session_state["assistant_outputs"]["export_notes"]
            render_assistant_result(result, "AI-assisted guide notes")
        else:
          st.caption("AI Assistant not enabled")
      else:
        st.info("Generate an onboarding quest to export the guide.")
        guide_use_df = pd.DataFrame([
          {"Use": "Commit to repository", "Value": "Keeps onboarding context close to the code"},
          {"Use": "Share with new team members", "Value": "Gives contributors a starting path"},
          {"Use": "Use as onboarding documentation", "Value": "Captures deterministic findings in Markdown"},
          {"Use": "Reference during code reviews", "Value": "Helps reviewers understand file relationships"},
        ])
        st.dataframe(guide_use_df, use_container_width=True, hide_index=True)

    # Tab 10: Built with IBM Bob
    with tabs[9]:
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
      st.markdown("**Core RepoQuest analysis does not depend on AI at runtime.** Repository scanning, detection, graphing, reading paths, component cards, quiz generation, and export are deterministic.")
      st.markdown("IBM Bob was used during development to help write code, tests, and documentation. Optional assistant features only run when explicitly configured and clicked.")

      render_mini_label("Development Approach", "overview", "blue")
      approach_df = pd.DataFrame([
        {"Principle": "Deterministic analysis", "Why it matters": "The same repository produces repeatable findings"},
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
