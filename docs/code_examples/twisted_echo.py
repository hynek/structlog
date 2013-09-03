import sys
import uuid

import twisted

from structlog import BoundLogger
from structlog.twisted import LogAdapter
from twisted.internet import protocol, reactor

logger = BoundLogger.wrap(twisted.python.log, processors=[LogAdapter()])


class Echo(protocol.Protocol):
    def connectionMade(self):
        self._log = logger.new(
            connection_id=str(uuid.uuid4()),
            peer=self.transport.getPeer().host,
        )

    def dataReceived(self, data):
        self._log.msg('got data', data=data)
        self.transport.write(data)

if __name__ == "__main__":
    twisted.python.log.startLogging(sys.stderr)
    reactor.listenTCP(1234, protocol.Factory.forProtocol(Echo))
    reactor.run()
