Authors
-------

structlog is written and maintained by `Hynek Schlawack <http://hynek.me/>`_.
It’s inspired by previous work done by `Jean-Paul Calderone <http://as.ynchrono.us>`_ and `David Reid <http://dreid.org>`_.

The development is kindly made possible by `Variomedia AG <https://www.variomedia.de/>`_.

The following folks helped forming structlog into what it is now:

- `Alex Gaynor <https://github.com/alex>`_
- `Christopher Armstrong <https://github.com/radeex>`_
- `Daniel Lindsley <https://github.com/toastdriven>`_
- `David Reid <http://dreid.org>`_
- `Donald Stufft <https://github.com/dstufft>`_
- `Glyph <https://github.com/glyph>`_
- `Holger Krekel <https://github.com/hpk42>`_
- `Itamar Turner-Trauring <https://github.com/itamarst>`_
- `Jack Pearkes <https://github.com/pearkes>`_
- `Jean-Paul Calderone <http://as.ynchrono.us>`_
- `Lynn Root <https://github.com/econchick>`_
- `Noah Kantrowitz <https://github.com/coderanger>`_
- `Tarek Ziadé <https://github.com/tarekziade>`_
- `Thomas Heinrichsdobler <https://github.com/dertyp>`_
- `Tom Lazar <https://github.com/tomster>`_

Some of them disapprove of the addition of thread local context data. :)


Third Party Code
^^^^^^^^^^^^^^^^

The compatibility code that makes this software run on both Python 2 and 3 is heavily inspired and partly copy and pasted from the `MIT <http://choosealicense.com/licenses/mit/>`_-licensed `six <https://bitbucket.org/gutworth/six/>`_ by Benjamin Peterson.
The only reason why it’s not used as a dependency is to avoid any runtime dependency in the first place.
