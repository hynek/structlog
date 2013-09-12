from structlog import DropEvent


class ConditionalDropper(object):
    def __init__(self, peer_to_ignore):
        self._peer_to_ignore = peer_to_ignore

    def __call__(self, logger, method_name, event_dict):
        """
        >>> cd = ConditionalDropper('127.0.0.1')
        >>> cd(None, None, {'event': 'foo', 'peer': '10.0.0.1'})
        {'peer': '10.0.0.1', 'event': 'foo'}
        >>> cd(None, None, {'event': 'foo', 'peer': '127.0.0.1'})
        Traceback (most recent call last):
        ...
        DropEvent
        """
        if event_dict.get('peer') == self._peer_to_ignore:
            raise DropEvent
        else:
            return event_dict
