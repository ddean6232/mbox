"""Configuration settings for the MBOX processor."""
from pathlib import Path
from typing import Optional

class Config:
    """Global configuration for the MBOX processor."""
    
    def __init__(
        self,
        input_file: str,
        output_dir: str = "attachments",
        output_mbox: str = "output.mbox",
        max_messages: int = 0,
        verbose: bool = False
    ):
        """Initialize configuration.
        
        Args:
            input_file: Path to the input MBOX file
            output_dir: Directory to save extracted attachments
            output_mbox: Path to save the processed MBOX file
            max_messages: Maximum number of messages to process (0 for all)
            verbose: Enable verbose output
        """
        self.input_file = Path(input_file).resolve()
        self.output_dir = Path(output_dir).resolve()
        self.output_mbox = Path(output_mbox).resolve()
        self.max_messages = max(0, int(max_messages)) if max_messages else 0
        self.verbose = bool(verbose)

    @property
    def attachments_dir(self) -> Path:
        """Get the absolute path to the attachments directory."""
        return self.output_dir / "attachments"

    def validate(self) -> None:
        """Validate the configuration.
        
        Raises:
            FileNotFoundError: If input file doesn't exist
            ValueError: If configuration is invalid
        """
        if not self.input_file.exists():
            raise FileNotFoundError(f"Input file not found: {self.input_file}")
        if self.max_messages < 0:
            raise ValueError("max_messages must be 0 or positive")
