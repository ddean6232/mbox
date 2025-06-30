"""Main MBOX processing module."""
import logging
import mailbox
import os
from datetime import datetime
from pathlib import Path
from typing import Iterator, List, Optional, Tuple, Union

from ..config import Config
from ..models import EmailMessage, Attachment
from .attachment_handler import AttachmentHandler
from .content_processor import ContentProcessor

logger = logging.getLogger(__name__)

class MboxProcessor:
    """Processes MBOX files and extracts content and attachments."""
    
    def __init__(self, config: Config):
        """Initialize the MBOX processor.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.attachment_handler = AttachmentHandler(str(config.attachments_dir))
        self.content_processor = ContentProcessor(keep_html=False)
        
        # Create output directory if it doesn't exist
        config.attachments_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("Initialized MboxProcessor with config: %s", {
            'input_file': str(config.input_file),
            'output_dir': str(config.output_dir),
            'max_messages': config.max_messages,
            'verbose': config.verbose
        })
    
    def process(self) -> dict:
        """Process the MBOX file and return statistics.
        
        Returns:
            Dictionary containing processing statistics
        """
        stats = {
            'total_messages': 0,
            'processed_messages': 0,
            'failed_messages': 0,
            'total_attachments': 0,
            'saved_attachments': 0,
            'start_time': datetime.utcnow().isoformat(),
            'end_time': None,
            'duration_seconds': None
        }
        
        try:
            # Open the MBOX file
            mbox = mailbox.mbox(self.config.input_file)
            stats['total_messages'] = len(mbox)
            
            logger.info("Processing %d messages from %s", 
                      stats['total_messages'], self.config.input_file)
            
            # Process each message
            for i, message in enumerate(mbox):
                if self.config.max_messages and i >= self.config.max_messages:
                    logger.info("Reached maximum number of messages to process (%d)", 
                              self.config.max_messages)
                    break
                
                try:
                    # Process the message
                    self._process_message(message, i + 1)
                    stats['processed_messages'] += 1
                    
                    # Log progress
                    if (i + 1) % 100 == 0:
                        logger.info("Processed %d/%d messages", 
                                  i + 1, min(stats['total_messages'], 
                                           self.config.max_messages or float('inf')))
                
                except Exception as e:
                    stats['failed_messages'] += 1
                    logger.error("Error processing message %d: %s", i + 1, str(e), 
                               exc_info=self.config.verbose)
        
        except Exception as e:
            logger.critical("Fatal error processing MBOX file: %s", str(e), 
                          exc_info=self.config.verbose)
            raise
        
        finally:
            # Calculate statistics
            stats['end_time'] = datetime.utcnow().isoformat()
            duration = datetime.fromisoformat(stats['end_time']) - \
                      datetime.fromisoformat(stats['start_time'])
            stats['duration_seconds'] = duration.total_seconds()
            
            logger.info("Processing complete. Statistics: %s", stats)
            return stats
    
    def _process_message(self, message: mailbox.mboxMessage, message_num: int) -> None:
        """Process a single email message.
        
        Args:
            message: The email message to process
            message_num: The message number (for logging)
        """
        try:
            # Parse the message
            parsed = self.content_processor.process_message(
                message.as_bytes()
            )
            
            # Create EmailMessage object
            email_msg = self._create_email_message(message, parsed)
            
            # Save attachments
            if email_msg.attachments:
                saved_paths = self.attachment_handler.save_attachments(email_msg)
                logger.info("Saved %d attachments for message %d", 
                           len(saved_paths), message_num)
            
            # TODO: Update MBOX file with processed content
            
        except Exception as e:
            logger.error("Error processing message %d: %s", message_num, str(e), 
                       exc_info=self.config.verbose)
            raise
    
    def _create_email_message(
        self, 
        raw_message: mailbox.mboxMessage, 
        parsed: dict
    ) -> EmailMessage:
        """Create an EmailMessage object from a raw message.
        
        Args:
            raw_message: The raw email message
            parsed: Parsed message content
            
        Returns:
            EmailMessage object
        """
        # Create attachments
        attachments = []
        for att in parsed.get('attachments', []):
            attachment = Attachment(
                content_id=att.get('content_id', ''),
                filename=att['filename'],
                content_type=att['content_type'],
                content_disposition=att['content_disposition'],
                payload=att['payload'],
                size=att['size']
            )
            attachments.append(attachment)
        
        # Create email message
        email_msg = EmailMessage(
            message_id=parsed.get('message_id', ''),
            from_addr=parsed['from_addr'],
            to_addrs=parsed['to_addrs'],
            subject=parsed['subject'],
            date=datetime.utcnow(),  # TODO: Parse date from headers
            raw_message=raw_message.as_string(),
            cc_addrs=parsed.get('cc_addrs', []),
            bcc_addrs=parsed.get('bcc_addrs', []),
            text_content=parsed.get('text_content'),
            html_content=parsed.get('html_content'),
            attachments=attachments,
            gmail_labels=parsed.get('headers', {}).get('X-Gmail-Labels', '').split(',')
        )
        
        return email_msg
