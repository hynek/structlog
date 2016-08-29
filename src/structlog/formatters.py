# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

"""
Processor->Formatter proxy.
Formatter for native ``logging`` module that uses bound ``structlog`` processor
to format message.
"""

import logging


class ProcessorFormatter(logging.Formatter):
    """Custom stdlib logging formatter for structlog ``event_dict`` messages.

    Apply a structlog processor to the ``event_dict`` passed as
    ``LogRecord.msg`` to convert it to loggable format (a string).

    """

    def __init__(self, processor, fmt=None, datefmt=None, style='%'):
        """Keep reference to the ``processor``."""
        super().__init__(fmt=fmt, datefmt=datefmt, style=style)
        self.processor = processor

    def format(self, record):
        """Extract structlog's ``event_dict`` from ``record.msg``.

        Process a copy of ``record.msg`` since the some processors modify the
        ``event_dict`` and the ``LogRecord`` will be used for multiple
        formatting runs.

        """
        if isinstance(record.msg, dict):
            msg_repr = self.processor(
                record._logger, record._name, record.msg.copy())
            return msg_repr
        return record.getMessage()
