.. _getting-started:

Getting Started
===============

.. _install:

Installation
------------

``structlog`` can be easily installed using::

   $ pip install structlog


Your First Log Entry
--------------------

A lot of effort went into making ``structlog`` accessible without reading pages of documentation.
And indeed, the simplest possible usage looks like this:

.. doctest::

   >>> import structlog
   >>> log = structlog.get_logger()
   >>> log.msg('greeted', whom='world', more_than_a_string=[1, 2, 3])
   whom='world' more_than_a_string=[1, 2, 3] event='greeted'

Here, ``structlog`` takes full advantage of its hopefully useful default settings:

- Output is sent to `standard out`_ instead of exploding into the user's face.
  Yes, that seems a rather controversial attitude towards logging.
- All keywords are formatted using :class:`structlog.processors.KeyValueRenderer`.
  That in turn uses `repr()`_ to serialize all values to strings.
  Thus, it's easy to add support for logging of your own objects\ [*]_.

It should be noted that even in most complex logging setups the example would still look just like that thanks to :ref:`configuration`.

There you go, structured logging!
However, this alone wouldn't warrant its own package.
After all, there's even a recipe_ on structured logging for the standard library.
So let's go a step further.


Building a Context
------------------

Imagine a hypothetical web application that wants to log out all relevant data with just the API from above:

.. literalinclude:: code_examples/getting-started/imaginary_web.py
   :language: python

The calls themselves are nice and straight to the point, however you're repeating yourself all over the place.
At this point, you'll be tempted to write a closure like

::

   def log_closure(event):
      log.msg(event, user_agent=user_agent, peer_ip=peer_ip)

inside of the view.
Problem solved?
Not quite.
What if the parameters are introduced step by step?
Do you really want to have a logging closure in each of your views?

Let's have a look at a better approach:

.. literalinclude:: code_examples/getting-started/imaginary_web_better.py
   :language: python

Suddenly your logger becomes your closure!

For ``structlog``, a log entry is just a dictionary called *event dict[ionary]*:

- You can pre-build a part of the dictionary step by step.
  These pre-saved values are called the *context*.
- As soon as an *event* happens -- which is a dictionary too -- it is merged together with the *context* to an *event dict* and logged out.
- If you don't like the concept of pre-building a context: just don't!
  Convenient key-value-based logging is great to have on it's own.
- To keep as much order of the keys as possible, an :class:`collections.OrderedDict` is used for the context by default.
- The recommended way of binding values is the one in these examples: creating new loggers with a new context.
  If you're okay with giving up immutable local state for convenience, you can also use :ref:`thread/greenlet local storage <threadlocal>` for the context.


.. _standard-library-lite:

structlog and Standard Library's logging
----------------------------------------

``structlog``'s primary application isn't printing though.
Instead, it's intended to wrap your *existing* loggers and **add** *structure* and *incremental context building* to them.
For that, ``structlog`` is *completely* agnostic of your underlying logger -- you can use it with any logger you like.

The most prominent example of such an 'existing logger' is without doubt the logging module in the standard library.
To make this common case as simple as possible, ``structlog`` comes with some tools to help you:

.. doctest::

   >>> import logging
   >>> logging.basicConfig()
   >>> from structlog import get_logger, configure
   >>> from structlog.stdlib import LoggerFactory
   >>> configure(logger_factory=LoggerFactory())  # doctest: +SKIP
   >>> log = get_logger()
   >>> log.warn('it works!', difficulty='easy')  # doctest: +SKIP
   WARNING:structlog...:difficulty='easy' event='it works!'

In other words, you tell ``structlog`` that you would like to use the standard library logger factory and keep calling :func:`~structlog.get_logger` like before.

Since ``structlog`` is mainly used together with standard library's logging, there's :doc:`more <standard-library>` goodness to make it as fast and convenient as possible.


Liked what you saw?
-------------------

Now you're all set for the rest of the user's guide.
If you want to see more code, make sure to check out the :ref:`examples`!

.. [*] In production, you're more likely to use :class:`~structlog.processors.JSONRenderer` that can also be customized using a ``__structlog__`` method so you don't have to change your repr methods to something they weren't originally intended for.


.. _`standard out`: https://en.wikipedia.org/wiki/Standard_out#Standard_output_.28stdout.29
.. _`repr()`: https://docs.python.org/2/reference/datamodel.html#object.__repr__
.. _recipe: https://docs.python.org/2/howto/logging-cookbook.html
