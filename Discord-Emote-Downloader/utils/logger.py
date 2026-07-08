import logging


def setup_logger():
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s',
        handlers=[
            logging.FileHandler('downloader.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


def get_file_only_logger(name: str, log_file: str = "downloader.log") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter("%(asctime)s | %(name)s | %(message)s"))
        logger.addHandler(file_handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger