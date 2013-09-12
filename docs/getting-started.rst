.. _getting-started:

Getting Started
===============

.. _install:

Installation
------------

structlog can be easily installed using::

   $ pip install structlog

Python 2.6
^^^^^^^^^^

If you're running Python 2.6 and want to use ``OrderedDict``\ s for your context (which is the default), you also have to install the respective compatibility package::

   $ pip install ordereddict

If the order of the keys of your context doesn't matter (e.g. if you're logging JSON that gets parsed anyway), simply use a vanilla ``dict`` to avoid this dependency.
See :ref:`configuration` on how to achieve that.


Your First Log Entry
--------------------

A lot of effort went into making structlog accessible without reading pages of documentation.
And indeed, the simplest possible usage looks like this:

.. literalinclude:: code_examples/getting-started/plain.txt
   :language: pycon

Here, structlog takes full advantage of its hopefully useful default settings:

- Output is sent to `standard out`_ instead of exploding into the user's face.
  Yes, that seems a rather controversial attitude toward logging.
- All keywords are formatted using :class:`structlog.processors.KeyValueRenderer`.
  That in turn uses `repr()`_ to serialize all values to strings.
  Thus, it's easy to add support for logging of your own objects.

It should be noted that even in most complex logging setups the example would still look just like that thanks to :ref:`configuration`.

There you go, structured logging!
However, this alone wouldn't warrant an own package.
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

For structlog, a log entry is just a dictionary called *event dict[ionary]*:

- You can pre-build a part of the dictionary step by step.
  These pre-saved values are called the *context*.
- As soon as an *event* happens -- which is a dictionary too -- it is merged together with the *context* to the *event dict* and logged out.
- To keep as much order of the keys as possible, an OrderedDict_ is used for the context by default.
- The recommended way of binding values is the one in these examples: creating new loggers with a new context.
  If you're okay with giving up immutable local state for convenience, you can also use :ref:`thread/greenlet local storage <threadlocal>` for the context.


structlog and Standard Library's logging
----------------------------------------

structlog's primary application isn't printing though.
Instead, it's intended to wrap your *existing* loggers and **add** *structure* and *incremental context building* to them.
For that, structlog is *completely* agnostic of your underlying logger -- you can use it with any logger you prefer.

The most prominent example of such an 'existing logger' is without doubt the logging module in the standard library.
To make this common case as simple as possible, structlog comes with some tools to help you:


.. literalinclude:: code_examples/getting-started/stdlib.txt
   :language: pycon

In other words, you tell structlog that you would like to use the standard library logger factory and keep calling :func:`~structlog.get_logger` like before.


Liked what you saw?
-------------------

Now you're all set for the rest of the user's guide.
If you want to see more code, make sure to check out the :ref:`examples`!

.. _`standard out`: http://en.wikipedia.org/wiki/Standard_out#Standard_output_.28stdout.29
.. _`repr()`: http://docs.python.org/2/reference/datamodel.html#object.__repr__
.. _recipe: http://docs.python.org/2/howto/logging-cookbook.html
.. _OrderedDict: http://docs.python.org/2/library/collections.html#collections.OrderedDict
