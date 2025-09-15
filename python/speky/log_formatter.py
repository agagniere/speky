import logging


class ColoredFormatter(logging.Formatter):
    green = '\033[32m'
    cyan = '\033[36m'
    dim = '\033[39;2m'
    yellow = '\033[33m'
    magenta = '\033[35m'
    red = '\033[31m'
    red_bg = '\033[41;97;1m'
    reset = '\033[0m'
    name = '%(name)6s '
    level = '%(levelname)8s'
    message = '  %(message)s'

    FORMATS = {
        logging.DEBUG: dim + name + level + message + reset,
        logging.INFO: name + green + level + reset + message,
        logging.WARNING: name + yellow + level + reset + message,
        logging.ERROR: name + red + level + reset + message,
        logging.CRITICAL: name + red_bg + level + reset + message,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)
