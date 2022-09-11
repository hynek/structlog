from structlog import get_logger


logger = get_logger()


def view(request):
    log = logger.bind(
        user_agent=request.get("HTTP_USER_AGENT", "UNKNOWN"),
        peer_ip=request.client_addr,
    )
    foo = request.get("foo")
    if foo:
        log = log.bind(foo=foo)
    if something:
        log.info("something")
        return "something"
    elif something_else:
        log.info("something_else")
        return "something_else"
    else:
        log.info("else")
        return "else"
