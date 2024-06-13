import logging as baselogging
import sys
import re

def strip_ansi_codes(text):
    ansi_escape = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', text)

# Custom formatter that strips ANSI codes
class StripAnsiFormatter(baselogging.Formatter):
    def format(self, record: baselogging.LogRecord):
        original = super().format(record)
        return strip_ansi_codes(original)

class MyLogger(baselogging.Logger):
    def __init__(self, name, level=baselogging.DEBUG):
        super().__init__(name, level)
        self.setLevel(level)

    def info(self, text):
        super().info("\033[1;33m" + text + "\033[0m")

    def error(self, text):
        super().error("\033[1;31m" + text + "\033[0m")

class logging:
    loggers = {}

    @staticmethod
    def get_logger(config=None, loglevel=baselogging.ERROR, loggername=__name__) -> MyLogger:
        if config:
            if config.DEBUG:
                loglevel = baselogging.DEBUG
            elif config.INFO:
                loglevel = baselogging.INFO
            else:
                loglevel = baselogging.ERROR

        if loggername in logging.loggers:
            return logging.loggers[loggername]
            
        # Create a logger
        logger = MyLogger(loggername, loglevel)

        # Ensure handlers are only added once
        if not logger.hasHandlers():
            # Console handler with colored output
            console_handler = baselogging.StreamHandler(sys.stdout)
            console_handler.setLevel(loglevel)
            console_format = baselogging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(console_format)

            # File handler without colored output
            file_handler = baselogging.FileHandler('logfile.log')
            file_handler.setLevel(loglevel)
            file_format = StripAnsiFormatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(file_format)

            # Add handlers to the logger
            logger.addHandler(console_handler)
            logger.addHandler(file_handler)

        logging.loggers[loggername] = logger
        return logger
