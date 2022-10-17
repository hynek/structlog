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

Configure it in the [application constructor](https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/startup.html#the-startup-process).

Here's an example for a *Pyramid* [*Tween*](https://kapeli.com/dash_share?docset_file=pyramid&docset_name=pyramid&path=narr/hooks.html%23registering-tweens&platform=pyramid) that stores various request-specific data into [*context variables*](contextvars.md):

```python
@dataclass
class StructLogTween:
    handler: Callable[[Request], Response]
    registry: Registry

    def __call__(self, request: Request) -> Response:
        structlog.contextvars.bind_contextvars(
            peer=request.client_addr,
            request_id=request.headers.get("X-Unique-ID", "NONE"),
            user_agent=request.environ.get("HTTP_USER_AGENT", "UNKNOWN"),
            user=request.authenticated_userid,
        )

        return self.handler(request)

```


## Twisted

The [plugin definition](https://docs.twisted.org/en/stable/core/howto/plugin.html) is the best place.
If your app is not a plugin, put it into your [tac file](https://docs.twisted.org/en/stable/core/howto/application.html).
