"""RepoQuest - Turn unfamiliar repos into guided onboarding journeys."""

import streamlit as st
import pandas as pd
import os

from repoquest.sample_loader import load_demo_repo
from repoquest.route_extractors import extract_all_routes
from repoquest.import_graph import build_import_graph
from repoquest.architecture import (
    generate_architecture_map,
    generate_dependency_graph,
    generate_simple_graph
)


def main():
    st.set_page_config(
        page_title="RepoQuest",
        page_icon="🗺️",
        layout="wide",
    )

    # Header
    st.title("🗺️ RepoQuest")
    st.markdown("Turn an unfamiliar repo into a guided onboarding journey")

    # Sidebar
    with st.sidebar:
        st.header("Input Source")

        input_mode = st.radio(
            "Choose input:",
            ["Use demo repo", "Upload ZIP (coming soon)"],
            help="Select how to provide the repository"
        )

        st.markdown("---")

        if st.button("🚀 Generate Onboarding Quest", type="primary", use_container_width=True):
            if input_mode == "Use demo repo":
                with st.spinner("Scanning demo repository..."):
                    try:
                        snapshot = load_demo_repo()
                        st.session_state["snapshot"] = snapshot

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

                        st.success("✅ Repository analyzed successfully!")
                    except Exception as e:
                        st.error(f"Error analyzing repository: {e}")
                        import traceback
                        st.code(traceback.format_exc())
            else:
                st.info("ZIP upload coming in next checkpoint!")

    # Main content
    if "snapshot" in st.session_state:
        snapshot = st.session_state["snapshot"]

        st.header("📊 Repository Scan Results")

        # Summary metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Files Seen", snapshot.total_files_seen)
        with col2:
            st.metric("Files Scanned", snapshot.total_files_scanned)
        with col3:
            scanned_files = [f for f in snapshot.files if not f.skipped]
            st.metric("Analyzed Files", len(scanned_files))

        # Warnings
        if snapshot.warnings:
            for warning in snapshot.warnings:
                st.warning(warning)

        # File inventory table
        st.subheader("📁 File Inventory")

        # Prepare data for table
        table_data = []
        for file in snapshot.files:
            if not file.skipped:
                table_data.append({
                    "Path": file.path,
                    "Extension": file.suffix or "none",
                    "Language": file.language,
                    "Role": file.role,
                    "Size (bytes)": file.size_bytes,
                    "Lines": file.line_count,
                })

        if table_data:
            df = pd.DataFrame(table_data)
            st.dataframe(
                df,
                use_container_width=True,
                height=400,
            )

            # Download CSV
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download as CSV",
                data=csv,
                file_name=f"{snapshot.source_name}_inventory.csv",
                mime="text/csv",
            )
        else:
            st.info("No files to display")

        # Architecture Map Section
        if "arch_map" in st.session_state:
            st.markdown("---")
            st.header("🏗️ Architecture Map")

            st.markdown("""
            This human-friendly map shows the high-level structure of the application,
            highlighting key components and their relationships.

            **Note:** Dashed edge indicates frontend API calls into backend routes.
            """)

            try:
                st.graphviz_chart(st.session_state["arch_map"])
            except Exception as e:
                st.error(f"Error rendering architecture map: {e}")

        # Dependency Graph Section
        if "dep_graph" in st.session_state:
            st.markdown("---")
            st.header("🔗 Dependency Graph")

            st.markdown("""
            This technical graph shows actual import relationships between files in the repository.
            """)

            try:
                st.graphviz_chart(st.session_state["dep_graph"])
            except Exception as e:
                st.error(f"Error rendering dependency graph: {e}")

        # Detected Routes Section
        if "routes" in st.session_state:
            routes = st.session_state["routes"]

            if routes:
                st.markdown("---")
                st.header("🛣️ Detected API Routes")

                st.markdown(f"Found **{len(routes)}** API endpoints in the repository:")

                # Create routes table
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

        # Import Statistics
        if "import_edges" in st.session_state:
            edges = st.session_state["import_edges"]

            if edges:
                st.markdown("---")
                st.header("📊 Import Statistics")

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Imports", len(edges))
                with col2:
                    python_imports = len([e for e in edges if e.kind == "python_import"])
                    st.metric("Python Imports", python_imports)
                with col3:
                    js_imports = len([e for e in edges if e.kind in ["js_import", "ts_import"]])
                    st.metric("JS/TS Imports", js_imports)

    else:
        # Welcome message
        st.info("👈 Select a demo repo and click 'Generate Onboarding Quest' to get started!")

        st.markdown("""
        ### What is RepoQuest?

        RepoQuest helps developers onboard to unfamiliar codebases by:

        - 🔍 **Scanning** the repository structure
        - 🏗️ **Detecting** frameworks and project types
        - 🗺️ **Mapping** architecture and dependencies
        - 📖 **Creating** a guided reading path
        - ✅ **Generating** onboarding quizzes
        - 📝 **Exporting** Markdown guides

        ### Current Checkpoint: Architecture & Routes

        This checkpoint demonstrates:
        - ✅ Loading bundled demo repository
        - ✅ Safe file scanning with ignore rules
        - ✅ File role classification
        - ✅ FastAPI route extraction
        - ✅ Python import parsing with AST
        - ✅ JS/TS import parsing with regex
        - ✅ Architecture map generation
        - ✅ Dependency graph visualization
        - ✅ Interactive file and route tables

        **Next checkpoint will add:** Reading path, component cards, and quiz generation!
        """)


if __name__ == "__main__":
    main()

# Made with Bob
