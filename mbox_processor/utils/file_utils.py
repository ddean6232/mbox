"""File utility functions for the MBOX processor."""
import hashlib
import logging
import os
import re
from pathlib import Path
from typing import Optional, Union

logger = logging.getLogger(__name__)

def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """Sanitize a filename to be filesystem-safe.
    
    Args:
        filename: The original filename
        max_length: Maximum length of the filename
        
    Returns:
        Sanitized filename
    """
    if not filename:
        return 'unnamed_file'
    
    # Replace invalid characters with underscore
    filename = re.sub(r'[\\/*?:"<>|]', '_', filename)
    
    # Remove control characters
    filename = ''.join(c for c in filename if ord(c) >= 32 or c in (' ', '.', '-', '_'))
    
    # Ensure the filename isn't too long
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        name = name[:max_length - len(ext) - 1]
        filename = f"{name}{ext}"
    
    return filename

def ensure_directory(directory: Union[str, Path]) -> Path:
    """Ensure a directory exists, creating it if necessary.
    
    Args:
        directory: Path to the directory
        
    Returns:
        Path object for the directory
    """
    path = Path(directory).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_file_hash(filepath: Union[str, Path], algorithm: str = 'sha256') -> str:
    """Calculate the hash of a file.
    
    Args:
        filepath: Path to the file
        algorithm: Hash algorithm to use (default: sha256)
        
    Returns:
        Hex digest of the file hash
    """
    filepath = Path(filepath)
    if not filepath.is_file():
        raise FileNotFoundError(f"File not found: {filepath}")
    
    hash_func = getattr(hashlib, algorithm, None)
    if not hash_func:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")
    
    h = hash_func()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    
    return h.hexdigest()

def get_file_size(filepath: Union[str, Path]) -> int:
    """Get the size of a file in bytes.
    
    Args:
        filepath: Path to the file
        
    Returns:
        Size of the file in bytes
    """
    filepath = Path(filepath)
    if not filepath.is_file():
        raise FileNotFoundError(f"File not found: {filepath}")
    
    return filepath.stat().st_size
