"""Handles saving and managing email attachments."""
import logging
import os
import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..models.attachment import Attachment
from ..models.email_message import EmailMessage
from ..utils.file_utils import ensure_directory, process_extensionless_files

logger = logging.getLogger(__name__)

class AttachmentHandler:
    """Handles saving and managing email attachments."""
    
    def __init__(self, base_dir: str = "attachments", post_process: bool = False, keep_temp: bool = False):
        """Initialize the attachment handler.
        
        Args:
            base_dir: Base directory to save attachments
            post_process: Whether to enable post-processing of files without extensions
            keep_temp: Whether to keep the temporary directory after processing
        """
        self.base_dir = Path(base_dir).resolve()
        self.post_process = post_process
        self.keep_temp = keep_temp
        
        # Ensure base directories exist
        self.base_dir.mkdir(parents=True, exist_ok=True)
        if self.post_process:
            self.temp_dir = self.base_dir / "temp"
            self.temp_dir.mkdir(parents=True, exist_ok=True)
            logger.debug("Temporary directory for post-processing: %s", self.temp_dir)
        
        logger.info(
            "Initialized AttachmentHandler with base directory: %s, post_process=%s, keep_temp=%s",
            self.base_dir, post_process, keep_temp
        )
    
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
        
        # Ensure the base directory exists
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        for attachment in message.attachments:
            try:
                # Set message context on attachment
                attachment.message_id = message.message_id
                attachment.email_date = message.date
                attachment.sender_email = message.from_addr
                
                # Get the save directory for this sender
                save_dir = self.get_attachment_dir(attachment.sender_email)
                
                # Save the attachment to the sender's directory
                saved_path = attachment.save(save_dir)
                saved_paths.append(saved_path)
                logger.debug("Saved attachment: %s -> %s", 
                            attachment.filename, saved_path)
                
            except Exception as e:
                logger.error("Failed to save attachment %s: %s", 
                           getattr(attachment, 'filename', 'unknown'), str(e),
                           exc_info=True)
                # Continue with next attachment even if one fails
                continue
        
        return saved_paths
        
    def post_process_attachments(self) -> Dict[str, str]:
        """Process files without extensions to detect their types and add extensions.
        
        Returns:
            Dictionary mapping original paths to new paths with extensions
        """
        if not self.post_process or not hasattr(self, 'temp_dir'):
            logger.debug("Skipping post-processing: post_process=%s, has temp_dir=%s", 
                        self.post_process, hasattr(self, 'temp_dir'))
            return {}
            
        logger.info("Starting post-processing of files without extensions in %s", self.temp_dir)
        
        # Log contents of temp directory before processing
        if logger.isEnabledFor(logging.DEBUG):
            temp_files = list(self.temp_dir.rglob('*'))
            logger.debug("Found %d files in temp directory before processing", len(temp_files))
            for f in temp_files:
                logger.debug("  - %s (size: %d bytes)", f, f.stat().st_size if f.is_file() else 0)
        
        # Process the files
        processed = process_extensionless_files(self.temp_dir, self.base_dir)
        
        # Log processing results
        logger.info(
            "Post-processing complete. Processed %d files, %d successfully",
            len(processed) + len(self._get_remaining_temp_files()),
            len(processed)
        )
        
        # Clean up temp directory if not keeping it
        if not self.keep_temp:
            self._cleanup_temp_dir()
        else:
            logger.info("Keeping temp directory as requested: %s", self.temp_dir)
            
        return processed
    
    def _get_remaining_temp_files(self) -> list:
        """Get list of files remaining in temp directory."""
        if not hasattr(self, 'temp_dir') or not self.temp_dir.exists():
            return []
        return [f for f in self.temp_dir.rglob('*') if f.is_file()]
    
    def _cleanup_temp_dir(self) -> None:
        """Clean up the temporary directory."""
        if not hasattr(self, 'temp_dir') or not self.temp_dir.exists():
            return
            
        try:
            logger.debug("Cleaning up temp directory: %s", self.temp_dir)
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        except Exception as e:
            logger.warning("Failed to clean up temp directory %s: %s", self.temp_dir, e)
        else:
            logger.debug("Successfully removed temp directory: %s", self.temp_dir)
    
    def get_attachment_dir(self, sender_email: str) -> Path:
        """Get the directory path for a sender's attachments.
        
        Args:
            sender_email: The sender's email address (can be in format "Name <email@example.com>")
            
        Returns:
            Path to the sender's attachment directory under base_dir
        """
        # Extract email from format: "John Doe <john@example.com>"
        email_match = re.search(r'<([^>]+)>', sender_email)
        if email_match:
            sender = email_match.group(1)  # Extract email from <>
        else:
            sender = sender_email  # Use as is if no <>
            
        # Sanitize sender email for directory name
        safe_email = (
            sender
            .replace('@', '_')
            .replace('.', '_')
            .replace('+', '_')
            .lower()
        )
            
        # Create sender's directory directly under base_dir
        sender_dir = self.base_dir / safe_email
        sender_dir.mkdir(parents=True, exist_ok=True)
            
        return sender_dir
    
    def list_attachments(self, sender_email: Optional[str] = None) -> List[Path]:
        """List all saved attachments, optionally filtered by sender.
        
        Args:
            sender_email: Optional sender email to filter by
            
        Returns:
            List of paths to attachments
        """
        if sender_email:
            # List attachments for a specific sender
            sender_dir = self.get_attachment_dir(sender_email)
            if not sender_dir.exists():
                return []
            return list(sender_dir.glob('*'))
        
        # List all attachments from all senders
        attachments = []
        for sender_dir in self.base_dir.glob('*'):
            if sender_dir.is_dir() and sender_dir.name != 'temp':
                attachments.extend(sender_dir.glob('*'))
        return attachments
