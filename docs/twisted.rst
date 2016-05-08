Twisted
=======

.. warning::

   Since :func:`sys.exc_clear` has been dropped in Python 3, there is currently no way to avoid multiple tracebacks in your log files if using ``structlog`` together with Twisted on Python 3.


Concrete Bound Logger
---------------------

To make ``structlog``'s behavior less magicy, it ships with a Twisted-specific wrapper class that has an explicit API instead of improvising: :class:`structlog.twisted.BoundLogger`.
It behaves exactly like the generic :class:`structlog.BoundLogger` except:

- it's slightly faster due to less overhead,
- has an explicit API (:func:`~structlog.twisted.BoundLogger.msg` and :func:`~structlog.twisted.BoundLogger.err`),
- hence causing less cryptic error messages if you get method names wrong.

In order to avoid that ``structlog`` disturbs your CamelCase harmony, it comes with an alias for :func:`structlog.get_logger` called :func:`structlog.getLogger`.


Processors
----------

``structlog`` comes with two Twisted-specific processors:

:class:`~structlog.twisted.EventAdapter`
   This is useful if you have an existing Twisted application and just want to wrap your loggers for now.
   It takes care of transforming your event dictionary into something `twisted.python.log.err <https://twistedmatrix.com/documents/current/api/twisted.python.log.html#err>`_ can digest.

   For example::

      def onError(fail):
         failure = fail.trap(MoonExploded)
         log.err(failure, _why='event-that-happend')

   will still work as expected.

   Needs to be put at the end of the processing chain.
   It formats the event using a renderer that needs to be passed into the constructor::

      configure(processors=[EventAdapter(KeyValueRenderer()])

   The drawback of this approach is that Twisted will format your exceptions as multi-line log entries which is painful to parse.
   Therefore ``structlog`` comes with:


:class:`~structlog.twisted.JSONRenderer`
   Goes a step further and circumvents Twisted logger's Exception/Failure handling and renders it itself as JSON strings.
   That gives you regular and simple-to-parse single-line JSON log entries no matter what happens.


Bending Foreign Logging To Your Will
------------------------------------

``structlog`` comes with a wrapper for Twisted's log observers to ensure the rest of your logs are in JSON too: :func:`~structlog.twisted.JSONLogObserverWrapper`.

What it does is determining whether a log entry has been formatted by :class:`~structlog.twisted.JSONRenderer`  and if not, converts the log entry to JSON with `event` being the log message and putting Twisted's `system` into a second key.

So for example::

   2013-09-15 22:02:18+0200 [-] Log opened.

becomes::

   2013-09-15 22:02:18+0200 [-] {"event": "Log opened.", "system": "-"}

There is obviously some redundancy here.
Also, I'm presuming that if you write out JSON logs, you're going to let something else parse them which makes the human-readable date entries more trouble than they're worth.

To get a clean log without timestamps and additional system fields (``[-]``), ``structlog`` comes with :class:`~structlog.twisted.PlainFileLogObserver` that writes only the plain message to a file and :func:`~structlog.twisted.plainJSONStdOutLogger` that composes it with the aforementioned :func:`~structlog.twisted.JSONLogObserverWrapper` and gives you a pure JSON log without any timestamps or other noise straight to `standard out`_::


   $ twistd -n --logger structlog.twisted.plainJSONStdOutLogger web
   {"event": "Log opened.", "system": "-"}
   {"event": "twistd 13.1.0 (python 2.7.3) starting up.", "system": "-"}
   {"event": "reactor class: twisted...EPollReactor.", "system": "-"}
   {"event": "Site starting on 8080", "system": "-"}
   {"event": "Starting factory <twisted.web.server.Site ...>", ...}
   ...


Suggested Configuration
-----------------------

::

   import structlog

   structlog.configure(
      processors=[
          structlog.processors.StackInfoRenderer(),
          structlog.twisted.JSONRenderer()
      ],
      context_class=dict,
      logger_factory=structlog.twisted.LoggerFactory(),
      wrapper_class=structlog.twisted.BoundLogger,
      cache_logger_on_first_use=True,
   )

See also :doc:`logging-best-practices`.


.. _`standard out`: https://en.wikipedia.org/wiki/Standard_out#Standard_output_.28stdout.29
