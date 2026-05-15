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

        if st.button(
            "🚀 Generate Onboarding Quest",
            type="primary",
            use_container_width=True,
            disabled=generate_disabled
        ):
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

                        if edges:
                            dep_graph = generate_dependency_graph(snapshot.files, edges)
                        else:
                            dep_graph = generate_simple_graph(snapshot.files)
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
                except Exception as e:
                    st.error(f"Error analyzing repository: {e}")
                    import traceback
                    with st.expander("Show error details"):
                        st.code(traceback.format_exc())

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
            "🎮 Quest & Quiz",
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

            if "arch_map" in st.session_state:
                st.markdown("""
                This human-friendly map shows the high-level structure of the application,
                highlighting key components and their relationships.
                """)

                try:
                    st.graphviz_chart(st.session_state["arch_map"])
                except Exception as e:
                    st.error(f"Error rendering architecture map: {e}")

            st.markdown("---")
            st.subheader("🔗 Dependency Graph")

            if "dep_graph" in st.session_state:
                st.markdown("""
                This technical graph shows actual import relationships between files in the repository.
                """)

                try:
                    st.graphviz_chart(st.session_state["dep_graph"])
                except Exception as e:
                    st.error(f"Error rendering dependency graph: {e}")

            # Detected Routes
            if "routes" in st.session_state:
                routes = st.session_state["routes"]

                if routes:
                    st.markdown("---")
                    st.subheader("🛣️ Detected API Routes")

                    st.markdown(f"Found **{len(routes)}** API endpoints:")

                    routes_data = []
                    for route in routes:
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
                            st.markdown(f"**Why read this:**")
                            st.markdown(item.reason)
                else:
                    st.warning("No reading path generated")
            else:
                st.info("Generate an onboarding quest to see the reading path")

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
                            st.markdown(f"**{card.role}**")
                            st.markdown(f"*{card.why_it_matters}*")

                            if card.detected_items:
                                st.markdown("**Detected items:**")
                                for item in card.detected_items:
                                    st.markdown(f"- {item}")

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
                st.info("Generate an onboarding quest to see component cards")

        # Tab 5: Quest & Quiz
        with tabs[4]:
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
                st.info("Generate an onboarding quest to see the quiz")

        # Tab 6: Export
        with tabs[5]:
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
                # Generate markdown report
                markdown_content = generate_markdown_report(
                    st.session_state["snapshot"],
                    st.session_state["fingerprint"],
                    st.session_state.get("routes", []),
                    st.session_state.get("reading_path", []),
                    st.session_state.get("component_cards", []),
                    st.session_state.get("quiz", [])
                )

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
                st.info("Generate an onboarding quest to export the guide")

        # Tab 7: Built with IBM Bob
        with tabs[6]:
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
        3. **Explore Tabs:** Navigate through Overview, Architecture, Reading Path, Components, Quiz, and Export
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


def generate_markdown_report(snapshot, fingerprint, routes, reading_path, component_cards, quiz):
    """Generate a Markdown onboarding guide."""
    lines = []
    
    lines.append(f"# RepoQuest Onboarding Guide")
    lines.append(f"")
    lines.append(f"**Repository:** {snapshot.source_name}")
    lines.append(f"")
    
    # Summary
    lines.append(f"## Summary")
    lines.append(f"")
    lines.append(f"**Project Type:** {fingerprint.project_type}")
    lines.append(f"**Confidence:** {fingerprint.confidence * 100:.0f}%")
    lines.append(f"")
    lines.append(fingerprint.summary)
    lines.append(f"")
    
    # Frameworks
    if fingerprint.frameworks:
        lines.append(f"## Detected Frameworks")
        lines.append(f"")
        for framework in fingerprint.frameworks:
            lines.append(f"### {framework.name} ({framework.category})")
            lines.append(f"")
            lines.append(f"**Confidence:** {framework.confidence * 100:.0f}%")
            lines.append(f"")
            lines.append(f"**Evidence:**")
            for evidence in framework.evidence:
                lines.append(f"- {evidence}")
            lines.append(f"")
    
    # Entry points
    if fingerprint.entry_points:
        lines.append(f"## Key Entry Points")
        lines.append(f"")
        for entry_point in fingerprint.entry_points:
            lines.append(f"- `{entry_point}`")
        lines.append(f"")
    
    # Routes
    if routes:
        lines.append(f"## Detected Routes")
        lines.append(f"")
        for route in routes:
            func_name = f" ({route.function_name})" if route.function_name else ""
            lines.append(f"- **{route.method} {route.path}** → `{route.file_path}`{func_name}")
        lines.append(f"")
    
    # Reading path
    if reading_path:
        lines.append(f"## 30-Minute Reading Path")
        lines.append(f"")
        total_minutes = sum(item.estimated_minutes for item in reading_path)
        lines.append(f"Suggested reading order (~{total_minutes} minutes):")
        lines.append(f"")
        for item in reading_path:
            lines.append(f"### {item.order}. {item.path} ({item.estimated_minutes} min)")
            lines.append(f"")
            lines.append(item.reason)
            lines.append(f"")
    
    # Component cards
    if component_cards:
        lines.append(f"## Component Cards")
        lines.append(f"")
        for card in component_cards:
            lines.append(f"### {card.title}")
            lines.append(f"")
            lines.append(f"**Path:** `{card.path}`")
            lines.append(f"")
            lines.append(f"**{card.role}**")
            lines.append(f"")
            lines.append(card.why_it_matters)
            lines.append(f"")
            
            if card.detected_items:
                lines.append(f"**Detected items:**")
                for item in card.detected_items:
                    lines.append(f"- {item}")
                lines.append(f"")
            
            if card.connected_to:
                lines.append(f"**Connected to:**")
                for conn in card.connected_to:
                    lines.append(f"- `{conn}`")
                lines.append(f"")
            
            if card.suggested_test_ideas:
                lines.append(f"**Suggested test ideas:**")
                for idea in card.suggested_test_ideas:
                    lines.append(f"- {idea}")
                lines.append(f"")
            
            lines.append(f"**IBM Bob prompt:**")
            lines.append(f"```")
            lines.append(card.suggested_bob_prompt)
            lines.append(f"```")
            lines.append(f"")
    
    # Quiz
    if quiz:
        lines.append(f"## Quiz Questions")
        lines.append(f"")
        for i, q in enumerate(quiz, 1):
            lines.append(f"### Question {i}")
            lines.append(f"")
            lines.append(q.question)
            lines.append(f"")
            for opt in q.options:
                lines.append(f"- {opt}")
            lines.append(f"")
            lines.append(f"**Correct answer:** {q.correct_answer}")
            lines.append(f"")
            lines.append(f"**Explanation:** {q.explanation}")
            lines.append(f"")
    
    # Warnings
    if fingerprint.warnings:
        lines.append(f"## Warnings and Limitations")
        lines.append(f"")
        for warning in fingerprint.warnings:
            lines.append(f"- {warning}")
        lines.append(f"")
    
    return "\n".join(lines)


if __name__ == "__main__":
    main()

# Made with Bob
