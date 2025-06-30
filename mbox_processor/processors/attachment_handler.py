"""Handles saving and managing email attachments."""
import logging
from pathlib import Path
from typing import List, Optional

from ..models.attachment import Attachment
from ..models.email_message import EmailMessage

logger = logging.getLogger(__name__)

class AttachmentHandler:
    """Handles saving and managing email attachments."""
    
    def __init__(self, base_dir: str = "attachments"):
        """Initialize the attachment handler.
        
        Args:
            base_dir: Base directory to save attachments
        """
        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Initialized AttachmentHandler with base directory: %s", self.base_dir)
    
    def save_attachments(
        self,
        message: EmailMessage,
        overwrite: bool = False
    ) -> List[Path]:
        """Save all attachments from an email message.
        
        Args:
            message: The email message containing attachments
            overwrite: Whether to overwrite existing files
            
        Returns:
            List of paths to saved attachments
        """
        saved_paths = []
        
        if not message.attachments:
            logger.debug("No attachments to save for message: %s", message.message_id)
            return saved_paths
        
        logger.info("Saving %d attachments for message: %s", 
                   len(message.attachments), message.message_id)
        
        for attachment in message.attachments:
            try:
                # Set metadata from message
                attachment.email_date = message.date
                attachment.sender_email = message.sender_email
                attachment.message_id = message.message_id
                
                # Save the attachment
                saved_path = attachment.save(self.base_dir)
                saved_paths.append(saved_path)
                logger.debug("Saved attachment: %s -> %s", 
                            attachment.filename, saved_path)
                
            except Exception as e:
                logger.error("Failed to save attachment %s: %s", 
                           getattr(attachment, 'filename', 'unknown'), str(e))
                # Continue with next attachment even if one fails
                continue
        
        return saved_paths
    
    def get_attachment_dir(self, sender_email: str) -> Path:
        """Get the directory path for a sender's attachments.
        
        Args:
            sender_email: The sender's email address
            
        Returns:
            Path to the sender's attachment directory
        """
        # Sanitize the email for use in a filename
        safe_email = (
            sender_email
            .replace('@', '_')  # Replace @ with single underscore
            .replace('.', '_')
            .replace('+', '_')
        )
        return self.base_dir / safe_email
    
    def list_attachments(self, sender_email: Optional[str] = None) -> List[Path]:
        """List all saved attachments, optionally filtered by sender.
        
        Args:
            sender_email: Optional sender email to filter by
            
        Returns:
            List of paths to attachments
        """
        if sender_email:
            dir_path = self.get_attachment_dir(sender_email)
            if not dir_path.exists():
                return []
            return list(dir_path.glob('*'))
        
        # Return all attachments from all senders
        return list(self.base_dir.glob('*/*'))
