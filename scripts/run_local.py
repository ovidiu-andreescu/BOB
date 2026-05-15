#!/usr/bin/env python3
"""Launch RepoQuest locally."""

import subprocess
import sys


def main():
    """Run the Streamlit app locally."""
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
        )
    except KeyboardInterrupt:
        print("\nShutting down RepoQuest...")
    except subprocess.CalledProcessError as e:
        print(f"Error running Streamlit: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

# Made with Bob
