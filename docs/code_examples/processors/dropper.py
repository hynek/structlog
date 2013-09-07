from structlog import DropEvent


def dropper(logger, method_name, event_dict):
    raise DropEvent
