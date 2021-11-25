# How To Contribute

First off, thank you for considering contributing to `structlog`!
It's people like *you* who make it such a great tool for everyone.

This document intends to make contribution more accessible by codifying tribal knowledge and expectations.
Don't be afraid to open half-finished PRs, and ask questions if something is unclear!

Please note that this project is released with a Contributor [Code of Conduct](https://github.com/hynek/structlog/blob/main/.github/CODE_OF_CONDUCT.md).
By participating in this project you agree to abide by its terms.
Please report any harm to [Hynek Schlawack] in any way you find appropriate.


## Workflow

- No contribution is too small!
  Please submit as many fixes for typos and grammar bloopers as you can!
- Try to limit each pull request to *one* change only.
- Since we squash on merge, it's up to you how you handle updates to the main branch.
  Whether you prefer to rebase on main or merge main into your branch, do whatever is more comfortable for you.
- *Always* add tests and docs for your code.
  This is a hard rule; patches with missing tests or documentation can't be merged.
- Make sure your changes pass our [CI].
  You won't get any feedback until it's green unless you ask for it.
- Once you've addressed review feedback, make sure to bump the pull request with a short note, so we know you're done.
- Don’t break [backward compatibility](https://structlog.org/en/latest/backward-compatibility.html).


## Code

- Obey [PEP 8](https://www.python.org/dev/peps/pep-0008/) and [PEP 257](https://www.python.org/dev/peps/pep-0257/).
  We use the `"""`-on-separate-lines style for docstrings:

  ```python
  def func(x):
      """
      Do something.

      :param str x: A very important parameter.

      :rtype: str
      """
  ```
- If you add or change public APIs, tag the docstring using `..  versionadded:: 16.0.0 WHAT` or `..  versionchanged:: 16.2.0 WHAT`.
- We use [*isort*](https://github.com/PyCQA/isort) to sort our imports, and we use [*Black*](https://github.com/psf/black) with line length of 79 characters to format our code.
  As long as you run our full [*tox*] suite before committing, or install our [*pre-commit*] hooks (ideally you'll do both – see [*Local Development Environment*](#local-development-environment) below), you won't have to spend any time on formatting your code at all.
  If you don't, [CI] will catch it for you – but that seems like a waste of your time!


## Tests

- Write your asserts as `expected == actual` to line them up nicely:

  ```python
  x = f()

  assert 42 == x.some_attribute
  assert "foo" == x._a_private_attribute
  ```

- To run the test suite, all you need is a recent [*tox*].
  It will ensure the test suite runs with all dependencies against all Python versions just as it will in our [CI].
  If you lack some Python versions, you can can always limit the environments like `tox -e py38,py39`, or make it a non-failure using `tox --skip-missing-interpreters`.

  In that case you should look into [*asdf*](https://asdf-vm.com) or [*pyenv*](https://github.com/pyenv/pyenv), which make it very easy to install many different Python versions in parallel.
- Write [good test docstrings](https://jml.io/pages/test-docstrings.html).
- To ensure new features work well with the rest of the system, they should be also added to our [*Hypothesis*](https://hypothesis.readthedocs.io/) testing strategy, which can be found in `tests/strategies.py`.
- If you've changed or added public APIs, please update our type stubs (files ending in `.pyi`).


## Documentation

- Use [semantic newlines] in [*reStructuredText*] files (files ending in `.rst`):

  ```rst
  This is a sentence.
  This is another sentence.
  ```

- If you start a new section, add two blank lines before and one blank line after the header, except if two headers follow immediately after each other:

  ```rst
  Last line of previous section.


  Header of New Top Section
  -------------------------

  Header of New Section
  ^^^^^^^^^^^^^^^^^^^^^

  First line of new section.
  ```


### Changelog

If your change is noteworthy, there needs to be a changelog entry in `CHANGELOG.rst` so our users can learn about it!

- As with other docs, please use [semantic newlines] in the changelog.
- Wrap symbols like modules, functions, or classes into double backticks so they are rendered in a `monospace font`.
- Wrap arguments into asterisks like in docstrings:
  `Added new argument *an_argument*.`
- If you mention functions or other callables, add parentheses at the end of their names:
  `structlog.func()` or `structlog.Class.method()`.
  This makes the changelog a lot more readable.
- Prefer simple past tense or constructions with "now".
  For example:

  + Added ``structlog.func()``.
  + ``structlog.func()`` now doesn't crash the Large Hadron Collider anymore when passed the *foobar* argument.

Example entries:

```rst
Added ``structlog.func()``.
The feature really *is* awesome.
```

or:

```rst
``structlog.func()`` now doesn't crash the Large Hadron Collider anymore when passed the *foobar* argument.
The bug really *was* nasty.
```


## Local Development Environment

You can (and should) run our test suite using [*tox*].
However, you’ll probably want a more traditional environment as well.
We highly recommend to develop using the latest Python release because we try to take advantage of modern features whenever possible.

First create a [virtual environment](https://virtualenv.pypa.io/) so you don't break your system-wide Python installation.
It’s out of scope for this document to list all the ways to manage virtual environments in Python, but if you don’t already have a pet way, take some time to look at tools like [*direnv*](https://github.com/direnv/direnv/wiki/Python), [*virtualfish*](https://virtualfish.readthedocs.io/), and [*virtualenvwrapper*](https://virtualenvwrapper.readthedocs.io/).

Next, get an up to date checkout of the *structlog* repository:

```console
$ git clone git@github.com:hynek/structlog.git
```

or if you want to use git via `https`:

```console
$ git clone https://github.com/hynek/structlog.git
```

Change into the newly created directory and **after activating your virtual environment** install an editable version of *structlog* along with its tests and docs requirements:

```console
$ cd structlog
$ pip install --upgrade pip setuptools  # PLEASE don't skip this step
$ pip install -e '.[dev]'
```

At this point,

```console
$ python -m pytest
```

should work and pass, as should:

```console
$ cd docs
$ make html
```

The built documentation can then be found in `docs/_build/html/`.

To avoid committing code that violates our style guide, we strongly advise you to install [*pre-commit*] [^dev] hooks:

```console
$ pre-commit install
```

You can also run them anytime (as our tox does) using:

```console
$ pre-commit run --all-files
```

[^dev]: *pre-commit* should have been installed into your virtualenv automatically when you ran `pip install -e '.[dev]'` above.
        If *pre-commit* is missing, your probably need to run `pip install -e '.[dev]'` again.


[CI]: https://github.com/hynek/structlog/actions
[Hynek Schlawack]: https://hynek.me/about/
[*pre-commit*]: https://pre-commit.com/
[*tox*]: https://https://tox.wiki/
[semantic newlines]: https://rhodesmill.org/brandon/2012/one-sentence-per-line/
[*reStructuredText*]: https://www.sphinx-doc.org/en/stable/usage/restructuredtext/basics.html
