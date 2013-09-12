import uuid

import flask
import structlog

from .some_module import some_function


logger = structlog.get_logger()
app = flask.Flask(__name__)


@app.route('/login', methods=['POST', 'GET'])
def some_route():
    log = logger.new(
        request_id=str(uuid.uuid4()),
    )
    # do something
    # ...
    log.info('user logged in', user='test-user')
    # gives you:
    # request_id='ffcdc44f-b952-4b5f-95e6-0f1f3a9ee5fd' event='user logged in' user='test-user'
    # ...
    some_function()
    # ...

if __name__ == "__main__":
    from structlog.stdlib import LoggerFactory
    from structlog.threadlocal import wrap_dict
    structlog.configure(
        context_class=wrap_dict(dict),
        logger_factory=LoggerFactory(),
    )
    app.run()
