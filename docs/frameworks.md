# Frameworks

To have consistent log output, it makes sense to configure *structlog* *before* any logging is done.
The best place to perform your configuration varies with applications and frameworks.
If you use standard library's {mod}`logging`, it makes sense to configure them next to each other.


## Celery

[Celery](https://docs.celeryq.dev/)'s multi-process architecture leads unavoidably to race conditions that show up as interleaved logs.
It ships standard library-based helpers in the form of [`celery.utils.log.get_task_logger()`](https://docs.celeryq.dev/en/stable/userguide/tasks.html#logging) that you should use inside of tasks to prevent that problem.

The most straight-forward way to integrate that with *structlog* is using {doc}`standard-library` and wrapping that logger using {func}`structlog.wrap_logger`:

```python
from celery.utils.log import get_task_logger

logger = structlog.wrap_logger(get_task_logger(__name__))
```

If you want to automatically bind task metadata to your {doc}`contextvars`, you can use [Celery's signals](https://docs.celeryq.dev/en/stable/userguide/signals.html):

```python
from celery import signals

@signals.task_prerun.connect
def on_task_prerun(sender, task_id, task, args, kwargs, **_):
    structlog.contextvars.bind_contextvars(task_id=task_id, task_name=task.name)
```

See [this issue](https://github.com/hynek/structlog/issues/287) for more details.


## Django

[*django-structlog*](https://pypi.org/project/django-structlog/) is a popular and well-maintained package that does all the heavy lifting.


## Flask

See Flask's [Logging docs](https://flask.palletsprojects.com/en/latest/logging/).

Generally speaking: configure *structlog* *before* instantiating `flask.Flask`.

Here's a [signal handler](https://flask.palletsprojects.com/en/latest/signals/) that binds various request details into [*context variables*](contextvars.md):

```python
def bind_request_details(sender: Flask, **extras: dict[str, Any]) -> None:
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        request_id=request.headers.get("X-Unique-ID", "NONE"),
        peer=peer,
    )

    if current_user.is_authenticated:
        structlog.contextvars.bind_contextvars(
            user_id=current_user.get_id(),
        )
```

You add it to an existing `app` like this:

```python
from flask import request_started

request_started.connect(bind_request_details, app)
```


## Litestar

[Litestar](https://docs.litestar.dev/) comes with *structlog* support [out of the box](https://docs.litestar.dev/latest/usage/logging.html).


## OpenTelemetry

The [Python OpenTelemetry SDK](https://opentelemetry.io/docs/instrumentation/python/) offers an easy API to get the current span, so you can enrich your logs with a straight-forward processor:

```python
from opentelemetry import trace

def add_open_telemetry_spans(_, __, event_dict):
    span = trace.get_current_span()
    if not span.is_recording():
        event_dict["span"] = None
        return event_dict

    ctx = span.get_span_context()
    parent = getattr(span, "parent", None)

    event_dict["span"] = {
        "span_id": hex(ctx.span_id),
        "trace_id": hex(ctx.trace_id),
        "parent_span_id": None if not parent else hex(parent.span_id),
    }

    return event_dict
```


## Pyramid

Configure it in the [application constructor](https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/startup.html#the-startup-process).

Here's an example for a Pyramid [*tween*](https://docs.pylonsproject.org/projects/pyramid/en/latest/glossary.html#term-tween) that stores various request-specific data into [*context variables*](contextvars.md):

```python
@dataclass
class StructLogTween:
    handler: Callable[[Request], Response]
    registry: Registry

    def __call__(self, request: Request) -> Response:
        structlog.contextvars.clear_contextvars()
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
