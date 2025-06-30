"""Handles processing and converting email content."""
import logging
import re
from email import policy
from email.parser import BytesParser
from typing import Optional, Tuple

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class ContentProcessor:
    """Handles processing and converting email content."""
    
    def __init__(self, keep_html: bool = False):
        """Initialize the content processor.
        
        Args:
            keep_html: Whether to keep HTML content in addition to plain text
        """
        self.keep_html = keep_html
        self.parser = BytesParser(policy=policy.default)
    
    def process_message(self, raw_message: bytes) -> dict:
        """Process a raw email message.
        
        Args:
            raw_message: Raw email message bytes
            
        Returns:
            Dictionary containing processed content
        """
        try:
            msg = self.parser.parsebytes(raw_message)
            
            # Extract basic information
            subject = msg.get('Subject', '(No Subject)')
            from_addr = msg.get('From', '')
            to_addrs = self._parse_addresses(msg.get('To', ''))
            cc_addrs = self._parse_addresses(msg.get('Cc', ''))
            bcc_addrs = self._parse_addresses(msg.get('Bcc', ''))
            
            # Extract content and attachments
            text_content, html_content, attachments = self._extract_content(msg)
            
            # Convert HTML to plain text if needed
            if not text_content and html_content:
                text_content = self._html_to_text(html_content)
            
            # If still no content, use a placeholder
            if not text_content and not html_content:
                text_content = "[No content]"
            
            return {
                'subject': subject,
                'from_addr': from_addr,
                'to_addrs': to_addrs,
                'cc_addrs': cc_addrs,
                'bcc_addrs': bcc_addrs,
                'text_content': text_content,
                'html_content': html_content if self.keep_html else None,
                'attachments': attachments,
                'headers': dict(msg.items())
            }
            
        except Exception as e:
            logger.error("Error processing message: %s", str(e), exc_info=True)
            raise
    
    def _extract_content(
        self, 
        msg, 
        text_parts: Optional[list] = None,
        html_parts: Optional[list] = None,
        attachments: Optional[list] = None
    ) -> Tuple[Optional[str], Optional[str], list]:
        """Recursively extract content and attachments from a message."""
        if text_parts is None:
            text_parts = []
        if html_parts is None:
            html_parts = []
        if attachments is None:
            attachments = []
        
        content_type = msg.get_content_type()
        
        # Handle multipart messages
        if msg.is_multipart():
            for part in msg.iter_parts():
                self._extract_content(part, text_parts, html_parts, attachments)
            return (
                '\n\n'.join(text_parts) if text_parts else None,
                '\n'.join(html_parts) if html_parts else None,
                attachments
            )
        
        # Handle attachments
        content_disposition = msg.get_content_disposition()
        if content_disposition and content_disposition.lower() in ('attachment', 'inline'):
            try:
                filename = msg.get_filename() or f'attachment_{len(attachments) + 1}'
                payload = msg.get_payload(decode=True)
                
                if payload:
                    attachments.append({
                        'filename': filename,
                        'content_type': content_type,
                        'content_disposition': content_disposition,
                        'payload': payload,
                        'size': len(payload)
                    })
                return None, None, attachments
            except Exception as e:
                logger.error("Error processing attachment: %s", str(e))
                return None, None, attachments
        
        # Handle text content
        payload = msg.get_payload(decode=True)
        if not payload:
            return None, None, attachments
        
        try:
            charset = msg.get_content_charset() or 'utf-8'
            content = payload.decode(charset, errors='replace')
            
            if content_type == 'text/plain':
                text_parts.append(content)
            elif content_type == 'text/html':
                html_parts.append(content)
                
        except Exception as e:
            logger.error("Error decoding content: %s", str(e))
        
        return None, None, attachments
    
    @staticmethod
    def _parse_addresses(addresses: str) -> list:
        """Parse email addresses from a header."""
        if not addresses:
            return []
        
        # Simple regex to extract email addresses
        # This is a simplified version and might need improvement
        email_regex = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        return re.findall(email_regex, addresses)
    
    @staticmethod
    def _html_to_text(html: str) -> str:
        """Convert HTML to plain text."""
        try:
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            return text
            
        except Exception as e:
            logger.error("Error converting HTML to text: %s", str(e))
            # Fallback to simple regex if BeautifulSoup fails
            return re.sub(r'<[^>]+>', '', html)
