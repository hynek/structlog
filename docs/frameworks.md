# Integration with Frameworks

To have consistent log output, it makes sense to configure *structlog* *before* any logging is done.
The best place to perform your configuration varies with applications and frameworks.
If you use standard library's logging, it makes sense to configure them next to each other.


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
