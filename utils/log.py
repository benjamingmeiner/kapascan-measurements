import logging
import sys
from functools import wraps
from collections import deque


logfile = "log.txt"
progress_logfile = "../kapascan/status/log.txt"

def log_exception(f):
    logger = logging.getLogger('')
    @wraps(f)
    def logging_f(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as error:
            logger.exception(error)
            raise
    return logging_f


class BufferingDebugHandler(logging.Handler):
    def __init__(self, capacity, targets, flushLevel=logging.ERROR):
        super().__init__()
        self.buffer = deque(maxlen=capacity)
        self.targets = targets
        self.flushLevel = flushLevel
    
    def shouldFlush(self, record):
        return record.levelno >= self.flushLevel
    
    def flush(self):
        separator_record = logging.LogRecord('', logging.DEBUG, '', 0, "\n\n" +
            "          +------------------------------------------------------------------+\n" +
            "          |                                                                  |\n" + 
            "          |                latest DEBUG output appended below:               |\n" +
            "          |                                                                  |\n" + 
            "          +------------------------------------------------------------------+\n", None, None)
        self.acquire()
        for target in self.targets:
            target.handle(separator_record)
        try:
            if self.targets:
                while True:
                    try:
                        record = self.buffer.popleft()
                        for target in self.targets:
                            target.handle(record)
                    except IndexError:
                        break
        finally:
            self.release()
    
    def emit(self, record):
        self.buffer.append(record)
        if self.shouldFlush(record):
            self.flush()

    def close(self):
        try:
            super().close()
        finally:
            self.buffer.clear()

            
class ProgressFilter():
    def filter(self, record):
        return not record.name.endswith('progress')


def configure_logging(debug=False):
    level = logging.DEBUG if debug else logging.INFO
    logger = logging.getLogger('')
    logger.setLevel(logging.DEBUG)
    redact_progress = ProgressFilter()
    
    info_handler = logging.FileHandler(filename=logfile, mode='w')
    info_handler.setLevel(level)
    info_handler.addFilter(redact_progress)
    
    progress_handler = logging.handlers.RotatingFileHandler(progress_logfile, mode='w', maxBytes=3000, backupCount=1)
    progress_handler.setLevel(logging.INFO)
    
    debug_handler = logging.FileHandler(filename=logfile, mode='a')
    debug_handler.setLevel(logging.DEBUG)
    
    info_formatter = logging.Formatter('{asctime}  {levelname:<8} {name}: {message}', style='{')
    info_handler.setFormatter(info_formatter)

    progress_formatter = logging.Formatter('{asctime}: {message}', style='{')
    progress_handler.setFormatter(progress_formatter)

    debug_buffer_handler = BufferingDebugHandler(250, targets=[debug_handler], flushLevel=logging.ERROR)
    debug_buffer_handler.setLevel(logging.DEBUG)
    
    logger.addHandler(info_handler)
    logger.addHandler(debug_buffer_handler)
    logger.addHandler(progress_handler)

    