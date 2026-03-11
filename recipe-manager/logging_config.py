"""
Structured Logging Configuration for FlavorHub Recipe Manager

This module provides centralized, production-grade logging with:
- JSON-formatted logs for machine parsing
- Request correlation IDs (trace same user across logs)
- Latency tracking (search duration, database query time)
- Error categorization and context
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
"""
import json
import logging
import sys
import traceback
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Dict, Optional

# ---------------------------------------------------------------------------
# Correlation ID context variable
# ---------------------------------------------------------------------------
# Stores the current request's correlation ID for the duration of the request.
# Each async task (FastAPI request handler) gets its own copy automatically.
_correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")


def get_correlation_id() -> str:
    """Return the correlation ID for the current request context."""
    return _correlation_id.get()


def set_correlation_id(correlation_id: str) -> None:
    """Set the correlation ID for the current request context."""
    _correlation_id.set(correlation_id)


def generate_correlation_id() -> str:
    """Generate a new unique correlation ID."""
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# JSON formatter
# ---------------------------------------------------------------------------

class JsonFormatter(logging.Formatter):
    """
    Formats log records as single-line JSON objects for machine parsing.

    Each log line contains:
    - timestamp  : ISO-8601 UTC timestamp
    - level      : Log level name (DEBUG / INFO / WARNING / ERROR / CRITICAL)
    - logger     : Logger name (module path)
    - message    : Human-readable message
    - correlation_id : Request correlation ID (empty string if not in a request)
    - error      : Exception info dict (type, message, traceback) – only on ERROR+
    - *extra*    : Any additional fields passed via the ``extra=`` parameter
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": get_correlation_id(),
        }

        # Attach extra fields (latency, user_id, query, etc.)
        for key, value in record.__dict__.items():
            if key not in _STANDARD_LOG_RECORD_KEYS and not key.startswith("_"):
                log_entry[key] = value

        # Attach exception info for ERROR and CRITICAL
        if record.exc_info:
            exc_type, exc_value, exc_tb = record.exc_info
            log_entry["error"] = {
                "type": exc_type.__name__ if exc_type else None,
                "message": str(exc_value) if exc_value else None,
                "traceback": traceback.format_exception(exc_type, exc_value, exc_tb),
            }
        elif record.exc_text:
            log_entry["error"] = {"message": record.exc_text}

        return json.dumps(log_entry, default=str)


# Keys that are always present on a LogRecord – we skip them to avoid noise.
_STANDARD_LOG_RECORD_KEYS = frozenset({
    "name", "msg", "args", "levelname", "levelno", "pathname",
    "filename", "module", "exc_info", "exc_text", "stack_info",
    "lineno", "funcName", "created", "msecs", "relativeCreated",
    "thread", "threadName", "processName", "process", "taskName",
    "message",
})


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

class _CorrelationIdFilter(logging.Filter):
    """Injects the current request correlation ID into every log record.

    This is required so that the plain-text format (``json_format=False``)
    can safely reference ``%(correlation_id)s``.
    """

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: A003
        record.correlation_id = get_correlation_id()  # type: ignore[attr-defined]
        return True


def configure_logging(level: int = logging.INFO, json_format: bool = True) -> logging.Logger:
    """
    Configure structured logging for the application.

    Args:
        level: Logging level (default: logging.INFO).
        json_format: When True (default) emit JSON lines; otherwise use a
                     human-readable text format suitable for local development.

    Returns:
        Configured root logger.

    Usage::

        from logging_config import configure_logging
        configure_logging()
        logger = logging.getLogger(__name__)
        logger.info("Application started")
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers to avoid duplicate output
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.addFilter(_CorrelationIdFilter())

    if json_format:
        console_handler.setFormatter(JsonFormatter())
    else:
        console_handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s %(levelname)-8s [%(correlation_id)s] %(name)s – %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%S",
            )
        )

    root_logger.addHandler(console_handler)
    return root_logger


def get_logger(module_name: str) -> logging.Logger:
    """
    Return a logger for *module_name* (typically pass ``__name__``).

    Usage::

        from logging_config import get_logger
        logger = get_logger(__name__)
        logger.info("Message", extra={"user_id": "abc"})
    """
    return logging.getLogger(module_name)


# ---------------------------------------------------------------------------
# Convenience logging helpers
# ---------------------------------------------------------------------------

def log_request_start(
    logger: logging.Logger,
    method: str,
    path: str,
    correlation_id: str,
    *,
    user_id: Optional[str] = None,
) -> None:
    """Log the start of an incoming HTTP request at INFO level."""
    logger.info(
        "Request started: %s %s",
        method,
        path,
        extra={
            "event": "request_start",
            "http_method": method,
            "http_path": path,
            "user_id": user_id,
        },
    )


def log_request_end(
    logger: logging.Logger,
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    *,
    user_id: Optional[str] = None,
) -> None:
    """Log the completion of an HTTP request at INFO level."""
    logger.info(
        "Request completed: %s %s → %d (%.2f ms)",
        method,
        path,
        status_code,
        duration_ms,
        extra={
            "event": "request_end",
            "http_method": method,
            "http_path": path,
            "http_status_code": status_code,
            "duration_ms": duration_ms,
            "user_id": user_id,
        },
    )


def log_search_start(
    logger: logging.Logger,
    query: str,
    user_id: str,
) -> None:
    """Log the start of a search operation at DEBUG level."""
    logger.debug(
        "Search started for user=%s query=%r",
        user_id,
        query,
        extra={
            "event": "search_start",
            "user_id": user_id,
            "query": query,
        },
    )


def log_search_end(
    logger: logging.Logger,
    query: str,
    user_id: str,
    results_count: int,
    duration_ms: float,
    *,
    db_duration_ms: Optional[float] = None,
) -> None:
    """Log the completion of a search operation at INFO level."""
    extra: Dict[str, Any] = {
        "event": "search_end",
        "user_id": user_id,
        "query": query,
        "results_count": results_count,
        "duration_ms": duration_ms,
    }
    if db_duration_ms is not None:
        extra["db_duration_ms"] = db_duration_ms
    logger.info(
        "Search completed for user=%s in %.2f ms – %d results",
        user_id,
        duration_ms,
        results_count,
        extra=extra,
    )


def log_error(
    logger: logging.Logger,
    error_category: str,
    message: str,
    exc: Optional[BaseException] = None,
    **context: Any,
) -> None:
    """
    Log a categorised error at ERROR level.

    Args:
        logger: Logger instance.
        error_category: Short identifier such as ``"VALIDATION_ERROR"`` or
            ``"NULL_DIETARY_BUG"``.
        message: Human-readable description.
        exc: Optional exception to attach.
        **context: Arbitrary key/value pairs added to the JSON log entry.
    """
    extra = {"error_category": error_category, **context}
    logger.error(message, exc_info=exc, extra=extra)
