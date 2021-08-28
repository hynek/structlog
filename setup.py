# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

import codecs
import os
import re

from setuptools import find_packages, setup


###############################################################################

NAME = "structlog"
KEYWORDS = ["logging", "structured", "structure", "log"]
PROJECT_URLS = {
    "Documentation": "https://www.structlog.org/",
    "Bug Tracker": "https://github.com/hynek/structlog/issues",
    "Source Code": "https://github.com/hynek/structlog",
    "Funding": "https://github.com/sponsors/hynek",
    "Tidelift": "https://tidelift.com/subscription/pkg/pypi-structlog?"
    "utm_source=pypi-structlog&utm_medium=pypi",
    "Ko-fi": "https://ko-fi.com/the_hynek",
}
CLASSIFIERS = [
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: Apache Software License",
    "License :: OSI Approved :: MIT License",
    "Natural Language :: English",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: Implementation :: CPython",
    "Programming Language :: Python :: Implementation :: PyPy",
    "Programming Language :: Python",
    "Topic :: Software Development :: Libraries :: Python Modules",
]
PYTHON_REQUIRES = ">=3.6"
INSTALL_REQUIRES = [
    "typing-extensions; python_version<'3.8'",
]
EXTRAS_REQUIRE = {
    "tests": [
        "coverage[toml]",
        "freezegun>=0.2.8",
        "pretend",
        "pytest-asyncio",
        "pytest>=6.0",
        "simplejson",
    ],
    "docs": ["furo", "sphinx", "twisted"],
}
EXTRAS_REQUIRE["dev"] = (
    EXTRAS_REQUIRE["tests"] + EXTRAS_REQUIRE["docs"] + ["pre-commit"]
)

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
        fr"^__{meta}__ = ['\"]([^'\"]*)['\"]", META_FILE, re.M
    )
    if meta_match:
        return meta_match.group(1)
    raise RuntimeError(f"Unable to find __{ meta }__ string.")


VERSION = find_meta("version")
LONG = (
    "==============================================\n"
    "``structlog``: : Structured Logging for Python\n"
    "==============================================\n"
    + read("README.rst").split(".. -begin-short-")[1]
    + "\n\n"
    + "Release Information\n"
    + "===================\n\n"
    + re.search(
        r"(\d+.\d.\d \(.*?\)\r?\n.*?)\r?\n\r?\n\r?\n----\r?\n\r?\n\r?\n",
        read("CHANGELOG.rst"),
        re.S,
    ).group(1)
    + "\n\n`Full changelog "
    + "<https://www.structlog.org/en/stable/changelog.html>`_.\n\n"
    + read("AUTHORS.rst")
)

if __name__ == "__main__":
    setup(
        name=NAME,
        description=find_meta("description"),
        license=find_meta("license"),
        url=find_meta("uri"),
        project_urls=PROJECT_URLS,
        version=VERSION,
        author=find_meta("author"),
        author_email=find_meta("email"),
        maintainer=find_meta("author"),
        maintainer_email=find_meta("email"),
        long_description=LONG,
        long_description_content_type="text/x-rst",
        keywords=KEYWORDS,
        packages=PACKAGES,
        package_dir={"": "src"},
        classifiers=CLASSIFIERS,
        python_requires=PYTHON_REQUIRES,
        install_requires=INSTALL_REQUIRES,
        extras_require=EXTRAS_REQUIRE,
        include_package_data=True,
        zip_safe=False,
        options={"bdist_wheel": {"universal": "1"}},
    )
