# Frameworks

To have consistent log output, it makes sense to configure *structlog* *before* any logging is done.
The best place to perform your configuration varies with applications and frameworks.
If you use standard library's logging, it makes sense to configure them next to each other.

If you have no choice but *have* to configure on import time in module-global scope, or can't rule out for other reasons that that your {func}`structlog.configure` gets called more than once, *structlog* offers {func}`structlog.configure_once` that raises a warning if *structlog* has been configured before (no matter whether using {func}`structlog.configure` or {func}`~structlog.configure_once`) but doesn't change anything.


## Django

[*django-structlog*](https://pypi.org/project/django-structlog/) is a popular and well-maintained package that does all the heavy lifting.


## Flask

See Flask's [Logging docs](https://flask.palletsprojects.com/en/latest/logging/).

Generally speaking: put it *before* instantiating `flask.Flask`.


## Pyramid

[Application constructor](https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/startup.html#the-startup-process>).


## Twisted

The [plugin definition](https://docs.twisted.org/en/stable/core/howto/plugin.html) is the best place.
If your app is not a plugin, put it into your [tac file](https://docs.twisted.org/en/stable/core/howto/application.html).
