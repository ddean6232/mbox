# Google Takeout MBOX Processor

A Python-based processor specifically designed to handle MBOX files exported from Google Takeout, with robust support for email content and attachments.

## Features

- **Google Takeout Optimized**: Specifically handles Google's MBOX format and custom headers
- **Attachment Preservation**: Extracts and saves attachments with original filenames and content types
- **Content Conversion**: Converts HTML email content to clean plain text while preserving formatting
- **Metadata Preservation**: Maintains all original email headers and metadata
- **Error Resilience**: Gracefully handles malformed messages and continues processing
- **Progress Reporting**: Provides detailed progress updates during processing

## Prerequisites

- Python 3.8+
- Required Python packages (will be installed automatically):
  - `email-validator`
  - `python-magic` (for better file type detection)

## Installation

1. Clone this repository or download the script
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   
   On Linux, you might also need to install:
   ```bash
   sudo apt-get install libmagic1  # For Ubuntu/Debian
   # OR
   sudo yum install file-devel      # For CentOS/RHEL
   ```

## Usage

### Command Line

```bash
python mbox_processor.py path/to/your/Inbox.mbox [options]
```

### Options

- `-o, --output-dir`: Directory to save attachments (default: './attachments')
- `--output-mbox`: Path to save the processed MBOX file (default: 'output.mbox')
- `--max-messages`: Maximum number of messages to process (default: 0 for all)
- `--verbose`: Enable verbose output

Example:
```bash
python mbox_processor.py Inbox.mbox -o ./email_attachments --output-mbox processed.mbox --max-messages 1000
```

## Google Takeout MBOX Format

This processor is specifically designed to handle Google Takeout's MBOX format, which includes:

- Custom Google headers (X-GM-THRID, X-Gmail-Labels, etc.)
- Special handling for Google-specific content (Drive links, Meet recordings)
- Proper character encoding for international content
- Preservation of Gmail labels and threading information

## Output Structure

```
.
├── attachments/               # Extracted attachments
│   └── YYYY-MM-DD/            # Date-based subdirectories
│       └── sender-email/      # Sender-based subdirectories
│           ├── filename.pdf
│           └── ...
└── processed.mbox             # Processed MBOX file with attachment notices
```

## Processing Details

1. **Message Parsing**:
   - Uses Python's built-in `email` and `mailbox` modules
   - Handles both standard and quoted-printable/base64 encoded content
   - Preserves all original headers and metadata

2. **Attachment Handling**:
   - Extracts all MIME attachments
   - Preserves original filenames and content types
   - Saves attachments in an organized directory structure
   - Handles large files and binary content properly

3. **Content Processing**:
   - Converts HTML to clean plain text when needed
   - Maintains proper formatting and line breaks
   - Handles various character encodings

## Error Handling

- Errors are logged to `processing_errors.log`
- The processor continues with the next message if an error occurs
- A summary of errors is displayed at the end of processing

## Performance

- Processes messages in a memory-efficient manner
- Handles large MBOX files (tested with 10GB+)
- Provides progress updates during long-running operations

## License

MIT
