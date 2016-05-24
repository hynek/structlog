# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

from setuptools import setup, find_packages

import codecs
import os
import re


###############################################################################

NAME = "structlog"
KEYWORDS = ["logging", "structured", "structure", "log"]
CLASSIFIERS = [
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: Apache Software License",
    "License :: OSI Approved :: MIT License",
    "Natural Language :: English",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 2",
    "Programming Language :: Python :: 2.7",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.4",
    "Programming Language :: Python :: 3.5",
    "Programming Language :: Python :: Implementation :: CPython",
    "Programming Language :: Python :: Implementation :: PyPy",
    "Programming Language :: Python",
    "Topic :: Software Development :: Libraries :: Python Modules",
]
INSTALL_REQUIRES = ["six"]
EXTRAS_REQUIRE = {
    "dev": ["colorama"],
}

###############################################################################

HERE = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    """
    Build an absolute path from *parts* and and return the contents of the
    resulting file.  Assume UTF-8 encoding.
    """
    with codecs.open(os.path.join(HERE, *parts), "rb", "utf-8") as f:
        return f.read()

try:
    PACKAGES
except NameError:
    PACKAGES = find_packages(where="src")

try:
    META_PATH
except NameError:
    META_PATH = os.path.join(HERE, "src", NAME, "__init__.py")
finally:
    META_FILE = read(META_PATH)


def find_meta(meta):
    """
    Extract __*meta*__ from META_FILE.
    """
    meta_match = re.search(
        r"^__{meta}__ = ['\"]([^'\"]*)['\"]".format(meta=meta),
        META_FILE, re.M
    )
    if meta_match:
        return meta_match.group(1)
    raise RuntimeError("Unable to find __{meta}__ string.".format(meta=meta))


VERSION = find_meta("version")
LONG = (
    read("README.rst") + "\n\n" +
    "Release Information\n" +
    "===================\n\n" +
    re.search("(\d+.\d.\d \(.*?\)\n.*?)\n\n\n----\n\n\n",
              read("CHANGELOG.rst"), re.S).group(1) +
    "\n\n`Full changelog " +
    "<http://www.structlog.org/en/stable/changelog.html>`_.\n\n" +
    read("AUTHORS.rst")
)

if __name__ == "__main__":
    setup(
        name=NAME,
        description=find_meta("description"),
        license=find_meta("license"),
        url=find_meta("uri"),
        version=VERSION,
        author=find_meta("author"),
        author_email=find_meta("email"),
        maintainer=find_meta("author"),
        maintainer_email=find_meta("email"),
        long_description=LONG,
        keywords=KEYWORDS,
        packages=PACKAGES,
        package_dir={"": "src"},
        classifiers=CLASSIFIERS,
        install_requires=INSTALL_REQUIRES,
        extras_require=EXTRAS_REQUIRE,
        zip_safe=False,
    )
