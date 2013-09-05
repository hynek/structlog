import uuid

import flask
import structlog

from .some_module import some_function

log = structlog.stdlib.get_logger()
app = flask.Flask(__name__)


@app.route('/login', methods=['POST', 'GET'])
def some_route():
    log.new(
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
    structlog.BoundLogger.configure(
        context_class=structlog.threadlocal.wrap_dict(dict),
    )
    app.run()
