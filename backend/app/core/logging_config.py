"""Sanitized logging configuration for cybersecurity hygiene.
Ensures that no PII (such as plaintext emails or tokens) is leaked into application logs.
"""
import logging
import re

class PIISanitizingFormatter(logging.Formatter):
    EMAIL_REGEX = re.compile(r'([a-zA-Z0-9_.+-]+)@([a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)')
    JWT_REGEX = re.compile(r'Bearer\s+[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*')

    def format(self, record: logging.LogRecord) -> str:
        msg = super().format(record)
        # Redact emails to e.g. a***@domain.com
        msg = self.EMAIL_REGEX.sub(r'\1[REDACTED]@\2', msg)
        # Redact JWTs
        msg = self.JWT_REGEX.sub('Bearer [REDACTED_JWT]', msg)
        return msg

def setup_logger(name: str = "app") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = PIISanitizingFormatter(
            fmt="%(asctime)s | %(levelname)-7s | [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

logger = setup_logger()

