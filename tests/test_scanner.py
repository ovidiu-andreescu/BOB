"""Tests for repository scanner."""

import tempfile
import zipfile
from pathlib import Path

import pytest

from repoquest.scanner import (
  should_ignore_path,
  should_skip_file,
  should_skip_zip_entry,
  guess_file_role,
  scan_directory,
  scan_zip,
)
from repoquest.zip_safety import ZIPSafetyError
from repoquest.config import MAX_FILES_SCANNED, MAX_FILE_SIZE_BYTES


def test_should_ignore_path():
  """Test path ignore logic."""
  assert should_ignore_path("node_modules/package/file.js")
  assert should_ignore_path(".git/config")
  assert should_ignore_path("src/__pycache__/module.pyc")
  assert not should_ignore_path("src/main.py")
  assert not should_ignore_path("README.md")


def test_should_skip_file_binary():
  """Test that binary files are skipped."""
  with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
    tmp_path = Path(tmp.name)
    try:
      should_skip, reason = should_skip_file(tmp_path)
      assert should_skip
      assert "binary" in reason.lower()
    finally:
      tmp_path.unlink()


def test_should_skip_file_large():
  """Test that large files are skipped."""
  with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
    tmp_path = Path(tmp.name)
    try:
      # Write more than MAX_FILE_SIZE_BYTES
      tmp.write(b"x" * (MAX_FILE_SIZE_BYTES + 1000))
      tmp.flush()

      should_skip, reason = should_skip_file(tmp_path)
      assert should_skip
      assert "too large" in reason.lower()
    finally:
      tmp_path.unlink()


def test_should_skip_file_normal():
  """Test that normal files are not skipped."""
  with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as tmp:
    tmp_path = Path(tmp.name)
    try:
      tmp.write(b"print('hello')")
      tmp.flush()

      should_skip, reason = should_skip_file(tmp_path)
      assert not should_skip
      assert reason is None
    finally:
      tmp_path.unlink()


def test_should_skip_zip_entry_directory():
  """Test that directory entries are skipped."""
  should_skip, reason = should_skip_zip_entry("folder/", 0)
  assert should_skip
  assert "directory" in reason.lower()


def test_should_skip_zip_entry_binary():
  """Test that binary entries are skipped."""
  should_skip, reason = should_skip_zip_entry("image.png", 1000)
  assert should_skip
  assert "binary" in reason.lower()


def test_should_skip_zip_entry_large():
  """Test that large entries are skipped."""
  should_skip, reason = should_skip_zip_entry("large.txt", MAX_FILE_SIZE_BYTES + 1000)
  assert should_skip
  assert "too large" in reason.lower()


def test_should_skip_zip_entry_normal():
  """Test that normal entries are not skipped."""
  should_skip, reason = should_skip_zip_entry("file.py", 1000)
  assert not should_skip
  assert reason is None


def test_guess_file_role_documentation():
  """Test documentation file role detection."""
  assert guess_file_role(Path("README.md")) == "documentation"
  assert guess_file_role(Path("docs/README.txt")) == "documentation"


def test_guess_file_role_config():
  """Test config file role detection."""
  assert guess_file_role(Path("package.json")) == "config"
  assert guess_file_role(Path("requirements.txt")) == "config"
  assert guess_file_role(Path("pyproject.toml")) == "config"


def test_guess_file_role_entrypoint():
  """Test entrypoint file role detection."""
  assert guess_file_role(Path("main.py")) == "entrypoint"
  assert guess_file_role(Path("app.py")) == "entrypoint"
  assert guess_file_role(Path("src/App.tsx")) == "entrypoint"


def test_guess_file_role_test():
  """Test test file role detection."""
  assert guess_file_role(Path("test_scanner.py")) == "test"
  assert guess_file_role(Path("tests/test_utils.py")) == "test"


def test_guess_file_role_frontend_component():
  """Test frontend component role detection."""
  assert guess_file_role(Path("src/components/Button.tsx")) == "frontend_component"
  assert guess_file_role(Path("components/Card.jsx")) == "frontend_component"


def test_guess_file_role_frontend_page():
  """Test frontend page role detection."""
  assert guess_file_role(Path("src/pages/Home.tsx")) == "frontend_page"
  assert guess_file_role(Path("pages/About.jsx")) == "frontend_page"


def test_guess_file_role_backend_route():
  """Test backend route role detection."""
  assert guess_file_role(Path("routes/users.py")) == "backend_route"
  assert guess_file_role(Path("backend/routes/trips.py")) == "backend_route"


def test_guess_file_role_backend_service():
  """Test backend service role detection."""
  assert guess_file_role(Path("services/auth.py")) == "backend_service"
  assert guess_file_role(Path("backend/services/db.py")) == "backend_service"


def test_guess_file_role_api_client():
  """Test API client role detection."""
  assert guess_file_role(Path("services/api.ts")) == "api_client"
  assert guess_file_role(Path("src/api/client.js")) == "api_client"


def test_guess_file_role_model():
  """Test model role detection."""
  assert guess_file_role(Path("models/user.py")) == "model"
  assert guess_file_role(Path("backend/models/trip.py")) == "model"


def test_scan_directory_basic():
  """Test basic directory scanning."""
  with tempfile.TemporaryDirectory() as tmpdir:
    tmp_path = Path(tmpdir)

    # Create test files
    (tmp_path / "test.py").write_text("print('hello')")
    (tmp_path / "README.md").write_text("# Test")

    snapshot = scan_directory(tmp_path)

    assert snapshot.source_name == tmp_path.name
    assert snapshot.total_files_seen >= 2
    assert len(snapshot.files) >= 2
    assert not any(f.skipped for f in snapshot.files if f.name in ["test.py", "README.md"])


def test_scan_directory_ignores_folders():
  """Test that ignored folders are not scanned."""
  with tempfile.TemporaryDirectory() as tmpdir:
    tmp_path = Path(tmpdir)

    # Create files in ignored folder
    node_modules = tmp_path / "node_modules"
    node_modules.mkdir()
    (node_modules / "package.js").write_text("module.exports = {}")

    # Create normal file
    (tmp_path / "app.js").write_text("console.log('hello')")

    snapshot = scan_directory(tmp_path)

    # Should not include files from node_modules
    assert not any("node_modules" in f.path for f in snapshot.files)
    assert any(f.name == "app.js" for f in snapshot.files)


def test_scan_directory_skips_binary():
  """Test that binary files are marked as skipped."""
  with tempfile.TemporaryDirectory() as tmpdir:
    tmp_path = Path(tmpdir)

    # Create binary file
    (tmp_path / "image.png").write_bytes(b"\x89PNG\r\n\x1a\n")

    snapshot = scan_directory(tmp_path)

    png_files = [f for f in snapshot.files if f.name == "image.png"]
    assert len(png_files) == 1
    assert png_files[0].skipped
    assert "binary" in png_files[0].skip_reason.lower()


def test_scan_directory_file_limit():
  """Test that file scanning respects MAX_FILES_SCANNED limit."""
  with tempfile.TemporaryDirectory() as tmpdir:
    tmp_path = Path(tmpdir)

    # Create more files than the limit
    for i in range(MAX_FILES_SCANNED + 10):
      (tmp_path / f"file_{i}.txt").write_text(f"Content {i}")

    snapshot = scan_directory(tmp_path)

    assert snapshot.total_files_seen > MAX_FILES_SCANNED
    assert snapshot.total_files_scanned <= MAX_FILES_SCANNED
    assert len(snapshot.warnings) > 0
    assert any("max file limit" in w.lower() for w in snapshot.warnings)


def test_scan_zip_basic():
  """Test basic ZIP scanning."""
  with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
    tmp_path = Path(tmp.name)
    try:
      # Create a simple ZIP
      with zipfile.ZipFile(tmp_path, "w") as zf:
        zf.writestr("test.py", "print('hello')")
        zf.writestr("README.md", "# Test")

      snapshot = scan_zip(tmp_path)

      assert snapshot.source_name == tmp_path.name
      assert snapshot.total_files_seen >= 2
      assert len(snapshot.files) >= 2
      assert not any(f.skipped for f in snapshot.files if f.name in ["test.py", "README.md"])
    finally:
      tmp_path.unlink()


def test_scan_zip_ignores_folders():
  """Test that ZIP scanning ignores specified folders."""
  with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
    tmp_path = Path(tmp.name)
    try:
      with zipfile.ZipFile(tmp_path, "w") as zf:
        zf.writestr("node_modules/package.js", "module.exports = {}")
        zf.writestr("app.js", "console.log('hello')")

      snapshot = scan_zip(tmp_path)

      # Should not include files from node_modules
      assert not any("node_modules" in f.path for f in snapshot.files)
      assert any(f.name == "app.js" for f in snapshot.files)
    finally:
      tmp_path.unlink()


def test_scan_zip_skips_binary():
  """Test that ZIP scanning marks binary files as skipped."""
  with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
    tmp_path = Path(tmp.name)
    try:
      with zipfile.ZipFile(tmp_path, "w") as zf:
        zf.writestr("image.png", b"\x89PNG\r\n\x1a\n")

      snapshot = scan_zip(tmp_path)

      png_files = [f for f in snapshot.files if f.name == "image.png"]
      assert len(png_files) == 1
      assert png_files[0].skipped
      assert "binary" in png_files[0].skip_reason.lower()
    finally:
      tmp_path.unlink()


def test_scan_zip_rejects_unsafe_paths():
  """Test that ZIP scanning rejects unsafe paths."""
  with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
    tmp_path = Path(tmp.name)
    try:
      with zipfile.ZipFile(tmp_path, "w") as zf:
        zf.writestr("../etc/passwd", "malicious")

      with pytest.raises(ZIPSafetyError):
        scan_zip(tmp_path)
    finally:
      tmp_path.unlink()


def test_scan_zip_file_limit():
  """Test that ZIP scanning respects MAX_FILES_SCANNED limit."""
  with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
    tmp_path = Path(tmp.name)
    try:
      with zipfile.ZipFile(tmp_path, "w") as zf:
        for i in range(MAX_FILES_SCANNED + 10):
          zf.writestr(f"file_{i}.txt", f"Content {i}")

      snapshot = scan_zip(tmp_path)

      assert snapshot.total_files_seen > MAX_FILES_SCANNED
      assert snapshot.total_files_scanned <= MAX_FILES_SCANNED
      assert len(snapshot.warnings) > 0
      assert any("max file limit" in w.lower() for w in snapshot.warnings)
    finally:
      tmp_path.unlink()


def test_scan_zip_invalid_zip():
  """Test that invalid ZIP files are rejected gracefully."""
  with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
    tmp_path = Path(tmp.name)
    try:
      tmp.write(b"This is not a ZIP file")
      tmp.flush()

      with pytest.raises(ZIPSafetyError) as exc_info:
        scan_zip(tmp_path)
      assert " not a valid zip" in str(exc_info.value).lower()
    finally:
      tmp_path.unlink()

# Made with Bob
