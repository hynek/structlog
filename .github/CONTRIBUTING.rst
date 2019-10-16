How To Contribute
=================

First off, thank you for considering contributing to ``structlog``!
It's people like *you* who make it is such a great tool for everyone.

This document is mainly to help you to get started by codifying tribal knowledge and expectations and make it more accessible to everyone.
But don't be afraid to open half-finished PRs and ask questions if something is unclear!


Support
-------

In case you'd like to help out but don't want to deal with GitHub, there's a great opportunity:
help your fellow developers on `StackOverflow <https://stackoverflow.com/questions/tagged/structlog>`_!

The offical tag is ``structlog`` and helping out in support frees us up to improve ``structlog`` instead!


Workflow
--------

- No contribution is too small!
  Please submit as many fixes for typos and grammar bloopers as you can!
- Try to limit each pull request to *one* change only.
- *Always* add tests and docs for your code.
  This is a hard rule; patches with missing tests or documentation can't be merged.
- Make sure your changes pass our CI_.
  You won't get any feedback until it's green unless you ask for it.
- Once you've addressed review feedback, make sure to bump the pull request with a short note, so we know you're done.
- Don’t break `backward compatibility`_.


Code
----

- Obey `PEP 8`_ and `PEP 257`_.
  We use the ``"""``\ -on-separate-lines style for docstrings:

  .. code-block:: python

     def func(x):
         """
         Do something.

         :param str x: A very important parameter.

         :rtype: str
         """
- If you add or change public APIs, tag the docstring using ``..  versionadded:: 16.0.0 WHAT`` or ``..  versionchanged:: 17.1.0 WHAT``.
- We use isort_ to sort our imports, and we follow the Black_ code style with a line length of 79 characters.
  As long as you run our full tox suite before committing, or install our pre-commit_ hooks (ideally you'll do both -- see below "Local Development Environment"), you won't have to spend any time on formatting your code at all.
  If you don't, CI will catch it for you -- but that seems like a waste of your time!


Tests
-----

- Write your asserts as ``expected == actual`` to line them up nicely and leave an empty line before them:

  .. code-block:: python

     x = f()

     assert 42 == x.some_attribute
     assert "foo" == x._a_private_attribute

- To run the test suite, all you need is a recent tox_.
  It will ensure the test suite runs with all dependencies against all Python versions just as it will in our CI.
  If you lack some Python versions, you can can make it a non-failure using ``tox --skip-missing-interpreters`` (in that case you may want to look into pyenv_ that makes it very easy to install many different Python versions in parallel).
- Write `good test docstrings`_.


Documentation
-------------

- Use `semantic newlines`_ in reStructuredText_ files (files ending in ``.rst``):

  .. code-block:: rst

     This is a sentence.
     This is another sentence.

- If you start a new section, add two blank lines before and one blank line after the header except if two headers follow immediately after each other:

  .. code-block:: rst

     Last line of previous section.


     Header of New Top Section
     -------------------------

     Header of New Section
     ^^^^^^^^^^^^^^^^^^^^^

     First line of new section.
- If your change is noteworthy, add an entry to the changelog_.
  Use `semantic newlines`_, and add a link to your pull request:

  .. code-block:: rst

     - Added ``structlog.func()`` that does foo.
       It's pretty cool.
       [`#1 <https://github.com/hynek/structlog/pull/1>`_]
     - ``structlog.func()`` now doesn't crash the Large Hadron Collider anymore.
       That was a nasty bug!
       [`#2 <https://github.com/hynek/structlog/pull/2>`_]


Local Development Environment
-----------------------------

You can (and should) run our test suite using tox_.
However, you’ll probably want a more traditional environment as well.
We highly recommend to develop using the latest Python 3 release because you're more likely to catch certain bugs earlier.

First create a `virtual environment <https://virtualenv.pypa.io/>`_.
It’s out of scope for this document to list all the ways to manage virtual environments in Python but if you don’t have already a pet way, take some time to look at tools like `pew <https://github.com/berdario/pew>`_, `virtualfish <https://virtualfish.readthedocs.io/>`_, and `virtualenvwrapper <https://virtualenvwrapper.readthedocs.io/>`_.

Next get an up to date checkout of the ``structlog`` repository:

.. code-block:: bash

    $ git checkout git@github.com:hynek/structlog.git

Change into the newly created directory and **after activating your virtual environment** install an editable version of ``structlog`` along with its test and docs dependencies:

.. code-block:: bash

    $ cd structlog
    $ pip install -e .[dev]

If you run the virtual environment’s Python and try to ``import structlog`` it should work!

At this point

.. code-block:: bash

   $ python -m pytest

should work and pass

and

.. code-block:: bash

   $ cd docs
   $ make html


should build docs in ``docs/_build/html``.

To avoid committing code that violates our style guide, we strongly advise you to install pre-commit_ [#f1]_ hooks:

.. code-block:: bash

   $ pre-commit install

You can also run them anytime using:

.. code-block:: bash

   $ pre-commit run --all-files

.. [#f1] pre-commit should have been installed into your virtualenv automatically when you ran ``pip install -e '.[dev]'`` above.
   If pre-commit is missing, it may be that you need to re-run ``pip install -e '.[dev]'``.

****

Again, this list is mainly to help you to get started by codifying tribal knowledge and expectations.
If something is unclear, feel free to ask for help!

Please note that this project is released with a Contributor `Code of Conduct`_.
By participating in this project you agree to abide by its terms.
Please report any harm to `Hynek Schlawack`_ in any way you find appropriate.

Thank you for considering contributing to ``structlog``!


.. _`Hynek Schlawack`: https://hynek.me/about/
.. _`PEP 8`: https://www.python.org/dev/peps/pep-0008/
.. _`PEP 257`: https://www.python.org/dev/peps/pep-0257/
.. _`good test docstrings`: https://jml.io/pages/test-docstrings.html
.. _`Code of Conduct`: https://github.com/hynek/structlog/blob/master/.github/CODE_OF_CONDUCT.rst
.. _changelog: https://github.com/hynek/structlog/blob/master/CHANGELOG.rst
.. _`backward compatibility`: https://www.structlog.org/en/latest/backward-compatibility.html
.. _tox: https://tox.readthedocs.io/
.. _pyenv: https://github.com/pyenv/pyenv
.. _reStructuredText: https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html
.. _semantic newlines: https://rhodesmill.org/brandon/2012/one-sentence-per-line/
.. _CI: https://dev.azure.com/the-hynek/structlog/_build?definitionId=1
.. _black: https://github.com/psf/black
.. _pre-commit: https://pre-commit.com/
.. _isort: https://github.com/timothycrosley/isort
