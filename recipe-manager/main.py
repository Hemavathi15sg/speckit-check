"""
FlavorHub Recipe Manager - Main Application

Minimal FastAPI app for workshop demonstration.
"""
import time
import logging
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router
from logging_config import (
    configure_logging,
    generate_correlation_id,
    set_correlation_id,
    get_correlation_id,
    log_request_start,
    log_request_end,
)

# Initialise structured JSON logging before anything else
configure_logging(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="FlavorHub Recipe Manager",
    description="Legacy recipe search API with bugs for workshop",
    version="2.3.1"
)

# CORS (wide open for workshop)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def correlation_id_and_latency_middleware(request: Request, call_next) -> Response:
    """
    Middleware that:
    1. Reads or generates a correlation ID per request and propagates it in
       the response header so clients can reference it in support tickets.
    2. Logs request start / end with latency information.
    """
    # Accept an existing correlation ID from the client (e.g. from an upstream
    # service or browser extension), or generate a fresh one.
    correlation_id = (
        request.headers.get("X-Correlation-ID")
        or request.headers.get("X-Request-ID")
        or generate_correlation_id()
    )
    set_correlation_id(correlation_id)

    log_request_start(logger, request.method, str(request.url.path), correlation_id)

    start = time.perf_counter()
    try:
        response: Response = await call_next(request)
    except Exception as exc:
        duration_ms = (time.perf_counter() - start) * 1000
        logger.error(
            "Unhandled exception during %s %s after %.2f ms",
            request.method,
            str(request.url.path),
            duration_ms,
            exc_info=exc,
            extra={
                "event": "request_error",
                "http_method": request.method,
                "http_path": str(request.url.path),
                "http_status_code": 500,
                "duration_ms": duration_ms,
            },
        )
        raise

    duration_ms = (time.perf_counter() - start) * 1000
    response.headers["X-Correlation-ID"] = correlation_id
    response.headers["X-Response-Time-Ms"] = f"{duration_ms:.2f}"

    log_request_end(
        logger,
        request.method,
        str(request.url.path),
        response.status_code,
        duration_ms,
    )
    return response


# Include routes
app.include_router(router, prefix="/api", tags=["search"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "FlavorHub Recipe Manager",
        "version": "2.3.1",
        "status": "running",
    
    }


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting FlavorHub Recipe Manager on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
