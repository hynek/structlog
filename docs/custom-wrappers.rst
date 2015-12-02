Custom Wrappers
===============

``structlog`` comes with a generic bound logger called :class:`structlog.BoundLogger` that can be used to wrap any logger class you fancy.
It does so by intercepting unknown method names and proxying them to the wrapped logger.

This works fine, except that it has a performance penalty and the API of :class:`~structlog.BoundLogger` isn't clear from reading the documentation because large parts depend on the wrapped logger.
An additional reason is that you may want to have semantically meaningful log method names that add meta data to log entries as it is fit (see example below).

To solve that, ``structlog`` offers you to use an own wrapper class which you can configure using :func:`structlog.configure`.
And to make it easier for you, it comes with the class :class:`structlog.BoundLoggerBase` which takes care of all data binding duties so you just add your log methods if you choose to sub-class it.


.. _wrapper_class-example:

Example
-------

It's much easier to demonstrate with an example:

.. doctest::

   >>> from structlog import BoundLoggerBase, PrintLogger, wrap_logger
   >>> class SemanticLogger(BoundLoggerBase):
   ...    def msg(self, event, **kw):
   ...        if not 'status' in kw:
   ...            return self._proxy_to_logger('msg', event, status='ok', **kw)
   ...        else:
   ...            return self._proxy_to_logger('msg', event, **kw)
   ...
   ...    def user_error(self, event, **kw):
   ...        self.msg(event, status='user_error', **kw)
   >>> log = wrap_logger(PrintLogger(), wrapper_class=SemanticLogger)
   >>> log = log.bind(user='fprefect')
   >>> log.user_error('user.forgot_towel')
   user='fprefect' status='user_error' event='user.forgot_towel'

You can observe the following:

- The wrapped logger can be found in the instance variable :attr:`structlog.BoundLoggerBase._logger`.
- The helper method :func:`structlog.BoundLoggerBase._proxy_to_logger` that is a DRY_ convenience function that runs the processor chain, handles possible :exc:`~structlog.DropEvent`\ s and calls a named function on :attr:`~structlog.BoundLoggerBase._logger`.
- You can run the chain by hand though using :func:`structlog.BoundLoggerBase._process_event` .

These two methods and one attribute is all you need to write own wrapper classes.


.. _DRY: https://en.wikipedia.org/wiki/Don%27t_repeat_yourself
