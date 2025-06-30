"""Email message model for the MBOX processor."""
from dataclasses import dataclass, field
from datetime import datetime
from email.message import Message
from pathlib import Path
from typing import List, Optional, Dict, Any

from ..models.attachment import Attachment

@dataclass
class EmailMessage:
    """Represents an email message with its metadata and attachments."""
    
    # Required fields
    message_id: str
    from_addr: str
    to_addrs: List[str]
    subject: str
    date: datetime
    raw_message: str
    
    # Optional fields
    cc_addrs: List[str] = field(default_factory=list)
    bcc_addrs: List[str] = field(default_factory=list)
    in_reply_to: Optional[str] = None
    references: List[str] = field(default_factory=list)
    
    # Content
    text_content: Optional[str] = None
    html_content: Optional[str] = None
    
    # Attachments
    attachments: List[Attachment] = field(default_factory=list)
    
    # Google-specific headers
    gmail_labels: List[str] = field(default_factory=list)
    gmail_thread_id: Optional[str] = None
    
    # Processing metadata
    processed: bool = False
    error: Optional[str] = None
    
    @property
    def sender_email(self) -> str:
        """Extract the email address from the From field."""
        # Handle cases like "John Doe <john@example.com>"
        if '<' in self.from_addr and '>' in self.from_addr:
            return self.from_addr.split('<')[-1].split('>')[0].strip()
        return self.from_addr.strip()
    
    @property
    def sender_name(self) -> str:
        """Extract the sender's name if available, otherwise return email local part."""
        if '<' in self.from_addr and '>' in self.from_addr:
            name_part = self.from_addr.split('<')[0].strip()
            if name_part:
                # Remove surrounding quotes if present
                return name_part.strip('\"\'')
        
        # If no name, use local part of email
        email = self.sender_email
        return email.split('@')[0] if '@' in email else email
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the message to a dictionary."""
        return {
            'message_id': self.message_id,
            'from': self.from_addr,
            'to': self.to_addrs,
            'subject': self.subject,
            'date': self.date.isoformat(),
            'has_attachments': len(self.attachments) > 0,
            'attachment_count': len(self.attachments),
            'processed': self.processed,
            'error': self.error
        }
