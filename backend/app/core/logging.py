"""Central logging configuration for the application process."""

import json
import logging
import logging.config
from datetime import datetime, timezone
from typing import Any


class StructuredFormatter(logging.Formatter):
    """Render application logs as compact JSON records."""

    _standard_fields = frozenset(logging.LogRecord("", 0, "", 0, "", (), None).__dict__)

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        payload.update(
            {key: value for key, value in record.__dict__.items() if key not in self._standard_fields}
        )
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging(log_level: str) -> None:
    """Configure readable, timestamped console logging."""
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json": {
                    "()": "app.core.logging.StructuredFormatter",
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "json",
                },
            },
            "root": {"handlers": ["console"], "level": log_level.upper()},
        }
    )
