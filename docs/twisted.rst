Twisted Support
===============

.. warning::
   Currently, the Twisted-specific code is *not* tested against Python 3.3.
   This is caused by this_ Twisted bug and will remedied once that bug is fixed.

Additionally to the smart logger wrappers :class:`~structlog.twisted.JSONRenderer` and :class:`~structlog.twisted.EventAdapter` that make sure that *your* log entries are well-formatted, structlog comes with a wrapper for Twisted's log observers to ensure the rest of your logs are in JSON too: :func:`~structlog.twisted.JSONLogObserverWrapper`.

What it does is determining whether a log entry has been formatted by :class:`~structlog.twisted.JSONRenderer`  and if not, converts the log entry to JSON with `event` being the log message and putting Twisted's `system` into a second key.

So for example::

   2013-09-15 22:02:18+0200 [-] Log opened.

becomes::

   2013-09-15 22:02:18+0200 [-] {"event": "Log opened.", "system": "-"}

There is obviously some redundancy here.
Also, I'm presuming that if you write out JSON logs, you're going to let something else parse them which makes the human-readable date entries more trouble than they're worth.


Best Practices
--------------

To get a clean log without timestamps and additional system fields (``[-]``), structlog comes with :class:`~structlog.twisted.PlainFileLogObserver` that only writes the plain message to a file and :func:`~structlog.twisted.plainJSONStdOutLogger` that composes it with the afromentioned :func:`~structlog.twisted.JSONLogObserverWrapper` and gives you a pure JSON log without any timestamps or other noise.

See also :doc:`logging-best-practices`.


.. _this: http://twistedmatrix.com/trac/ticket/6540
