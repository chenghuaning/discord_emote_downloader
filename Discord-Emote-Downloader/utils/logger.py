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