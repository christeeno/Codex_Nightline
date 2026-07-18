"""Logging configuration for the application process."""

import logging.config


def configure_logging(log_level: str) -> None:
    """Configure structured, process-wide console logging."""
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "standard",
                },
            },
            "root": {"handlers": ["console"], "level": log_level.upper()},
        }
    )
