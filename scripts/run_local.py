#!/usr/bin/env python3
"""Launch RepoQuest locally."""

import subprocess
import sys
import os
from pathlib import Path


def main():
    """Run the Streamlit app locally with proper PYTHONPATH."""
    # Get the project root directory (parent of scripts/)
    project_root = Path(__file__).parent.parent.resolve()

    # Set PYTHONPATH to include project root so 'repoquest' module can be imported
    env = os.environ.copy()
    current_pythonpath = env.get("PYTHONPATH", "")
    if current_pythonpath:
        env["PYTHONPATH"] = f"{project_root}{os.pathsep}{current_pythonpath}"
    else:
        env["PYTHONPATH"] = str(project_root)

    try:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                "app/streamlit_app.py",
                "--server.maxUploadSize=25",
                "--server.runOnSave=true",
            ],
            check=True,
            env=env,
            cwd=project_root,
        )
    except KeyboardInterrupt:
        print("\nShutting down RepoQuest...")
    except subprocess.CalledProcessError as e:
        print(f"Error running Streamlit: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

# Made with Bob
