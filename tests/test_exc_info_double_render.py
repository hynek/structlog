import logging

import structlog

from structlog.stdlib import BoundLogger, LoggerFactory, render_to_log_kwargs


def test_exception_no_double_render_with_in_band_signaling(caplog):
    """
    Ensure that the stdlib BoundLogger suppresses exc_info when a processor
    has already rendered the exception, preventing duplicate tracebacks.
    """

    def mock_format_exc_info(logger, name, event_dict):
        event_dict["exception"] = "Mocked Traceback"
        event_dict["_structlog_exception_already_rendered"] = True
        return event_dict

    structlog.configure(
        processors=[
            mock_format_exc_info,
            structlog.stdlib.add_log_level,
            render_to_log_kwargs,
        ],
        logger_factory=LoggerFactory(),
        wrapper_class=BoundLogger,
    )

    logger = structlog.get_logger("test_logger")

    with caplog.at_level(logging.ERROR):
        try:
            raise ValueError("test error")
        except ValueError:
            logger.exception("An error occurred")

    assert len(caplog.records) == 1
    record = caplog.records[0]

    # Verify the underlying logger was called without exc_info
    assert record.exc_info is False or record.exc_info is None

    # Verify the message and extra data are intact
    assert record.msg == "An error occurred"
    assert record.__dict__.get("exception") == "Mocked Traceback"
