import logging
import sys
import uuid

import flask

from some_module import some_function

import structlog


logger = structlog.get_logger()
app = flask.Flask(__name__)


@app.route("/login", methods=["POST", "GET"])
def some_route():
    # You would put this into some kind of middleware or processor so it's set
    # automatically for all requests in all views.
    structlog.threadlocal.clear_threadlocal()
    structlog.threadlocal.bind_threadlocal(
        view=flask.request.path,
        request_id=str(uuid.uuid4()),
        peer=flask.request.access_route[0],
    )
    # End of belongs-to-middleware.

    log = logger.bind()
    # do something
    # ...
    log.info("user logged in", user="test-user")
    # ...
    some_function()
    # ...
    return "logged in!"


if __name__ == "__main__":
    logging.basicConfig(
        format="%(message)s", stream=sys.stdout, level=logging.INFO
    )
    structlog.configure(
        processors=[
            structlog.threadlocal.merge_threadlocal,  # <--!!!
            structlog.processors.KeyValueRenderer(
                key_order=["event", "view", "peer"]
            ),
        ],
        context_class=structlog.threadlocal.wrap_dict(dict),
        logger_factory=structlog.stdlib.LoggerFactory(),
    )
    app.run()
