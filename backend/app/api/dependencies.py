"""Explicit dependencies shared by the HTTP endpoint contracts."""

import logging
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db


def get_logger() -> logging.Logger:
    return logging.getLogger("para_ai.api")


SessionDep = Annotated[Session, Depends(get_db)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
LoggerDep = Annotated[logging.Logger, Depends(get_logger)]
