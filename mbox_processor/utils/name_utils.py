"""Name and email utility functions for the MBOX processor."""
import re
from typing import Optional, Tuple

def get_safe_filename(
    original_name: str,
    prefix: str = "",
    suffix: str = "",
    max_length: int = 255
) -> str:
    """Generate a safe filename with optional prefix and suffix.
    
    Args:
        original_name: Original filename
        prefix: Optional prefix to add
        suffix: Optional suffix to add before extension
        max_length: Maximum length of the filename
        
    Returns:
        Safe filename with prefix and suffix
    """
    # Remove directory path if present
    name = original_name.split('/')[-1].split('\\')[-1]
    
    # Split into name and extension
    name_parts = name.rsplit('.', 1)
    if len(name_parts) == 2 and name_parts[1]:
        base_name, ext = name_parts
        ext = f".{ext}"
    else:
        base_name = name_parts[0]
        ext = ""
    
    # Apply prefix and suffix
    safe_name = f"{prefix}{base_name}{suffix}{ext}"
    
    # Remove invalid characters
    safe_name = re.sub(r'[\\/*?:"<>|]', '_', safe_name)
    
    # Limit length
    if len(safe_name) > max_length:
        # Keep extension if present
        if ext:
            base = safe_name[:-len(ext)]
            safe_name = base[:(max_length - len(ext))] + ext
        else:
            safe_name = safe_name[:max_length]
    
    return safe_name

def extract_email_address(email_str: str) -> Tuple[Optional[str], Optional[str]]:
    """Extract name and email address from a string.
    
    Args:
        email_str: String containing name and email (e.g., "John Doe <john@example.com>")
        
    Returns:
        Tuple of (name, email) or (None, None) if no email found
    """
    if not email_str:
        return None, None
    
    # Try to match "Name <email@example.com>" format
    match = re.match(r'^\s*(.*?)\s*<([^>]+)>\s*$', email_str)
    if match:
        name, email = match.groups()
        name = name.strip('"\'').strip() or None
        return name, email.strip()
    
    # Try to match just an email address
    email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', email_str)
    if email_match:
        return None, email_match.group(0)
    
    return None, None

def format_sender_name(name: str, email: str) -> str:
    """Format a sender's name and email address.
    
    Args:
        name: Sender's name (optional)
        email: Sender's email address
        
    Returns:
        Formatted string (e.g., "John Doe <john@example.com>" or "john@example.com")
    """
    if not email:
        return ""
    
    if not name or name == email:
        return email
    
    # If the name is already in the format "name <email>" or is just an email
    if '@' in name and ('<' in name or '>' in name):
        return name
    
    return f'"{name}" <{email}>'
