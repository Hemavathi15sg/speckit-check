"""
Unit Tests for Structured Logging Configuration

Tests for logging_config.py covering:
- JSON-formatted log output
- Request correlation IDs
- Latency tracking helpers
- Error categorization
- All log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
"""

import json
import logging
import pytest
from io import StringIO
from unittest.mock import patch

from logging_config import (
    JsonFormatter,
    configure_logging,
    generate_correlation_id,
    get_correlation_id,
    set_correlation_id,
    get_logger,
    log_request_start,
    log_request_end,
    log_search_start,
    log_search_end,
    log_error,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _capture_log(level: int = logging.DEBUG) -> tuple[logging.Logger, StringIO]:
    """Return a logger wired to an in-memory stream for assertions."""
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())
    handler.setLevel(level)

    logger = logging.getLogger(f"test.{id(stream)}")
    logger.setLevel(level)
    logger.propagate = False
    logger.addHandler(handler)
    return logger, stream


def _parse_log(stream: StringIO) -> list[dict]:
    """Parse all JSON log lines from *stream*."""
    stream.seek(0)
    return [json.loads(line) for line in stream.read().splitlines() if line.strip()]


# ---------------------------------------------------------------------------
# Correlation ID tests
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_generate_correlation_id_is_unique():
    """Two generated IDs should never be the same."""
    id1 = generate_correlation_id()
    id2 = generate_correlation_id()
    assert id1 != id2


@pytest.mark.unit
def test_generate_correlation_id_is_string():
    """Correlation IDs must be non-empty strings."""
    cid = generate_correlation_id()
    assert isinstance(cid, str)
    assert len(cid) > 0


@pytest.mark.unit
def test_set_and_get_correlation_id():
    """set_correlation_id / get_correlation_id round-trip."""
    test_id = "test-correlation-123"
    set_correlation_id(test_id)
    assert get_correlation_id() == test_id


@pytest.mark.unit
def test_correlation_id_default_is_empty_string():
    """Before any request context, correlation ID defaults to empty string."""
    set_correlation_id("")
    assert get_correlation_id() == ""


# ---------------------------------------------------------------------------
# JSON formatter tests
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_json_formatter_produces_valid_json():
    """Every log record must be valid JSON."""
    logger, stream = _capture_log()
    logger.info("hello world")

    records = _parse_log(stream)
    assert len(records) == 1


@pytest.mark.unit
def test_json_formatter_contains_required_fields():
    """JSON log entry must have timestamp, level, logger, message, correlation_id."""
    logger, stream = _capture_log()
    logger.info("required fields test")

    entry = _parse_log(stream)[0]
    for field in ("timestamp", "level", "logger", "message", "correlation_id"):
        assert field in entry, f"Missing required field: {field}"


@pytest.mark.unit
def test_json_formatter_level_names():
    """All five log levels should appear correctly in JSON output."""
    logger, stream = _capture_log(level=logging.DEBUG)
    logger.debug("debug msg")
    logger.info("info msg")
    logger.warning("warning msg")
    logger.error("error msg")
    logger.critical("critical msg")

    levels = [r["level"] for r in _parse_log(stream)]
    assert levels == ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


@pytest.mark.unit
def test_json_formatter_includes_correlation_id():
    """Correlation ID stored in context should appear in the log entry."""
    set_correlation_id("req-abc-999")
    logger, stream = _capture_log()
    logger.info("correlation test")

    entry = _parse_log(stream)[0]
    assert entry["correlation_id"] == "req-abc-999"
    # Reset
    set_correlation_id("")


@pytest.mark.unit
def test_json_formatter_includes_extra_fields():
    """Extra keyword fields passed via ``extra=`` must appear in JSON."""
    logger, stream = _capture_log()
    logger.info("extra fields", extra={"user_id": "u-42", "duration_ms": 12.5})

    entry = _parse_log(stream)[0]
    assert entry["user_id"] == "u-42"
    assert entry["duration_ms"] == 12.5


@pytest.mark.unit
def test_json_formatter_includes_exception_info():
    """Exceptions logged with exc_info should be serialized into the entry."""
    logger, stream = _capture_log()
    try:
        raise ValueError("boom")
    except ValueError:
        logger.error("something broke", exc_info=True)

    entry = _parse_log(stream)[0]
    assert "error" in entry
    assert entry["error"]["type"] == "ValueError"
    assert "boom" in entry["error"]["message"]
    assert isinstance(entry["error"]["traceback"], list)


# ---------------------------------------------------------------------------
# configure_logging tests
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_configure_logging_returns_root_logger():
    """configure_logging() must return the root logger."""
    root = configure_logging()
    assert root is logging.getLogger()


@pytest.mark.unit
def test_configure_logging_sets_level():
    """Root logger level should match the level argument."""
    configure_logging(level=logging.WARNING)
    assert logging.getLogger().level == logging.WARNING
    # Restore
    configure_logging(level=logging.DEBUG)


# ---------------------------------------------------------------------------
# get_logger tests
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_get_logger_returns_named_logger():
    """get_logger should return a Logger with the given name."""
    lg = get_logger("my.module")
    assert lg.name == "my.module"


@pytest.mark.unit
def test_get_logger_is_logging_logger():
    """Returned object must be an instance of logging.Logger."""
    assert isinstance(get_logger("test"), logging.Logger)


# ---------------------------------------------------------------------------
# log_request_start / log_request_end tests
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_log_request_start_emits_event():
    """log_request_start should emit a JSON log with event=request_start."""
    logger, stream = _capture_log()
    log_request_start(logger, "GET", "/api/health", "corr-001")

    entry = _parse_log(stream)[0]
    assert entry["event"] == "request_start"
    assert entry["http_method"] == "GET"
    assert entry["http_path"] == "/api/health"


@pytest.mark.unit
def test_log_request_end_includes_latency():
    """log_request_end must include duration_ms and status_code."""
    logger, stream = _capture_log()
    log_request_end(logger, "POST", "/api/search", 200, 45.3)

    entry = _parse_log(stream)[0]
    assert entry["event"] == "request_end"
    assert entry["http_status_code"] == 200
    assert entry["duration_ms"] == pytest.approx(45.3)


# ---------------------------------------------------------------------------
# log_search_start / log_search_end tests
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_log_search_start_emits_event():
    """log_search_start should emit a DEBUG log with event=search_start."""
    logger, stream = _capture_log(level=logging.DEBUG)
    log_search_start(logger, "pasta", "user-1")

    entry = _parse_log(stream)[0]
    assert entry["event"] == "search_start"
    assert entry["query"] == "pasta"
    assert entry["user_id"] == "user-1"
    assert entry["level"] == "DEBUG"


@pytest.mark.unit
def test_log_search_end_includes_results_and_latency():
    """log_search_end must include results_count, duration_ms, and event."""
    logger, stream = _capture_log()
    log_search_end(logger, "pasta", "user-1", 7, 88.2)

    entry = _parse_log(stream)[0]
    assert entry["event"] == "search_end"
    assert entry["results_count"] == 7
    assert entry["duration_ms"] == pytest.approx(88.2)


@pytest.mark.unit
def test_log_search_end_includes_db_duration_when_provided():
    """Optional db_duration_ms should appear when supplied."""
    logger, stream = _capture_log()
    log_search_end(logger, "pasta", "user-1", 3, 60.0, db_duration_ms=20.5)

    entry = _parse_log(stream)[0]
    assert entry["db_duration_ms"] == pytest.approx(20.5)


# ---------------------------------------------------------------------------
# log_error tests
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_log_error_emits_at_error_level():
    """log_error must emit at ERROR level."""
    logger, stream = _capture_log()
    log_error(logger, "TEST_ERROR", "something went wrong")

    entry = _parse_log(stream)[0]
    assert entry["level"] == "ERROR"


@pytest.mark.unit
def test_log_error_includes_category():
    """error_category must appear in the JSON entry."""
    logger, stream = _capture_log()
    log_error(logger, "NULL_DIETARY_BUG", "dietary_restrictions is None", user_id="u-1")

    entry = _parse_log(stream)[0]
    assert entry["error_category"] == "NULL_DIETARY_BUG"
    assert entry["user_id"] == "u-1"


@pytest.mark.unit
def test_log_error_attaches_exception():
    """When an exception is passed, it must be serialized into ``error``."""
    logger, stream = _capture_log()
    exc = TypeError("'NoneType' object is not iterable")
    log_error(logger, "NULL_DIETARY_BUG", "crash", exc=exc)

    entry = _parse_log(stream)[0]
    assert "error" in entry
    assert entry["error"]["type"] == "TypeError"


@pytest.mark.unit
def test_log_error_accepts_arbitrary_context():
    """Extra keyword args to log_error should appear in JSON."""
    logger, stream = _capture_log()
    log_error(logger, "SOME_ERR", "ctx test", query="pasta", duration_ms=5.0)

    entry = _parse_log(stream)[0]
    assert entry["query"] == "pasta"
    assert entry["duration_ms"] == pytest.approx(5.0)
