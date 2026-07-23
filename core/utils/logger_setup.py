# ================================================================
#  logger_setup.py  –  Structured rotating logging configuration
# ================================================================

import logging
from logging.handlers import RotatingFileHandler

def setup_logger(verbose: bool = False) -> logging.Logger:
    """
    Configure root logging to log to both a rotating file and the console.
    
    Parameters
    ----------
    verbose : bool
        If True, sets the console log level to DEBUG. Otherwise, INFO.
        
    Returns
    -------
    logging.Logger
    """
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # Root level set to capture all messages

    # Clear existing handlers to prevent duplicate logs on re-setup
    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 1. Console Handler (toggled via verbose)
    console_level = logging.DEBUG if verbose else logging.INFO
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 2. Rotating File Handler (always captures up to DEBUG)
    file_handler = RotatingFileHandler(
        "fitness_trainer.log",
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Silence noisy default logs from dependencies
    logging.getLogger("matplotlib").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)

    return logger
