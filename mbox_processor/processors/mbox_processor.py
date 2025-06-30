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
        self.attachment_handler = AttachmentHandler(
            base_dir=str(config.attachments_dir),
            post_process=config.post_process,
            keep_temp=config.keep_temp
        )
        self.content_processor = ContentProcessor(keep_html=False)
        
        # Create output directory if it doesn't exist
        config.attachments_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("Initialized MboxProcessor with config: %s", {
            'input_file': str(config.input_file),
            'output_dir': str(config.output_dir),
            'max_messages': config.max_messages,
            'verbose': config.verbose
        })
    
    def _init_stats(self) -> dict:
        """Initialize the statistics dictionary.
        
        Returns:
            Dictionary containing initialized statistics
        """
        return {
            'total_messages': 0,
            'processed_messages': 0,
            'failed_messages': 0,
            'total_attachments': 0,
            'saved_attachments': 0,
            'post_processed': 0,  # Number of files post-processed
            'attachments_by_type': {},
            'senders': {},
            'start_time': datetime.utcnow(),
            'end_time': None,
            'duration_seconds': None,
            'attachments_size_bytes': 0,
            'messages_with_attachments': 0,
            'messages_processed_per_second': 0.0
        }

    def _format_size(self, size_bytes: int) -> str:
        """Format file size in a human-readable format.
        
        Args:
            size_bytes: Size in bytes
            
        Returns:
            Formatted size string (e.g., '1.2 MB')
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                if unit == 'B':
                    return f"{int(size_bytes)} {unit}"
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"

    def _print_stats(self, stats: dict) -> None:
        """Print processing statistics in a formatted way.
        
        Args:
            stats: Dictionary containing processing statistics
        """
        duration = stats['duration_seconds']
        mins, secs = divmod(duration, 60)
        hours, mins = divmod(mins, 60)
        
        print("\n" + "="*80)
        print("MBOX PROCESSING SUMMARY".center(80))
        print("="*80)
        
        # Basic info
        print(f"\n{'Total Messages:':<25} {stats['total_messages']:,}")
        print(f"{'Processed Messages:':<25} {stats['processed_messages']:,}")
        print(f"{'Failed Messages:':<25} {stats['failed_messages']:,}")
        print(f"{'Messages with Attachments:':<25} {stats['messages_with_attachments']:,}")
        
        # Timing
        print(f"\n{'Start Time:':<25} {stats['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'End Time:':<25} {stats['end_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'Duration:':<25} {int(hours):02d}:{int(mins):02d}:{int(secs):02d}")
        print(f"{'Messages/second:':<25} {stats.get('messages_processed_per_second', 0):.2f}")
        
        # Attachments
        print(f"\n{'Total Attachments:':<25} {stats['total_attachments']:,}")
        print(f"{'Saved Attachments:':<25} {stats['saved_attachments']:,}")
        if stats.get('post_processed', 0) > 0:
            print(f"{'Post-processed:':<25} {stats['post_processed']:,} files")
        print(f"{'Total Size:':<25} {self._format_size(stats['attachments_size_bytes'])}")
        
        # Top attachment types
        if stats['attachments_by_type']:
            print("\nAttachment Types:")
            for ext, count in sorted(stats['attachments_by_type'].items(), 
                                  key=lambda x: x[1], reverse=True)[:5]:
                print(f"  {ext.upper() if ext else 'UNKNOWN':<8} {count:,}")
        
        # Top senders
        if stats['senders']:
            print("\nTop Senders:")
            for sender, count in sorted(stats['senders'].items(), 
                                     key=lambda x: x[1], reverse=True)[:5]:
                print(f"  {sender:<40} {count:,} messages")
        
        print("\n" + "="*80 + "\n")

    def process(self) -> dict:
        """Process the MBOX file and return statistics.
        
        Returns:
            Dictionary containing processing statistics
        """
        stats = self._init_stats()
        
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
                    attachments_saved = self._process_message(message, i + 1)
                    stats['processed_messages'] += 1
                    
                    # Update sender stats
                    from_addr = message.get('from', 'unknown@unknown.com')
                    stats['senders'][from_addr] = stats['senders'].get(from_addr, 0) + 1
                    
                    # Update attachment stats
                    if attachments_saved:
                        stats['messages_with_attachments'] += 1
                        stats['saved_attachments'] += len(attachments_saved)
                        
                        for att in attachments_saved:
                            # Update attachment type stats
                            ext = Path(att).suffix.lower()
                            stats['attachments_by_type'][ext] = stats['attachments_by_type'].get(ext, 0) + 1
                            
                            # Update total size
                            try:
                                stats['attachments_size_bytes'] += Path(att).stat().st_size
                            except (OSError, AttributeError):
                                pass
                    
                    # Log progress
                    if (i + 1) % 100 == 0 or (i + 1) == min(stats['total_messages'], 
                                                          self.config.max_messages or float('inf')):
                        elapsed = (datetime.utcnow() - stats['start_time']).total_seconds()
                        rate = (i + 1) / elapsed if elapsed > 0 else 0
                        logger.info(
                            "Processed %d/%d messages (%.1f msg/s, %d attachments)",
                            i + 1, 
                            min(stats['total_messages'], self.config.max_messages or float('inf')),
                            rate,
                            stats['saved_attachments']
                        )
                
                except Exception as e:
                    stats['failed_messages'] += 1
                    logger.error("Error processing message %d: %s", i + 1, str(e), 
                               exc_info=self.config.verbose)
        
        except Exception as e:
            logger.critical("Fatal error processing MBOX file: %s", str(e), 
                          exc_info=self.config.verbose)
            raise
        
        finally:
            # Calculate final statistics
            stats['end_time'] = datetime.utcnow()
            stats['duration_seconds'] = (stats['end_time'] - stats['start_time']).total_seconds()
            
            if stats['duration_seconds'] > 0:
                stats['messages_processed_per_second'] = stats['processed_messages'] / stats['duration_seconds']
            
            # Post-process attachments if enabled
            if self.config.post_process:
                logger.info("Starting post-processing of attachments...")
                processed = self.attachment_handler.post_process_attachments()
                stats['post_processed'] = len(processed)
                logger.info("Post-processing complete. Processed %d files", len(processed))
                
                # Update stats with post-processing results
                for orig_path, new_path in processed.items():
                    logger.debug("Post-processed: %s -> %s", orig_path, new_path)
            
            # Print final statistics
            self._print_stats(stats)
            logger.info("Processing complete. Processed %d messages with %d attachments",
                       stats['processed_messages'], stats['saved_attachments'])
            
            return stats
    
    def _process_message(self, message: mailbox.mboxMessage, message_num: int) -> List[str]:
        """Process a single email message.
        
        Args:
            message: The email message to process
            message_num: The message number (for logging)
            
        Returns:
            List of paths to saved attachments
        """
        try:
            # Parse the message
            parsed = self.content_processor.process_message(
                message.as_bytes()
            )
            
            # Create EmailMessage object
            email_msg = self._create_email_message(message, parsed)
            
            # Save attachments
            saved_paths = []
            if email_msg.attachments:
                saved_paths = self.attachment_handler.save_attachments(email_msg)
                if saved_paths:
                    logger.debug("Saved %d attachments for message %d: %s", 
                               len(saved_paths), message_num, 
                               ", ".join(str(p) for p in saved_paths))
            
            # TODO: Update MBOX file with processed content
            
            return saved_paths
            
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
        # Parse the message date from headers if available
        email_date = None
        if 'Date' in parsed.get('headers', {}):
            try:
                from email.utils import parsedate_to_datetime
                email_date = parsedate_to_datetime(parsed['headers']['Date'])
            except (ValueError, TypeError):
                pass
        
        # Fall back to current time if date parsing fails
        if email_date is None:
            email_date = datetime.utcnow()
        
        # Create attachments
        attachments = []
        for att in parsed.get('attachments', []):
            attachment = Attachment(
                content_id=att.get('content_id', ''),
                filename=att['filename'],
                content_type=att['content_type'],
                content_disposition=att.get('content_disposition', ''),
                payload=att['payload'],
                size=att['size'],
                email_date=email_date,
                sender_email=parsed['from_addr'],
                message_id=parsed.get('message_id', '')
            )
            attachments.append(attachment)
        
        # Create email message
        email_msg = EmailMessage(
            message_id=parsed.get('message_id', ''),
            from_addr=parsed['from_addr'],
            to_addrs=parsed['to_addrs'],
            subject=parsed['subject'],
            date=email_date,
            raw_message=raw_message.as_string(),
            cc_addrs=parsed.get('cc_addrs', []),
            bcc_addrs=parsed.get('bcc_addrs', []),
            text_content=parsed.get('text_content'),
            html_content=parsed.get('html_content'),
            attachments=attachments,
            gmail_labels=parsed.get('headers', {}).get('X-Gmail-Labels', '').split(',')
        )
        
        return email_msg
