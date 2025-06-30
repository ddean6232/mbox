"""Attachment model for the MBOX processor."""
from dataclasses import dataclass
import random
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Union, BinaryIO
import hashlib
import os

@dataclass
class Attachment:
    """Represents an email attachment."""
    
    content_id: str
    filename: str
    content_type: str
    content_disposition: str
    payload: bytes
    size: int
    
    # These will be set during processing
    saved_path: Optional[Path] = None
    message_id: Optional[str] = None
    email_date: Optional[datetime] = None
    sender_email: Optional[str] = None
    
    @property
    def extension(self) -> str:
        """Get the file extension in lowercase.
        
        Returns:
            File extension including the dot (e.g., '.pdf'), or empty string if no extension
        """
        if not self.filename:
            return ""
            
        # Get extension from filename
        return Path(self.filename).suffix.lower()
        
    def has_extension(self) -> bool:
        """Check if the attachment has a file extension.
        
        Returns:
            True if the filename has an extension, False otherwise
        """
        if not self.filename:
            return False
            
        # Check if there's at least one dot and the part after the last dot is 1-10 chars long
        parts = self.filename.rsplit('.', 1)
        if len(parts) < 2:
            return False
            
        extension = parts[1].lower()
        return 1 <= len(extension) <= 10 and extension.isalnum()
    
    @property
    def safe_filename(self) -> str:
        """Generate a safe filename for the attachment.
        
        Returns:
            A safe filename in the format: {YYYY-MM-DD}_{sanitized_sender_email}_{random_5_digits}.{ext}
            Example: 2025-06-30_john_doe_example_com_12345.pdf
            
        Raises:
            ValueError: If email_date or sender_email is not set
        """
        if not all([self.email_date, self.sender_email]):
            raise ValueError("email_date and sender_email must be set")
            
        # Extract email from format: "John Doe <john@example.com>"
        email_match = re.search(r'<([^>]+)>', self.sender_email)
        if email_match:
            sender = email_match.group(1)  # Extract email from <>
        else:
            sender = self.sender_email  # Use as is if no <>
            
        # Sanitize sender email
        safe_email = (
            sender
            .split('@')[0]  # Take only the part before @
            .replace('.', '_')
            .replace('+', '_')
            .lower()  # Ensure consistent case
        )
        
        # Get domain if available
        if '@' in sender:
            domain = sender.split('@')[1].split('>')[0]  # Handle trailing > if present
            safe_email = f"{safe_email}_{domain.replace('.', '_')}"
        
        # Generate random 5-digit number
        random_suffix = str(random.randint(10000, 99999))
        
        # Format date as YYYY-MM-DD
        date_str = self.email_date.strftime('%Y-%m-%d')
        
        # Ensure extension starts with a dot
        ext = self.extension if self.extension.startswith('.') else f'.{self.extension}'
        
        return f"{date_str}_{safe_email}_{random_suffix}{ext}"
    
    def save(self, save_dir: Union[str, Path]) -> Path:
        """Save the attachment to disk.
        
        Args:
            save_dir: Directory to save the attachment in (should be the sender's directory)
            
        Returns:
            Path to the saved file
            
        Raises:
            ValueError: If email_date or sender_email is not set
            OSError: If the file cannot be written
        """
        if not all([self.email_date, self.sender_email]):
            raise ValueError("email_date and sender_email must be set before saving")
            
        # Ensure save_dir is a Path object
        save_dir = Path(save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate the filename
        filename = self.safe_filename
        filepath = save_dir / filename
        
        # Handle filename collisions
        counter = 1
        while filepath.exists():
            # If file exists, try appending a counter before the extension
            name_parts = filename.rsplit('.', 1)
            if len(name_parts) > 1:
                new_name = f"{name_parts[0]}_{counter}.{name_parts[1]}"
            else:
                new_name = f"{filename}_{counter}"
            filepath = save_dir / new_name
            counter += 1
        
        # Write the file
        with open(filepath, 'wb') as f:
            f.write(self.payload)
        
        self.saved_path = filepath
        return filepath
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the attachment to a dictionary."""
        return {
            'content_id': self.content_id,
            'filename': self.filename,
            'content_type': self.content_type,
            'size': self.size,
            'saved_path': str(self.saved_path) if self.saved_path else None,
            'message_id': self.message_id,
            'email_date': self.email_date.isoformat() if self.email_date else None,
            'sender_email': self.sender_email
        }
