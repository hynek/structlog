"""Helper classes for logging to Graylog using GELF"""

import datetime
import json
import logging.handlers
import math
import socket
import struct
import zlib

try:
    import pika
except ImportError:  # nocov
    pika = None


class GELFFormatter(logging.Formatter):
    """Format records as binary GELF.

    Supports both structured logging and regular stdlib-style string
    logging.

    """

    @staticmethod
    def get_syslog_level(level):
        if level >= logging.CRITICAL:
            return 2
        elif level >= logging.ERROR:
            return 3
        elif level >= logging.INFO:
            return 6
        else:
            # DEBUG or lower
            return 7

    def format(self, record):
        # sensible defaults -- not prefixing them with '_' is kind of
        # invalid according to spec but prevents collisions with
        # user-specified fields
        gelf = {
            "version": "1.1",
            "timestamp": record.created,
            "host": socket.gethostname(),

            "level": self.get_syslog_level(record.levelno),
            "severity": record.levelname,

            "file": record.pathname,
            "line": record.lineno,
            "function": record.funcName,

            "process": record.process,
            "process_name": record.processName,
            "thread": record.thread,
            "thread_name": record.threadName,
        }

        # extract and cache any exception
        if record.exc_info is not None and record.exc_text is None:
            record.exc_text = self.formatException(record.exc_info)

        # ...and include it
        if record.exc_text is not None:
            gelf["exception"] = record.exc_text

        if not isinstance(record.msg, dict):
            # not structlog; just include the formatted message
            gelf["short_message"] = record.getMessage()

            # we normally get this from structlog
            gelf["_logger"] = record.name

        else:
            # structlog; the message is in event, and send everything
            # onwards
            gelf["short_message"] = record.msg["event"]

            # someone using e.g. `pid` or `file` presumably knows what
            # they're doing
            gelf.update(
                ("_" + k, v) for k, v in record.msg.items() if k != "event"
            )

        # fall back to repr() to handle anything
        return json.dumps(gelf, default=repr)


_defaultFormatter = GELFFormatter()


class GraylogAMQPHandler(logging.Handler):
    "Log to Graylog via AMQP; only works with the GELF formatter"

    def __init__(
        self,
        host="localhost",
        port=5672,
        vhost="/",
        exchange="log-messages",
        routing_key="#",
        user="guest",
        password="guest",
    ):
        super().__init__()

        # sanity check
        if pika is None:
            raise ValueError("please install pika!")

        # ensure a sensible default given that nothing but GELF works
        if self.formatter is None:
            self.formatter = _defaultFormatter

        # connect lazily so that we transparently handle reconnections
        self.channel = None

        # save for later
        self.params = pika.ConnectionParameters(
            host,
            port,
            vhost,
            pika.PlainCredentials(user, password),
            # disable heartbeats and rely on TCP keep-alive instead,
            # so that the logger can safely remain idle
            heartbeat=0,
        )

        self.exchange = exchange
        self.routing_key = routing_key

    def create_channel(self):
        """Connect and create the AMQP channel"""
        channel = pika.BlockingConnection(self.params).channel()

        channel.exchange_declare(self.exchange, durable=True, passive=True)

        self.channel = channel

    def handleError(self, record):
        """Assume that something happened to the connection, and reconnect
        next time. There's no backoff, yet.

        """
        if self.channel is not None and self.channel.is_open:
            self.channel.close()

        self.channel = None

        super().handleError(record)

    def emit(self, record):
        """Send a formatted `record` to Graylog.

        """
        try:
            if self.channel is None or self.channel.is_closed:
                self.create_channel()

            self.channel.basic_publish(
                self.exchange,
                self.routing_key,
                self.format(record).encode("ascii"),
            )

        except Exception:
            self.handleError(record)


class GraylogSocketHandler(logging.handlers.SocketHandler):
    "Log to Graylog via TCP; only works with the GELF formatter"

    def __init__(self, host="localhost", port=12201, delimiter="\0"):
        super().__init__(host, port)

        self.delimiter = delimiter.encode("ascii")

        # ensure a sensible default given that nothing but GELF works
        if self.formatter is None:
            self.formatter = _defaultFormatter

    def emit(self, record):
        try:
            self.send(self.format(record).encode("ascii") + self.delimiter)

        except Exception:
            self.handleError(record)


class GraylogDatagramHandler(logging.handlers.DatagramHandler):
    "Log to Graylog via UDP; only works with the GELF formatter"

    mtu = 8000

    def __init__(self, host="localhost", port=12201):
        super().__init__(host, port)

        # ensure a sensible default given that nothing but GELF works
        if self.formatter is None:
            self.formatter = _defaultFormatter

    def chunks(self, data):
        """Split the given binary data into chunks.

        For most parts, GELF is a near-trivial format merely
        specifying which fields to use in JSON. This method implements
        the exception: support for splitting messages across more than
        one UDP datagram.

        https://docs.graylog.org/en/3.0/pages/gelf.html#chunking

        """
        # heavily inspired by MIT-licensed code from python-gelfclient

        chunk_size = self.mtu - 12  # leave space for GELF chunked header
        total_chunks = int(math.ceil(len(data) / float(chunk_size)))

        if total_chunks >= 128:
            raise ValueError("record too large!")

        count = 0
        message_id = hash(
            str(datetime.datetime.now().microsecond) + socket.gethostname()
        )

        for i, offset in enumerate(range(0, len(data), chunk_size)):
            header = struct.pack(
                "!ccqBB", b"\x1e", b"\x0f", message_id, count, total_chunks
            )

            yield header + data[offset : offset + chunk_size]

    def emit(self, record):
        try:
            body = zlib.compress(self.format(record).encode("ascii"))

            if len(body) > self.mtu:
                for chunk in self.chunks(body):
                    self.send(chunk)
            else:
                self.send(body)

        except Exception:
            self.handleError(record)
