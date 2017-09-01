import logging
import time
import threading, queue
import smtplib
from email.message import EmailMessage
import email.utils
from functools import wraps
from collections import deque
from .credentials import *

logfile = "/home/kapascan/statuslog/log.txt"
progress_logfile = "/home/kapascan/statuslog/latest_log.txt"
email_settings = {'mail_host': ('smtp.web.de', 587),
                  'from_address': 'kapascan@web.de',
                  'credentials': (username, password),
                  'subject': 'kapascan',
                  'send_interval': 60,
                  }

logger = logging.getLogger(__name__)


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


class BufferingSMTPHandler(logging.Handler):
    def __init__(self, mail_host, from_address, to_address, subject, send_interval, credentials=None, timeout=5):
        super().__init__()
        if isinstance(mail_host, (list, tuple)):
            self.mail_host, self.mail_port = mail_host
        else:
            self.mail_host, self.mail_port = mail_host, smtplib.SMTP_PORT
        if isinstance(credentials, (list, tuple)):
            self.username, self.password = credentials
        else:
            self.username = None
        self.from_address = from_address
        if isinstance(to_address, str):
            to_address = [to_address]
        self.to_address = to_address
        self.subject = subject
        self.timeout = timeout
        self.send_interval = send_interval

        self.buffer = queue.Queue()
        self._stop = threading.Event()
        self.thread = threading.Thread(target=self.target, name=self.__class__.__name__)
        self.thread.start()

    def emit(self, record):
        self.buffer.put(record)

    def target(self):
        last_send = time.time()
        next_send = last_send + self.send_interval
        while not self._stop.is_set():
            if time.time() > next_send:
                last_send = time.time()
                self.send_buffer()
                next_send = last_send + self.send_interval
            time.sleep(max(next_send - time.time(), 0))

    def send_buffer(self):
        try:
            outgoing = []
            while not self.buffer.empty():
                record = self.buffer.get_nowait()
                outgoing.append(self.format(record))
            if outgoing:
                body = '\r\n\r\n'.join(outgoing)
                message = self.format_email(body)
                self.send_email(message)
        except Exception:
            self.handleError(record)

    def format_email(self, body):
        message = EmailMessage()
        message['From'] = self.from_address
        message['To'] = ','.join(self.to_address)
        message['Subject'] = self.subject
        message['Date'] = email.utils.localtime()
        message.set_content(body)
        return message

    def send_email(self, message):
        with smtplib.SMTP(self.mail_host, self.mail_port, timeout=self.timeout) as smtp:
            if self.username:
                smtp.ehlo()
                smtp.starttls()
                smtp.login(self.username, self.password)
            smtp.send_message(message)

    def close(self):
        self._stop.set()
        self.thread.join()
        
        super().close()


class ProgressFilter():
    def filter(self, record):
        return not record.name.endswith('progress')


def configure_logging(debug=False, email=None):
    level = logging.DEBUG if debug else logging.INFO
    # Filters:
    redact_progress = ProgressFilter()
    # Formatters:
    datefmt='%Y-%m-%d %H:%M:%S'
    info_formatter = logging.Formatter('{asctime} {levelname:^8} {message:<110}   {name:>20}', style='{', datefmt=datefmt)
    progress_formatter = logging.Formatter('{asctime} {message}', style='{', datefmt=datefmt)
    # Handlers:
    file_info_handler = logging.FileHandler(filename=logfile, mode='w')
    file_info_handler.setLevel(level)
    file_info_handler.addFilter(redact_progress)
    file_info_handler.setFormatter(info_formatter)
    debug_handler = logging.FileHandler(filename=logfile, mode='a')
    debug_handler.setLevel(logging.DEBUG)
    debug_buffer_handler = BufferingDebugHandler(250, targets=[debug_handler], flushLevel=logging.ERROR)
    debug_buffer_handler.setLevel(logging.DEBUG)
    progress_handler = logging.handlers.RotatingFileHandler(progress_logfile, mode='w', maxBytes=3000, backupCount=1)
    progress_handler.setLevel(logging.INFO)
    progress_handler.setFormatter(progress_formatter)
    if email:
        email_settings['to_address'] = email
        email_info_handler = BufferingSMTPHandler(**email_settings)
        email_info_handler.setLevel(logging.INFO)
        email_info_handler.addFilter(redact_progress)
        email_info_handler.setFormatter(info_formatter)
    # Loggers:
    logger = logging.getLogger('')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(file_info_handler)
    logger.addHandler(progress_handler)
    if level != logging.DEBUG:
        logger.addHandler(debug_buffer_handler)       
    if email:
        logger.addHandler(email_info_handler)

