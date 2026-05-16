"""Tests for ZIP safety validation."""

import tempfile
import zipfile
from pathlib import Path

import pytest

from repoquest.zip_safety import (
  validate_zip_size,
  is_safe_zip_path,
  validate_zip_entry_path,
  validate_zip_file,
  safe_read_zip_entry,
  ZIPSafetyError,
)
from repoquest.config import MAX_ZIP_SIZE_MB


def test_is_safe_zip_path_normal():
  """Test that normal paths are considered safe."""
  is_safe, reason = is_safe_zip_path("folder/file.txt")
  assert is_safe
  assert reason is None

  is_safe, reason = is_safe_zip_path("README.md")
  assert is_safe
  assert reason is None


def test_is_safe_zip_path_rejects_absolute():
  """Test that absolute paths are rejected."""
  is_safe, reason = is_safe_zip_path("/etc/passwd")
  assert not is_safe
  assert "absolute" in reason.lower()


def test_is_safe_zip_path_rejects_parent_traversal():
  """Test that parent directory traversal is rejected."""
  is_safe, reason = is_safe_zip_path("../etc/passwd")
  assert not is_safe
  assert ".." in reason.lower()

  is_safe, reason = is_safe_zip_path("folder/../../etc/passwd")
  assert not is_safe
  assert ".." in reason.lower()


def test_is_safe_zip_path_rejects_normalized_escape():
  """Test that normalized paths that escape are rejected."""
  is_safe, reason = is_safe_zip_path("folder/../../../etc/passwd")
  assert not is_safe


def test_validate_zip_entry_path_normal():
  """Test that normal paths pass validation."""
  with tempfile.TemporaryDirectory() as tmpdir:
    target = Path(tmpdir)
    # Should not raise
    validate_zip_entry_path("folder/file.txt", target)
    validate_zip_entry_path("README.md", target)


def test_validate_zip_entry_path_rejects_escape():
  """Test that paths escaping target directory are rejected."""
  with tempfile.TemporaryDirectory() as tmpdir:
    target = Path(tmpdir)

    with pytest.raises(ZIPSafetyError) as exc_info:
      validate_zip_entry_path("../etc/passwd", target)
    assert " not allowed" in str(exc_info.value).lower()


def test_validate_zip_entry_path_rejects_absolute():
  """Test that absolute paths are rejected."""
  with tempfile.TemporaryDirectory() as tmpdir:
    target = Path(tmpdir)

    with pytest.raises(ZIPSafetyError) as exc_info:
      validate_zip_entry_path("/etc/passwd", target)
    assert "absolute" in str(exc_info.value).lower()


def test_validate_zip_size_normal():
  """Test that normal-sized ZIPs pass validation."""
  with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
    tmp_path = Path(tmp.name)
    try:
      # Create a small ZIP
      with zipfile.ZipFile(tmp_path, "w") as zf:
        zf.writestr("test.txt", "Hello, World!")

      # Should not raise
      validate_zip_size(tmp_path)
    finally:
      tmp_path.unlink()


def test_validate_zip_size_rejects_large():
  """Test that oversized ZIPs are rejected."""
  with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
    tmp_path = Path(tmp.name)
    try:
      # Create a ZIP larger than the limit
      with zipfile.ZipFile(tmp_path, "w") as zf:
        # Write enough data to exceed MAX_ZIP_SIZE_MB
        large_data = "x" * (MAX_ZIP_SIZE_MB * 1024 * 1024 + 1000)
        zf.writestr("large.txt", large_data)

      with pytest.raises(ZIPSafetyError) as exc_info:
        validate_zip_size(tmp_path)
      assert "too large" in str(exc_info.value).lower()
    finally:
      tmp_path.unlink()


def test_validate_zip_file_normal():
  """Test that a normal ZIP passes full validation."""
  with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
    tmp_path = Path(tmp.name)
    try:
      # Create a valid ZIP with safe paths
      with zipfile.ZipFile(tmp_path, "w") as zf:
        zf.writestr("folder/file.txt", "Content")
        zf.writestr("README.md", "# Test")

      # Should not raise
      validate_zip_file(tmp_path)
    finally:
      tmp_path.unlink()


def test_validate_zip_file_rejects_unsafe_paths():
  """Test that ZIPs with unsafe paths are rejected."""
  with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
    tmp_path = Path(tmp.name)
    try:
      # Create a ZIP with path traversal
      with zipfile.ZipFile(tmp_path, "w") as zf:
        zf.writestr("../etc/passwd", "malicious")

      with pytest.raises(ZIPSafetyError) as exc_info:
        validate_zip_file(tmp_path)
      assert " not allowed" in str(exc_info.value).lower() or "escape" in str(exc_info.value).lower()
    finally:
      tmp_path.unlink()


def test_validate_zip_file_rejects_invalid_zip():
  """Test that invalid ZIP files are rejected."""
  with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
    tmp_path = Path(tmp.name)
    try:
      # Write non-ZIP content
      tmp.write(b"This is not a ZIP file")
      tmp.flush()

      with pytest.raises(ZIPSafetyError) as exc_info:
        validate_zip_file(tmp_path)
      assert " not a valid zip" in str(exc_info.value).lower()
    finally:
      tmp_path.unlink()


def test_safe_read_zip_entry_normal():
  """Test reading a normal ZIP entry."""
  with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
    tmp_path = Path(tmp.name)
    try:
      content = b"Hello, World!"
      with zipfile.ZipFile(tmp_path, "w") as zf:
        zf.writestr("test.txt", content)

      with zipfile.ZipFile(tmp_path, "r") as zf:
        result = safe_read_zip_entry(zf, "test.txt", 1024)
        assert result == content
    finally:
      tmp_path.unlink()


def test_safe_read_zip_entry_rejects_large():
  """Test that oversized entries are rejected."""
  with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
    tmp_path = Path(tmp.name)
    try:
      large_content = b"x" * 10000
      with zipfile.ZipFile(tmp_path, "w") as zf:
        zf.writestr("large.txt", large_content)

      with zipfile.ZipFile(tmp_path, "r") as zf:
        with pytest.raises(ZIPSafetyError) as exc_info:
          safe_read_zip_entry(zf, "large.txt", 100)
        assert "too large" in str(exc_info.value).lower()
    finally:
      tmp_path.unlink()


def test_safe_read_zip_entry_missing():
  """Test reading a non-existent entry."""
  with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
    tmp_path = Path(tmp.name)
    try:
      with zipfile.ZipFile(tmp_path, "w") as zf:
        zf.writestr("exists.txt", "content")

      with zipfile.ZipFile(tmp_path, "r") as zf:
        with pytest.raises(ZIPSafetyError) as exc_info:
          safe_read_zip_entry(zf, "missing.txt", 1024)
        assert " not found" in str(exc_info.value).lower()
    finally:
      tmp_path.unlink()


def test_zip_slip_attack_prevention():
  """Test that ZIP slip attacks are prevented."""
  with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
    tmp_path = Path(tmp.name)
    try:
      # Create a malicious ZIP with various path traversal attempts
      with zipfile.ZipFile(tmp_path, "w") as zf:
        zf.writestr("../../etc/passwd", "malicious")

      with pytest.raises(ZIPSafetyError):
        validate_zip_file(tmp_path)
    finally:
      tmp_path.unlink()

# Made with Bob
