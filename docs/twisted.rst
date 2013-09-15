.. _twisted:

Twisted Support
===============

Additionally to the smart logger wrappers :class:`~structlog.twisted.JSONRenderer` and :class:`~structlog.twisted.LogAdapter` that make sure that *your* log entries are well-formatted, structlog comes with a wrapper for Twisted's log observers to ensure the rest of your logs are in JSON to: :func:`~structlog.twisted.withJSONObserver`.

What it does is determining whether a log entry has been formatted by structlog and if not, converts the log entry to JSON with `event` being the log message and making `system` the second key.

So for example, the common::

   2013-09-15 22:02:18+0200 [-] Log opened.

becomes::

   2013-09-15 22:02:18+0200 [-] {"event": "Log opened.", "system": "-"}

There is obviously some redundancy here.
Also, I'm presuming that when you write out JSON logs, you're going to let something else parse them which makes the human-readable date entries more trouble than they're worth.


Logging Best Practices
----------------------

To get a clean log without timestamps and additional system fields (``[-]``), structlog comes with :class:`~structlog.twisted.PlainFileLogObserver` that only writes the plain message to a file and :func:`~structlog.twisted.plainJSONStdOutLogger` that composes it with :func:`~structlog.twisted.JSONLogObserverWrapper` and gives you a pure JSON log without any timestamps or other noise.

And finally, to get *fast* and *efficiently machine-readable* timestamps, you can either pipe your output to tai64n_ or use runit_ in the first place.
If you have only moderate amounts of log entries, you can also just send them to syslogd_.

.. _tai64n: http://cr.yp.to/daemontools/tai64n.html
.. _runit: http://smarden.org/runit/
.. _syslogd: http://en.wikipedia.org/wiki/Syslogd
