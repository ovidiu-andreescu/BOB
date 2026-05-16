"""RepoQuest - Turn unfamiliar repos into guided onboarding journeys."""

import streamlit as st
import pandas as pd
from pathlib import Path
import tempfile

from repoquest.sample_loader import load_demo_repo
from repoquest.scanner import scan_zip
from repoquest.zip_safety import ZIPSafetyError
from repoquest.detectors import generate_fingerprint
from repoquest.route_extractors import extract_all_routes
from repoquest.import_graph import build_import_graph
from repoquest.architecture import (
    generate_architecture_map,
    generate_dependency_graph,
    generate_simple_graph
)
from repoquest.reading_path import generate_reading_path
from repoquest.quest import generate_component_cards, generate_quiz
from repoquest.config import MAX_ZIP_SIZE_MB
from repoquest.report import (
    generate_markdown_report,
    extract_code_snippet,
    get_test_files,
    get_doc_files,
    generate_dependency_summary,
)


def reset_analysis():
    """Reset all analysis state."""
    keys_to_remove = [
        "snapshot", "fingerprint", "routes", "import_edges",
        "arch_map", "dep_graph", "reading_path", "component_cards",
        "quiz", "source_type", "quiz_answers", "quiz_submitted",
        "generated_doc"
    ]
    for key in keys_to_remove:
        if key in st.session_state:
            del st.session_state[key]





def main():
    st.set_page_config(
        page_title="RepoQuest",
        page_icon="🗺️",
        layout="wide",
    )

    # Header
    st.title("🗺️ RepoQuest")
    st.markdown("Turn an unfamiliar repo into a guided onboarding journey")
    st.markdown("*Detects project type, maps architecture, finds key files, and creates a 30-minute contributor path.*")

    # Sidebar
    with st.sidebar:
        st.header("Input Source")

        input_mode = st.radio(
            "Choose input:",
            ["Use demo repo", "Upload ZIP"],
            help="Select how to provide the repository"
        )

        uploaded_file = None
        if input_mode == "Upload ZIP":
            st.info(f"📦 Max ZIP size: {MAX_ZIP_SIZE_MB} MB")
            uploaded_file = st.file_uploader(
                "Choose a ZIP file",
                type=["zip"],
                help=f"Upload a repository ZIP file (max {MAX_ZIP_SIZE_MB} MB)"
            )

        st.markdown("---")

        # App limits info
        with st.expander("ℹ️ App Limits"):
            st.markdown(f"""
            - **Max ZIP size:** {MAX_ZIP_SIZE_MB} MB
            - **Max files scanned:** 600
            - **Max file size:** 512 KB
            - **Max graph nodes:** 80
            - **Max reading path items:** 9
            - **Max component cards:** 30
            - **Max quiz questions:** 8
            """)

        generate_disabled = input_mode == "Upload ZIP" and uploaded_file is None

        col1, col2 = st.columns(2)
        
        with col1:
            if st.button(
                "🚀 Generate Quest",
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
                            st.error(f"🚫 ZIP Safety Error: {e}")
                            st.warning("The uploaded ZIP file failed security validation. Please ensure it contains only safe paths and is under the size limit.")
                            return
                        except Exception as e:
                            st.error(f"Error processing ZIP file: {e}")
                            import traceback
                            with st.expander("Show error details"):
                                st.code(traceback.format_exc())
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

                        st.success("✅ Onboarding Quest generated successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error analyzing repository: {e}")
                        import traceback
                        with st.expander("Show error details"):
                            st.code(traceback.format_exc())
        
        with col2:
            if st.button(
                "🔄 Reset",
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
        if source_type == "demo":
            st.info(f"📦 Analyzing bundled demo: **{snapshot.source_name}**")
        elif source_type == "upload":
            st.info(f"📤 Analyzing uploaded ZIP: **{snapshot.source_name}**")

        # Create tabs
        tabs = st.tabs([
            "📊 Overview",
            "🏗️ Architecture Map",
            "📖 Reading Path",
            "🎯 Components",
            "🧪 Tests",
            "🎮 Quest & Quiz",
            "📚 Documentation",
            "📥 Export",
            "🤖 Built with IBM Bob"
        ])

        # Tab 1: Overview
        with tabs[0]:
            st.header("Repository Overview")

            if fingerprint:
                # Project type and confidence
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.subheader(f"Project Type: {fingerprint.project_type}")
                    st.markdown(fingerprint.summary)
                with col2:
                    st.metric("Confidence", f"{fingerprint.confidence * 100:.0f}%")

                # Frameworks
                if fingerprint.frameworks:
                    st.subheader("🔧 Detected Frameworks")
                    
                    for framework in fingerprint.frameworks:
                        with st.expander(f"**{framework.name}** ({framework.category}) - {framework.confidence * 100:.0f}% confidence"):
                            st.markdown("**Evidence:**")
                            for evidence in framework.evidence:
                                st.markdown(f"- {evidence}")

                # Entry points
                if fingerprint.entry_points:
                    st.subheader("🚪 Entry Points")
                    for entry_point in fingerprint.entry_points:
                        st.markdown(f"- `{entry_point}`")

                # Key folders
                if fingerprint.key_folders:
                    st.subheader("📁 Key Folders")
                    for folder in fingerprint.key_folders:
                        st.markdown(f"- `{folder}`")

                # Warnings
                if fingerprint.warnings:
                    st.subheader("⚠️ Warnings")
                    for warning in fingerprint.warnings:
                        st.warning(warning)

            # Summary metrics
            st.subheader("📈 Scan Summary")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Files Seen", snapshot.total_files_seen)
            with col2:
                st.metric("Files Scanned", snapshot.total_files_scanned)
            with col3:
                scanned_files = [f for f in snapshot.files if not f.skipped]
                st.metric("Analyzed Files", len(scanned_files))

        # Tab 2: Architecture Map
        with tabs[1]:
            st.header("Architecture Map")

            st.markdown("""
            This human-friendly map shows the high-level structure of the application,
            highlighting key components and their relationships.
            """)

            if "arch_map" in st.session_state:
                try:
                    st.graphviz_chart(st.session_state["arch_map"])
                except Exception as e:
                    st.error(f"Error rendering architecture map: {e}")
            else:
                st.info("Architecture map will appear here after generating the quest.")

            st.markdown("---")
            st.subheader("🔗 Dependency Graph")

            st.markdown("""
            This technical graph shows actual import relationships between files in the repository.
            **Note:** Test files are excluded from this view and shown separately in the Tests tab.
            """)

            if "dep_graph" in st.session_state:
                try:
                    st.graphviz_chart(st.session_state["dep_graph"])
                except Exception as e:
                    st.error(f"Error rendering dependency graph: {e}")
                
                # Dependency path summary
                if "import_edges" in st.session_state:
                    edges = st.session_state["import_edges"]
                    if edges:
                        with st.expander("📊 Dependency Path Summary"):
                            summary = generate_dependency_summary(snapshot, edges)
                            st.text(summary)
                
                # Legend
                with st.expander("🎨 Graph Legend"):
                    st.markdown("""
                    **Node Colors:**
                    - 🟦 **Blue:** Entry points (main.py, App.tsx, etc.)
                    - 🟩 **Green:** Frontend components and pages
                    - 🟨 **Yellow:** Backend routes and services
                    - 🟧 **Orange:** Models and data structures
                    - ⬜ **White:** Other files
                    
                    **Edge Styles:**
                    - **Solid line:** Direct import/dependency
                    - **Dashed line:** API boundary (frontend → backend)
                    """)
            else:
                st.info("Dependency graph will appear here after generating the quest.")

            # Detected Routes
            if "routes" in st.session_state:
                routes = st.session_state["routes"]

                if routes:
                    st.markdown("---")
                    st.subheader("🛣️ Detected API Routes")

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
            st.header("📖 30-Minute Reading Path")

            if "reading_path" in st.session_state:
                reading_path = st.session_state["reading_path"]

                if reading_path:
                    total_minutes = sum(item.estimated_minutes for item in reading_path)
                    st.info(f"📚 Suggested reading path with {len(reading_path)} files (~{total_minutes} minutes)")

                    for item in reading_path:
                        with st.expander(f"**{item.order}. {item.path}** ({item.estimated_minutes} min)"):
                            st.markdown("**Why read this:**")
                            st.markdown(item.reason)
                else:
                    st.warning("No reading path generated")
            else:
                st.info("📖 Generate an onboarding quest to see the suggested reading path.")
                st.markdown("""
                The reading path will guide you through the most important files in a logical order,
                helping you understand the codebase in approximately 30 minutes.
                """)

        # Tab 4: Components
        with tabs[3]:
            st.header("🎯 Component Cards")

            if "component_cards" in st.session_state:
                component_cards = st.session_state["component_cards"]

                if component_cards:
                    st.info(f"📦 {len(component_cards)} important components identified")

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

                    for card in filtered_cards:
                        with st.expander(f"**{card.title}** - {card.path}"):
                            st.markdown(f"**Role:** {card.role}")
                            st.markdown(f"*{card.why_it_matters}*")

                            if card.detected_items:
                                st.markdown("**Detected items:**")
                                for item in card.detected_items:
                                    st.markdown(f"- {item}")
                                
                                # Try to show code snippet for first detected item
                                if card.detected_items:
                                    file_info = next((f for f in snapshot.files if f.path == card.path), None)
                                    if file_info and file_info.text_preview:
                                        first_item = card.detected_items[0]
                                        # Extract pattern from detected item (e.g., "@router.get" from "@router.get('/trips')")
                                        pattern = first_item.split("(")[0] if "(" in first_item else first_item
                                        snippet = extract_code_snippet(file_info, pattern)
                                        if snippet:
                                            with st.expander("📄 Code snippet"):
                                                st.code(snippet, language=file_info.language)

                            if card.connected_to:
                                st.markdown("**Connected to:**")
                                for conn in card.connected_to:
                                    st.markdown(f"- `{conn}`")

                            if card.suggested_test_ideas:
                                st.markdown("**💡 Suggested test ideas:**")
                                for idea in card.suggested_test_ideas:
                                    st.markdown(f"- {idea}")

                            st.markdown("**🤖 Suggested IBM Bob prompt:**")
                            st.code(card.suggested_bob_prompt, language=None)
                else:
                    st.warning("No component cards generated")
            else:
                st.info("🎯 Generate an onboarding quest to see component cards.")
                st.markdown("""
                Component cards provide detailed information about important files,
                including their role, connections, and suggested test ideas.
                """)

        # Tab 5: Tests
        with tabs[4]:
            st.header("🧪 Test Files")

            test_files = get_test_files(snapshot)
            
            if test_files:
                st.info(f"🧪 Found {len(test_files)} test files")
                
                for test_file in test_files:
                    with st.expander(f"**{test_file.path}**"):
                        st.markdown(f"**Language:** {test_file.language}")
                        st.markdown(f"**Lines:** {test_file.line_count}")
                        
                        # Detect test framework
                        framework_hints = []
                        if test_file.text_preview:
                            if "pytest" in test_file.text_preview or "def test_" in test_file.text_preview:
                                framework_hints.append("pytest")
                            if "unittest" in test_file.text_preview:
                                framework_hints.append("unittest")
                            if "jest" in test_file.text_preview or "describe(" in test_file.text_preview:
                                framework_hints.append("jest")
                        
                        if framework_hints:
                            st.markdown(f"**Likely framework:** {', '.join(framework_hints)}")
                        
                        # Find imports to detect what's being tested
                        if test_file.text_preview:
                            imports = []
                            for line in test_file.text_preview.split('\n')[:20]:
                                if line.strip().startswith('import ') or line.strip().startswith('from '):
                                    imports.append(line.strip())
                            
                            if imports:
                                st.markdown("**Imports:**")
                                for imp in imports[:5]:
                                    st.code(imp, language=test_file.language)
                        
                        # Find related component card
                        if "component_cards" in st.session_state:
                            related_cards = [
                                card for card in st.session_state["component_cards"]
                                if any(test_idea for test_idea in card.suggested_test_ideas)
                            ]
                            if related_cards:
                                st.markdown("**Related components with test suggestions:**")
                                for card in related_cards[:3]:
                                    st.markdown(f"- `{card.path}`")
            else:
                st.info("🧪 No test files detected in this repository.")
                st.markdown("""
                Test files help verify that the code works correctly. Consider adding tests for:
                - API endpoints
                - Business logic
                - Data models
                - UI components
                """)
            
            # Show suggested tests from component cards
            if "component_cards" in st.session_state:
                all_test_ideas = []
                for card in st.session_state["component_cards"]:
                    if card.suggested_test_ideas:
                        all_test_ideas.extend([
                            f"{card.path}: {idea}"
                            for idea in card.suggested_test_ideas
                        ])
                
                if all_test_ideas:
                    st.markdown("---")
                    st.subheader("💡 Suggested Next Tests")
                    st.markdown("Based on component analysis, consider adding tests for:")
                    for idea in all_test_ideas[:10]:
                        st.markdown(f"- {idea}")

        # Tab 6: Quest & Quiz
        with tabs[5]:
            st.header("🎮 Onboarding Quest & Quiz")

            # Onboarding checklist
            st.subheader("✅ Onboarding Checklist")
            
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

            for item in checklist_items:
                st.checkbox(item, key=f"checklist_{item}")

            st.markdown("---")

            # Quiz
            st.subheader("🧠 Knowledge Check Quiz")

            if "quiz" in st.session_state:
                quiz = st.session_state["quiz"]

                if quiz:
                    st.info(f"📝 {len(quiz)} questions to test your understanding")

                    # Initialize quiz state
                    if "quiz_answers" not in st.session_state:
                        st.session_state["quiz_answers"] = {}
                    if "quiz_submitted" not in st.session_state:
                        st.session_state["quiz_submitted"] = False

                    for i, question in enumerate(quiz):
                        st.markdown(f"**Question {i + 1}:** {question.question}")
                        
                        answer = st.radio(
                            f"Select your answer for Q{i + 1}:",
                            question.options,
                            key=f"quiz_q{i}",
                            index=None,
                            disabled=st.session_state["quiz_submitted"]
                        )

                        if answer:
                            st.session_state["quiz_answers"][i] = answer

                        # Show explanation if submitted
                        if st.session_state["quiz_submitted"]:
                            if answer == question.correct_answer:
                                st.success(f"✅ Correct! {question.explanation}")
                            else:
                                st.error(f"❌ Incorrect. The correct answer is: **{question.correct_answer}**")
                                st.info(question.explanation)

                        st.markdown("---")

                    # Submit button
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        if not st.session_state["quiz_submitted"]:
                            if st.button("Submit Quiz", type="primary"):
                                st.session_state["quiz_submitted"] = True
                                st.rerun()
                        else:
                            if st.button("Reset Quiz"):
                                st.session_state["quiz_submitted"] = False
                                st.session_state["quiz_answers"] = {}
                                st.rerun()

                    # Show score if submitted
                    if st.session_state["quiz_submitted"]:
                        correct_count = sum(
                            1 for i, q in enumerate(quiz)
                            if st.session_state["quiz_answers"].get(i) == q.correct_answer
                        )
                        total = len(quiz)
                        percentage = (correct_count / total * 100) if total > 0 else 0

                        st.markdown("---")
                        st.subheader("📊 Quiz Results")
                        st.metric("Score", f"{correct_count}/{total} ({percentage:.0f}%)")

                        if percentage >= 80:
                            st.success("🎉 Excellent! You have a strong understanding of this codebase.")
                        elif percentage >= 60:
                            st.info("👍 Good job! Review the areas you missed to strengthen your understanding.")
                        else:
                            st.warning("📚 Keep learning! Review the reading path and component cards again.")

                else:
                    st.warning("No quiz questions generated")
            else:
                st.info("🎮 Generate an onboarding quest to see the quiz.")
                st.markdown("""
                The quiz will test your understanding of the codebase structure,
                key components, and architectural decisions.
                """)

        # Tab 7: Documentation
        with tabs[6]:
            st.header("📚 Documentation")

            doc_files = get_doc_files(snapshot)
            
            # README preview
            readme_file = next((f for f in doc_files if f.name.lower() == "readme.md"), None)
            if readme_file:
                st.subheader("📖 README Preview")
                preview = readme_file.text_preview[:1000] if readme_file.text_preview else "No preview available"
                if len(readme_file.text_preview) > 1000:
                    preview += "\n\n... (truncated)"
                st.markdown(preview)
            else:
                st.info("No README.md found in this repository.")
            
            st.markdown("---")
            
            # Documentation files table
            if doc_files:
                st.subheader("📄 Documentation & Config Files")
                
                doc_data = []
                for doc_file in doc_files:
                    doc_data.append({
                        "File": doc_file.path,
                        "Type": doc_file.suffix,
                        "Lines": doc_file.line_count,
                        "Size": f"{doc_file.size_bytes / 1024:.1f} KB"
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
                    with st.expander(f"📄 {doc_file.name}"):
                        preview = doc_file.text_preview[:2000] if doc_file.text_preview else "No preview available"
                        if len(doc_file.text_preview) > 2000:
                            preview += "\n\n... (truncated)"
                        st.code(preview, language=None)
            
            st.markdown("---")
            
            # Generated documentation
            st.subheader("📝 Generated Onboarding Guide")
            
            if st.button("🔄 Generate Documentation", type="primary"):
                if "fingerprint" in st.session_state and "reading_path" in st.session_state:
                    with st.spinner("Generating documentation..."):
                        markdown_content = generate_markdown_report(
                            snapshot=st.session_state["snapshot"],
                            fingerprint=st.session_state["fingerprint"],
                            routes=st.session_state.get("routes", []),
                            reading_path=st.session_state.get("reading_path", []),
                            component_cards=st.session_state.get("component_cards", []),
                            quiz=st.session_state.get("quiz", []),
                            import_edges=st.session_state.get("import_edges", [])
                        )
                        st.session_state["generated_doc"] = markdown_content
                        st.success("✅ Documentation generated!")
                else:
                    st.warning("Please generate an onboarding quest first.")
            
            if "generated_doc" in st.session_state:
                with st.expander("📄 Preview Generated Guide"):
                    preview = st.session_state["generated_doc"][:3000]
                    if len(st.session_state["generated_doc"]) > 3000:
                        preview += "\n\n... (truncated, see Export tab for full document)"
                    st.markdown(preview)

        # Tab 8: Export
        with tabs[7]:
            st.header("📥 Export Onboarding Guide")

            st.markdown("""
            Download a comprehensive Markdown guide that includes:
            - Project overview and detected frameworks
            - Architecture summary
            - Reading path with explanations
            - Component cards with test ideas
            - Quiz questions for self-assessment
            """)

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
                        import_edges=st.session_state.get("import_edges", [])
                    )
                    st.session_state["generated_doc"] = markdown_content
                
                markdown_content = st.session_state["generated_doc"]

                # Preview
                with st.expander("📄 Preview Markdown Report"):
                    st.markdown(markdown_content)

                # Download button
                st.download_button(
                    label="📥 Download Onboarding Guide",
                    data=markdown_content,
                    file_name=f"{snapshot.source_name}_onboarding_guide.md",
                    mime="text/markdown",
                    type="primary"
                )
            else:
                st.info("📥 Generate an onboarding quest to export the guide.")
                st.markdown("""
                The exported guide will be a comprehensive Markdown document that can be:
                - Committed to the repository
                - Shared with new team members
                - Used as onboarding documentation
                - Referenced during code reviews
                """)

        # Tab 9: Built with IBM Bob
        with tabs[8]:
            st.header("🤖 Built with IBM Bob")

            st.markdown("""
            ### How IBM Bob Helped Build RepoQuest

            IBM Bob was used as a development partner throughout this project, helping with:

            **1. Project Scaffolding**
            - Created the repository structure
            - Set up dependency management
            - Configured local and cloud deployment profiles

            **2. Safe Repository Scanning**
            - Implemented ZIP safety validation
            - Built file scanning with ignore rules
            - Added binary file detection

            **3. Framework Detection**
            - Designed deterministic detection rules
            - Implemented confidence scoring
            - Created project type classification

            **4. Graph Generation**
            - Built Python import parsing with AST
            - Implemented JS/TS import regex patterns
            - Created architecture map generation

            **5. Route Extraction**
            - Implemented FastAPI route detection
            - Added router prefix detection
            - Created route information models

            **6. Reading Path & Component Cards**
            - Designed priority-based reading path
            - Created component card generation
            - Implemented quiz question generation

            **7. Streamlit UI**
            - Built tabbed interface
            - Created interactive visualizations
            - Implemented file upload and validation

            **8. Tests & Documentation**
            - Generated comprehensive unit tests
            - Created deployment documentation
            - Wrote milestone tracking docs

            ### Important Note

            **RepoQuest does not use AI at runtime.** All analysis is deterministic, based on:
            - Static file scanning
            - Pattern matching
            - Heuristic rules
            - AST parsing

            IBM Bob was used during *development* to help write code, tests, and documentation.
            The deployed app requires no external AI services, credentials, or API calls.

            ### Development Approach

            RepoQuest was built using:
            - ✅ Deterministic static analysis
            - ✅ Framework heuristics
            - ✅ Pattern matching
            - ✅ Simple ranked priorities
            - ❌ No runtime LLM calls
            - ❌ No vector databases
            - ❌ No embeddings
            - ❌ No external APIs

            This makes RepoQuest fast, predictable, and easy to audit.
            """)

            st.info("📁 Exported Bob task session reports will be placed in the `bob_sessions/` directory before final submission.")

    else:
        # Welcome message
        st.info("👈 Select a demo repo or upload a ZIP, then click 'Generate Onboarding Quest' to get started!")

        st.markdown("""
        ### What is RepoQuest?

        RepoQuest helps developers onboard to unfamiliar codebases by:

        - 🔍 **Scanning** the repository structure
        - 🏗️ **Detecting** frameworks and project types
        - 🗺️ **Mapping** architecture and dependencies
        - 📖 **Creating** a guided reading path
        - 🎯 **Generating** component cards with test ideas
        - 🎮 **Creating** onboarding quizzes
        - 📝 **Exporting** Markdown guides

        ### How It Works

        1. **Select Input:** Choose the bundled demo or upload your own ZIP
        2. **Generate Quest:** Click the button to analyze the repository
        3. **Explore Tabs:** Navigate through Overview, Architecture, Reading Path, Components, Tests, Quiz, Documentation, and Export
        4. **Download Guide:** Export a comprehensive Markdown onboarding document

        ### Security Features

        ZIP uploads are protected against:
        - 🛡️ Path traversal attacks (ZIP slip)
        - 🛡️ Absolute path injection
        - 🛡️ Oversized files (25 MB limit)
        - 🛡️ Binary file execution
        - 🛡️ Malicious code execution

        ### Technology

        RepoQuest uses **deterministic static analysis** - no runtime AI, no external APIs, no credentials required.
        """)


if __name__ == "__main__":
    main()

# Made with Bob