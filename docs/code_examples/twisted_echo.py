import sys
import uuid

import twisted

from structlog import BoundLogger
from structlog.twisted import get_logger, LogAdapter
from twisted.internet import protocol, reactor

logger = get_logger()


class Echo(protocol.Protocol):
    def connectionMade(self):
        self._log = logger.new(
            connection_id=str(uuid.uuid4()),
            peer=self.transport.getPeer().host,
        )

    def dataReceived(self, data):
        self._log.msg('got data', data=data)
        # gives you:
        # peer='127.0.0.1' connection_id='ffdfcf85-82c4-47be-9b80-e979598c0453' data='foo\n' event='got data'
        self.transport.write(data)

if __name__ == "__main__":
    BoundLogger.configure(
        processors=[LogAdapter()]
    )
    twisted.python.log.startLogging(sys.stderr)
    reactor.listenTCP(1234, protocol.Factory.forProtocol(Echo))
    reactor.run()
