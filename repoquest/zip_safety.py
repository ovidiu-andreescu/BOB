"""ZIP file safety validation for RepoQuest."""

import os
import zipfile
from pathlib import Path

from repoquest.config import MAX_ZIP_SIZE_MB


class ZIPSafetyError(Exception):
  """Raised when a ZIP file fails safety validation."""
  pass


def validate_zip_size(zip_path: Path) -> None:
  """Validate that a ZIP file is not too large.

  Args:
    zip_path: Path to the ZIP file

  Raises:
    ZIPSafetyError: If the ZIP is larger than MAX_ZIP_SIZE_MB
  """
  size_bytes = zip_path.stat().st_size
  size_mb = size_bytes / (1024 * 1024)

  if size_mb > MAX_ZIP_SIZE_MB:
    raise ZIPSafetyError(
      f"ZIP file is too large: {size_mb:.1f} MB (max: {MAX_ZIP_SIZE_MB} MB)"
    )


def is_safe_zip_path(zip_entry_name: str) -> tuple[bool, str | None]:
  """Check if a ZIP entry path is safe to process.

  Args:
    zip_entry_name: The name/path of the ZIP entry

  Returns:
    Tuple of (is_safe, reason). If not safe, reason explains why.
  """
  # Reject absolute paths
  if os.path.isabs(zip_entry_name):
    return False, "Absolute path not allowed"

  # Reject paths containing..
  if ".." in zip_entry_name:
    return False, "Path traversal (..) not allowed"

  # Normalize and check for path traversal
  normalized = os.path.normpath(zip_entry_name)
  if normalized.startswith("..") or normalized.startswith("/"):
    return False, "Path would escape target directory"

  return True, None


def validate_zip_entry_path(zip_entry_name: str, target_dir: Path) -> None:
  """Validate that a ZIP entry path is safe and won't escape target directory.

  Args:
    zip_entry_name: The name/path of the ZIP entry
    target_dir: The target directory where extraction would occur

  Raises:
    ZIPSafetyError: If the path is unsafe
  """
  is_safe, reason = is_safe_zip_path(zip_entry_name)
  if not is_safe:
    raise ZIPSafetyError(f"Unsafe ZIP entry path '{zip_entry_name}': {reason}")

  # Additional check: verify resolved path stays within target
  try:
    resolved = (target_dir / zip_entry_name).resolve()
    target_resolved = target_dir.resolve()

    # Check if resolved path is within target directory
    try:
      resolved.relative_to(target_resolved)
    except ValueError:
      raise ZIPSafetyError(
        f"ZIP entry '{zip_entry_name}' would escape target directory"
      )
  except Exception as e:
    raise ZIPSafetyError(f"Cannot validate ZIP entry path '{zip_entry_name}': {e}")


def validate_zip_file(zip_path: Path) -> None:
  """Perform comprehensive safety validation on a ZIP file.

  Args:
    zip_path: Path to the ZIP file

  Raises:
    ZIPSafetyError: If the ZIP fails any safety check
  """
  # Check file size
  validate_zip_size(zip_path)

  # Check if it's a valid ZIP
  if not zipfile.is_zipfile(zip_path):
    raise ZIPSafetyError("File is not a valid ZIP archive")

  # Validate all entry paths
  try:
    with zipfile.ZipFile(zip_path, "r") as zf:
      for entry in zf.namelist():
        # Use a dummy target dir for validation
        validate_zip_entry_path(entry, Path("/tmp/dummy"))
  except zipfile.BadZipFile as e:
    raise ZIPSafetyError(f"Corrupted ZIP file: {e}")
  except Exception as e:
    if isinstance(e, ZIPSafetyError):
      raise
    raise ZIPSafetyError(f"ZIP validation failed: {e}")


def safe_read_zip_entry(zf: zipfile.ZipFile, entry_name: str, max_size: int) -> bytes:
  """Safely read a ZIP entry with size limit.

  Args:
    zf: Open ZipFile object
    entry_name: Name of the entry to read
    max_size: Maximum bytes to read

  Returns:
    The entry content as bytes

  Raises:
    ZIPSafetyError: If the entry is too large or cannot be read
  """
  try:
    info = zf.getinfo(entry_name)

    # Check uncompressed size
    if info.file_size > max_size:
      raise ZIPSafetyError(
        f"ZIP entry '{entry_name}' is too large: {info.file_size} bytes"
      )

    # Read with size limit
    with zf.open(entry_name) as f:
      return f.read(max_size)
  except KeyError:
    raise ZIPSafetyError(f"ZIP entry '{entry_name}' not found")
  except Exception as e:
    if isinstance(e, ZIPSafetyError):
      raise
    raise ZIPSafetyError(f"Cannot read ZIP entry '{entry_name}': {e}")

# Made with Bob
