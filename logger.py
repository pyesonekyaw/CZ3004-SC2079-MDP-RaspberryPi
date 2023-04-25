import logging


def prepare_logger() -> logging.Logger:
    """
    Creates a logger that is able to both print to console and save to file.
    """
    log_format = logging.Formatter(
        '%(asctime)s :: %(levelname)s :: %(message)s')

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    if not logger.hasHandlers():
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(log_format)

        # File handler
        file_handler = logging.FileHandler('logfile.txt')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(log_format)

        # Add handlers to logger
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    return logger
