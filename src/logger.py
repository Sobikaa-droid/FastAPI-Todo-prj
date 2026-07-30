import logging
import sys


def setup_logger(name: str = "myapp") -> logging.Logger:
    """Create and configure logger."""
    logger_instance = logging.getLogger(name)
    logger_instance.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger_instance.addHandler(handler)

    return logger_instance


logger = setup_logger()