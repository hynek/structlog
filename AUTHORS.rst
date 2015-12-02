Authors
-------

``structlog`` is written and maintained by `Hynek Schlawack <https://hynek.me/>`_.
It’s inspired by previous work done by `Jean-Paul Calderone <http://as.ynchrono.us/>`_ and `David Reid <https://dreid.org/>`_.

The development is kindly supported by `Variomedia AG <https://www.variomedia.de/>`_.

A full list of contributors can be found on `GitHub <https://github.com/hynek/structlog/graphs/contributors>`_.
Some of them disapprove of the addition of thread local context data. :)


Third Party Code
^^^^^^^^^^^^^^^^

The compatibility code that makes this software run on both Python 2 and 3 is heavily inspired and partly copy and pasted from the MIT-licensed six_ by Benjamin Peterson.
The only reason why it’s not used as a dependency is to avoid any runtime dependency in the first place.

.. _six: https://bitbucket.org/gutworth/six/
