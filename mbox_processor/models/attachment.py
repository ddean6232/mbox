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
        """Generate a safe filename with the specified format.
        
        Format: {YYYY-MM-DD}_{sender_email}_{random_5_digits}{ext}
        """
        if not all([self.email_date, self.sender_email]):
            raise ValueError("email_date and sender_email must be set")
        
        # Sanitize sender email for filename
        safe_email = (
            self.sender_email
            .replace('@', '_')  # Replace @ with single underscore
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
        
        # Sanitize sender email for directory name
        safe_sender = (
            self.sender_email
            .replace('@', '_')  # Replace @ with single underscore
            .replace('.', '_')
            .replace('+', '_')
        )
        
        # Create sender directory
        sender_dir = Path(base_dir) / safe_sender
        sender_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate safe filename
        filename = self.safe_filename
        filepath = sender_dir / filename
        
        # Handle filename collisions
        counter = 1
        while filepath.exists():
            # If file exists, add a counter before the extension
            name_parts = filepath.stem.rsplit('_', 1)
            if len(name_parts) > 1 and name_parts[1].isdigit():
                # If filename already has a counter, increment it
                base_name = name_parts[0]
                counter = int(name_parts[1]) + 1
            else:
                # Otherwise add a counter
                base_name = filepath.stem
                
            new_filename = f"{base_name}_{counter}{filepath.suffix}"
            filepath = filepath.with_name(new_filename)
            counter += 1
        
        # Ensure parent directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
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
