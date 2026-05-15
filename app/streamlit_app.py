"""RepoQuest - Turn unfamiliar repos into guided onboarding journeys."""

import streamlit as st
import pandas as pd

from repoquest.sample_loader import load_demo_repo


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
                        st.success("✅ Repository scanned successfully!")
                    except Exception as e:
                        st.error(f"Error scanning repository: {e}")
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
        
        # Next steps placeholder
        st.markdown("---")
        st.info("🔮 **Coming Next:** Framework detection, route extraction, architecture maps, and more!")
        
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
        
        ### Current Checkpoint: File Inventory
        
        This checkpoint demonstrates:
        - ✅ Loading bundled demo repository
        - ✅ Safe file scanning with ignore rules
        - ✅ File role classification
        - ✅ Interactive file table
        - ✅ CSV export
        
        **Next checkpoint will add:** Framework detection for React/Vite and FastAPI!
        """)


if __name__ == "__main__":
    main()

# Made with Bob
