"""Configure application file logging and UTC calendar-day retention."""

import logging
import re
import time
from datetime import datetime, timedelta, timezone
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from app.utils.constant import LogSettings

LOG_DIRECTORY = Path(__file__).resolve().parents[2] / LogSettings.LOG_DIRECTORY_NAME


class DailyLogHandler(TimedRotatingFileHandler):
    """Rotate at UTC midnight and retain today plus the preceding six UTC dates."""

    def __init__(self, directory: Path):
        directory.mkdir(parents=True, exist_ok=True)
        super().__init__(
            directory / LogSettings.LOG_FILE_NAME,
            when="midnight",
            interval=1,
            backupCount=0,
            encoding="utf-8",
            utc=True,
            delay=False,
        )
        self.directory = directory

    def purge_expired(self, now: datetime | None = None) -> None:
        """Delete only this handler's dated archives older than the retention window."""
        cutoff = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).date() - timedelta(
            days=LogSettings.LOG_RETENTION_DAYS - 1
        )
        for path in self.directory.iterdir():
            match = re.fullmatch(rf"{re.escape(LogSettings.LOG_FILE_NAME)}\.(\d{{4}}-\d{{2}}-\d{{2}})", path.name)
            if not match or not path.is_file():
                continue
            try:
                archive_day = datetime.strptime(match.group(1), "%Y-%m-%d").date()
            except ValueError:
                continue
            if archive_day < cutoff:
                path.unlink(missing_ok=True)

    def doRollover(self) -> None:
        super().doRollover()
        self.purge_expired()


def configure_logging(directory: Path = LOG_DIRECTORY) -> DailyLogHandler:
    """Attach one file handler to application and Uvicorn loggers."""
    handler = DailyLogHandler(directory)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    if handler.rolloverAt <= time.time():
        handler.doRollover()
    handler.purge_expired()
    root = logging.getLogger()
    root.addHandler(handler)
    root.setLevel(logging.INFO)
    for name in ("uvicorn.error", "uvicorn.access"):
        logging.getLogger(name).addHandler(handler)
    return handler


def close_logging(handler: DailyLogHandler) -> None:
    """Detach and close the application file handler."""
    logging.getLogger().removeHandler(handler)
    for name in ("uvicorn.error", "uvicorn.access"):
        logging.getLogger(name).removeHandler(handler)
    handler.close()
