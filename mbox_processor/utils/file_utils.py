"""File utility functions for the MBOX processor."""
import hashlib
import logging
import os
import re
import magic
import shutil
import traceback
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

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


def detect_file_type(filepath: Union[str, Path]) -> Tuple[str, str]:
    """Detect the MIME type and extension of a file.
    
    Args:
        filepath: Path to the file
        
    Returns:
        Tuple of (mime_type, extension)
    """
    filepath = Path(filepath)
    if not filepath.is_file():
        raise FileNotFoundError(f"File not found: {filepath}")
    
    try:
        mime = magic.Magic(mime=True)
        mime_type = mime.from_file(str(filepath))
        
        # Map common MIME types to extensions
        mime_to_ext = {
            'application/pdf': '.pdf',
            'image/jpeg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'application/msword': '.doc',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
            'application/vnd.ms-excel': '.xls',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
            'application/vnd.ms-powerpoint': '.ppt',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation': '.pptx',
            'text/plain': '.txt',
            'text/csv': '.csv',
            'application/zip': '.zip',
            'application/x-rar-compressed': '.rar',
            'application/x-7z-compressed': '.7z',
            'application/x-tar': '.tar',
            'application/gzip': '.gz',
        }
        
        extension = mime_to_ext.get(mime_type, '')
        return mime_type, extension
    except Exception as e:
        logger.warning(f"Could not detect file type for {filepath}: {e}")
        return 'application/octet-stream', ''


def process_extensionless_files(temp_dir: Path, attachments_dir: Path) -> Dict[str, str]:
    """Process files without extensions to detect their types and add extensions.
    
    Args:
        temp_dir: Directory containing files without extensions
        attachments_dir: Base directory for attachments
        
    Returns:
        Dictionary mapping original paths to new paths with extensions
    """
    results = {}
    
    if not temp_dir.exists():
        logger.debug("Temporary directory does not exist: %s", temp_dir)
        return results
    
    # Get all files in temp directory
    files_to_process = list(temp_dir.glob('**/*'))
    logger.debug("Found %d files to process in %s", len(files_to_process), temp_dir)
    
    for filepath in files_to_process:
        if not filepath.is_file():
            logger.debug("Skipping non-file: %s", filepath)
            continue
            
        # Skip files that already have extensions (shouldn't happen, but just in case)
        if filepath.suffix and len(filepath.suffix) <= 6:  # Allow up to 6-char extensions
            logger.debug("Skipping file with extension: %s", filepath)
            continue
            
        try:
            file_size = filepath.stat().st_size
            logger.debug("Processing file: %s (size: %d bytes)", filepath.name, file_size)
            
            # Detect file type
            mime_type, extension = detect_file_type(filepath)
            
            if not extension:
                logger.warning(
                    "Could not determine extension for %s (MIME: %s, size: %d bytes). "
                    "Leaving in temp directory.", 
                    filepath.name, mime_type, file_size
                )
                continue
                
            # Create new filename with extension
            new_filename = filepath.name + extension.lower()
            
            # Determine the target directory based on the sender's email
            sender_dir = filepath.parent.name
            target_dir = attachments_dir / sender_dir
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # Create new path and move the file
            new_path = target_dir / new_filename
            
            # Handle filename collisions
            counter = 1
            while new_path.exists():
                new_filename = f"{filepath.stem}_{counter}{extension}"
                new_path = target_dir / new_filename
                counter += 1
            
            # Log the move operation
            logger.info(
                "Moving %s -> %s (detected as %s, %d bytes)",
                filepath.name, new_path.name, mime_type, file_size
            )
                
            # Move the file to its new location
            shutil.move(str(filepath), str(new_path))
            results[str(filepath)] = str(new_path)
            
            # Verify the file was moved successfully
            if new_path.exists() and new_path.stat().st_size == file_size:
                logger.debug("Successfully moved %s to %s", filepath.name, new_path)
            else:
                logger.warning(
                    "Possible issue moving %s. Original size: %d, new size: %d",
                    filepath.name, file_size, new_path.stat().st_size if new_path.exists() else 0
                )
            
        except Exception as e:
            logger.error(
                "Error processing %s: %s\n%s",
                filepath, str(e), traceback.format_exc(),
                exc_info=False  # Don't log the traceback again
            )
    
    logger.debug("Processed %d files, %d successfully", len(files_to_process), len(results))
    return results
