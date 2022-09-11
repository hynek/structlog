from structlog import get_logger


log = get_logger()


def view(request):
    user_agent = request.get("HTTP_USER_AGENT", "UNKNOWN")
    peer_ip = request.client_addr
    if something:
        log.info("something", user_agent=user_agent, peer_ip=peer_ip)
        return "something"
    elif something_else:
        log.info("something_else", user_agent=user_agent, peer_ip=peer_ip)
        return "something_else"
    else:
        log.info("else", user_agent=user_agent, peer_ip=peer_ip)
        return "else"
