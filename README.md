# Google Takeout MBOX Processor

A Python-based processor specifically designed to handle MBOX files exported from Google Takeout, with robust support for email content and attachments.

## Features

- **Google Takeout Optimized**: Specifically handles Google's MBOX format and custom headers
- **Attachment Preservation**: Extracts and saves attachments with consistent naming
- **Post-Processing**: Automatically detects and adds file extensions to extensionless files
- **Content Conversion**: Converts HTML email content to clean plain text
- **Metadata Preservation**: Maintains all original email headers and metadata
- **Error Resilience**: Gracefully handles malformed messages and continues processing
- **Progress Reporting**: Provides detailed progress updates during processing
- **Temporary File Handling**: Optionally preserves temporary files for debugging

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
  --Pp, --post-process  Enable post-processing of files without extensions (default: False)
  --keep-temp          Keep temporary directory after processing (for debugging) (default: False)
  --version            Show program's version number and exit
```

### Example

```bash
# Process a file with default settings
mbox-processor Inbox.mbox

# Basic processing with custom output
mbox-processor Inbox.mbox \
    --output-dir ./my_attachments \
    --output-mbox ./processed/emails.mbox \
    --max-messages 1000 \
    --verbose

# Enable post-processing of files without extensions
mbox-processor Inbox.mbox --Pp

# Keep temporary files for debugging
mbox-processor Inbox.mbox --Pp --keep-temp
```

## Output Structure

```
.
├── attachments/                     # Extracted attachments
│   ├── temp/                       # Temporary files without extensions (if --keep-temp is used)
│   │   ├── sender_example_com/
│   │   │   └── 2025-06-30_sender_example_com_12345
│   │   └── another_sender_example_com/
│   │       └── 2025-06-29_another_sender_example_com_54321
│   ├── sender_example_com/         # Sender's email with _ instead of special chars
│   │   ├── 2025-06-30_sender_example_com_12345.pdf
│   │   └── 2025-06-30_sender_example_com_67890.jpg
│   └── another_sender_example_com/
│       └── 2025-06-29_another_sender_example_com_54321.pdf
└── output.mbox                     # Processed MBOX file with attachment notices
```

### Attachment Naming and Processing

#### Naming Convention

- **Folder Name**: Sender's email with special characters replaced
  - Example: `john_doe_example_com`
  - All special characters including `.`, `@`, and `+` are replaced with `_`
  - Example: `john.doe+test@example.com` becomes `john_doe_test_example_com`

- **File Name Format**: `{YYYY-MM-DD}_{sanitized_sender_email}_{random_5_digits}.{ext}`
  - `YYYY-MM-DD`: Date email was received
  - `sanitized_sender_email`: Sender's email with special characters replaced by `_`
  - `random_5_digits`: Random number between 10000-99999 (ensures uniqueness)
  - `ext`: Original file extension (in lowercase)

Example: `2025-06-30_john_doe_example_com_12345.pdf`

#### Post-Processing

When the `--Pp` flag is used, the processor will:

1. Save files without extensions to a temporary directory
2. Attempt to detect their MIME type using `python-magic`
3. Add the appropriate extension based on the detected type
4. Move the file to the correct sender's directory
5. Keep files with unknown types in the temp directory

**Note**: The temporary directory is automatically cleaned up unless the `--keep-temp` flag is used.

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
