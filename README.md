# Google Takeout MBOX Processor

A Python-based processor specifically designed to handle MBOX files exported from Google Takeout, with robust support for email content and attachments.

## Features

- **Google Takeout Optimized**: Specifically handles Google's MBOX format and custom headers
- **Attachment Preservation**: Extracts and saves attachments with consistent naming
- **Content Conversion**: Converts HTML email content to clean plain text
- **Metadata Preservation**: Maintains all original email headers and metadata
- **Error Resilience**: Gracefully handles malformed messages and continues processing
- **Progress Reporting**: Provides detailed progress updates during processing

## Installation

### Prerequisites

- Python 3.8+
- System dependencies (Linux):
  ```bash
  # For Ubuntu/Debian
  sudo apt-get install libmagic1
  
  # For CentOS/RHEL
  sudo yum install file-devel
  ```

### Using pip

```bash
# Install from source
git clone https://github.com/yourusername/mbox-processor.git
cd mbox-processor
pip install -e .

# Or install directly
pip install git+https://github.com/yourusername/mbox-processor.git
```

## Usage

### Command Line

```bash
mbox-processor path/to/your/Inbox.mbox [options]
```

Or:

```bash
python -m mbox_processor path/to/your/Inbox.mbox [options]
```

### Options

```
positional arguments:
  input_file            Path to the input MBOX file

options:
  -h, --help            show this help message and exit
  -o OUTPUT_DIR, --output-dir OUTPUT_DIR
                        Directory to save extracted attachments (default: 'attachments')
  --output-mbox OUTPUT_MBOX
                        Path to save the processed MBOX file (default: 'output.mbox')
  -m MAX_MESSAGES, --max-messages MAX_MESSAGES
                        Maximum number of messages to process (0 for all) (default: 0)
  -v, --verbose         Enable verbose output (default: False)
  --log-file LOG_FILE   Path to the log file (default: 'mbox_processor.log')
  --version             show program's version number and exit
```

### Example

```bash
# Process a file with default settings
mbox-processor Inbox.mbox

# Specify custom output directories and limit to 1000 messages
mbox-processor Inbox.mbox \
    --output-dir ./my_attachments \
    --output-mbox ./processed/emails.mbox \
    --max-messages 1000 \
    --verbose
```

## Output Structure

```
.
├── attachments/                     # Extracted attachments
│   ├── sender@example.com/         # Sender's email as folder name
│   │   ├── 2025-06-30_sender@example.com_12345.pdf
│   │   └── 2025-06-30_sender@example.com_67890.jpg
│   └── another.sender@example.com/
│       └── 2025-06-29_another.sender@example.com_54321.pdf
└── output.mbox                     # Processed MBOX file with attachment notices
```

### Attachment Naming Convention

- **Folder Name**: Sender's full email address
  - Example: `john.doe@example.com`
  - Special characters (except @) are replaced with `_`
  - @ symbol is kept as is

- **File Name Format**: `{YYYY-MM-DD}_{sender_email}_{random_5_digits}.{ext}`
  - `YYYY-MM-DD`: Date email was received
  - `sender_email`: Full sender's email (matches folder name)
  - `random_5_digits`: Random number between 10000-99999 (ensures uniqueness)
  - `ext`: Original file extension (in lowercase)

Example: `2025-06-30_john.doe@example.com_12345.pdf`

## Development

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/mbox-processor.git
   cd mbox-processor
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=mbox_processor tests/

# Or
make test
```

### Code Style

This project uses:
- Black for code formatting
- isort for import sorting
- flake8 for linting
- mypy for type checking

```bash
# Format code
black .

# Sort imports
isort .

# Run linter
flake8

# Run type checker
mypy .
```

## License

MIT License - see the [LICENSE](LICENSE) file for details.
