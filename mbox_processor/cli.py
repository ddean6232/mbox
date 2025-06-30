"""Command-line interface for the MBOX processor."""
import argparse
import logging
import sys
from pathlib import Path
from typing import Optional, List

from . import __version__
from .config import Config
from .processors import MboxProcessor
from .utils.logging_utils import setup_logging

def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments.
    
    Args:
        args: List of command-line arguments (default: sys.argv[1:])
        
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description='Process MBOX files from Google Takeout',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Required arguments
    parser.add_argument(
        'input_file',
        type=str,
        help='Path to the input MBOX file'
    )
    
    # Optional arguments
    parser.add_argument(
        '-o', '--output-dir',
        type=str,
        default='attachments',
        help='Directory to save extracted attachments'
    )
    
    parser.add_argument(
        '--output-mbox',
        type=str,
        default='output.mbox',
        help='Path to save the processed MBOX file'
    )
    
    parser.add_argument(
        '-m', '--max-messages',
        type=int,
        default=0,
        help='Maximum number of messages to process (0 for all)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--log-file',
        type=str,
        default='mbox_processor.log',
        help='Path to the log file'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {__version__}'
    )
    
    return parser.parse_args(args)

def main() -> int:
    """Main entry point for the CLI.
    
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        # Parse command-line arguments
        args = parse_args()
        
        # Set up logging
        log_level = logging.DEBUG if args.verbose else logging.INFO
        setup_logging(log_file=args.log_file, log_level=log_level)
        
        logger = logging.getLogger(__name__)
        logger.info("Starting MBOX processor (version: %s)", __version__)
        
        # Create and validate configuration
        config = Config(
            input_file=args.input_file,
            output_dir=args.output_dir,
            output_mbox=args.output_mbox,
            max_messages=args.max_messages,
            verbose=args.verbose
        )
        
        try:
            config.validate()
        except (FileNotFoundError, ValueError) as e:
            logger.error("Configuration error: %s", str(e))
            return 1
        
        # Process the MBOX file
        processor = MboxProcessor(config)
        stats = processor.process()
        
        # Print summary
        print("\nProcessing complete!")
        print(f"Total messages: {stats['total_messages']}")
        print(f"Processed: {stats['processed_messages']}")
        print(f"Failed: {stats['failed_messages']}")
        print(f"Duration: {stats['duration_seconds']:.2f} seconds")
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
        return 1
    except Exception as e:
        logger.exception("An unexpected error occurred: %s", str(e))
        return 1

if __name__ == '__main__':
    sys.exit(main())
