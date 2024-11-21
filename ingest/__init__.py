import logging


def logging_setup():
    log_format = "%(asctime)s - %(levelname)-8s - %(name)s - %(message)s"
    logging.basicConfig(format=log_format, level=logging.DEBUG)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("elasticsearch").setLevel(logging.WARNING)
