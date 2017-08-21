import logging
import sys
from functools import wraps
from collections import deque


logfile = "kapascan.log"


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


class DebugBuffer(logging.Handler):
    def __init__(self, capacity, target, flushLevel=logging.ERROR):
        super().__init__()
        self.buffer = deque(maxlen=capacity)
        self.target = target
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
        self.target.handle(separator_record)
        try:
            if self.target:
                while True:
                    try:
                        record = self.buffer.popleft()
                        self.target.handle(record)
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



def configure_logging(debug=False):
    level = logging.DEBUG if debug else logging.INFO
    logger = logging.getLogger('')
    logger.setLevel(logging.DEBUG)
    
    info_handler = logging.FileHandler(filename=logfile, mode='w')
    info_handler.setLevel(level)
    error_handler = logging.StreamHandler(sys.stdout)
    error_handler.setLevel(logging.ERROR)
    debug_handler = logging.FileHandler(filename=logfile, mode='w')
    debug_handler.setLevel(logging.DEBUG)
    debug_buffer_handler = DebugBuffer(500, target=info_handler, flushLevel=logging.ERROR)
    debug_buffer_handler.setLevel(logging.DEBUG)
    
    info_formatter = logging.Formatter('{asctime}  {levelname:<8} {name}: {message}', style='{')
    error_formatter = logging.Formatter('{message}', style='{')
    info_handler.setFormatter(info_formatter)
    error_handler.setFormatter(error_formatter)
    debug_handler.setFormatter(info_formatter)
    
    logger.addHandler(info_handler)
    logger.addHandler(error_handler)
    logger.addHandler(debug_buffer_handler)
