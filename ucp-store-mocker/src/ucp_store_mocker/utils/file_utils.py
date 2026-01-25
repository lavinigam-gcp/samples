"""File utility functions."""

import shutil
from pathlib import Path
from typing import Union


def ensure_dir(path: Union[str, Path]) -> Path:
    """Ensure a directory exists, creating it if necessary."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def copy_template(src: Path, dest: Path) -> None:
    """Copy a template file or directory."""
    if src.is_dir():
        shutil.copytree(src, dest, dirs_exist_ok=True)
    else:
        shutil.copy2(src, dest)


def write_file(path: Union[str, Path], content: str) -> Path:
    """Write content to a file, creating parent directories if needed."""
    path = Path(path)
    ensure_dir(path.parent)
    path.write_text(content)
    return path


def clean_directory(path: Union[str, Path]) -> None:
    """Remove all contents of a directory."""
    path = Path(path)
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)
