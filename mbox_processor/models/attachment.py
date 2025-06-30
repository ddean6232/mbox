"""Attachment model for the MBOX processor."""
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Union, BinaryIO
import hashlib
import os
import random

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
        """Get the file extension in lowercase."""
        if not self.filename:
            # Try to determine from content type
            ext = self.content_type.split('/')[-1].lower()
            return f".{ext}" if ext else ""
        
        # Get extension from filename
        return Path(self.filename).suffix.lower()
    
    @property
    def safe_filename(self) -> str:
        """Generate a safe filename with the specified format.
        
        Format: {YYYY-MM-DD}_{sender_email}_{random_5_digits}{ext}
        """
        if not all([self.email_date, self.sender_email]):
            raise ValueError("email_date and sender_email must be set")
        
        # Sanitize sender email for filename
        safe_email = (
            self.sender_email
            .replace('@', '_at_')
            .replace('.', '_')
            .replace('+', '_')
        )
        
        # Generate random 5-digit number
        random_suffix = str(random.randint(10000, 99999))
        
        # Format date as YYYY-MM-DD
        date_str = self.email_date.strftime('%Y-%m-%d')
        
        # Get file extension
        ext = self.extension
        
        return f"{date_str}_{safe_email}_{random_suffix}{ext}"
    
    def save(self, base_dir: Union[str, Path]) -> Path:
        """Save the attachment to disk.
        
        Args:
            base_dir: Base directory to save attachments
            
        Returns:
            Path to the saved file
            
        Raises:
            ValueError: If required fields are not set
            OSError: If there's an error writing the file
        """
        if not all([self.email_date, self.sender_email]):
            raise ValueError("email_date and sender_email must be set before saving")
        
        # Create sender directory
        sender_dir = Path(base_dir) / self.sender_email
        sender_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate safe filename
        filename = self.safe_filename
        filepath = sender_dir / filename
        
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
