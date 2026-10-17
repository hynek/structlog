# SPDX-License-Identifier: MIT OR Apache-2.0
# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

import json
import subprocess
import sys

from importlib import metadata

import pytest

import structlog


class TestLegacyMetadataHack:
    def test_version(self, recwarn):
        """
        structlog.__version__ returns the correct version and doesn't warn.
        """
        assert metadata.version("structlog") == structlog.__version__
        assert [] == recwarn.list

    def test_description(self):
        """
        structlog.__description__ returns the correct description.
        """
        with pytest.deprecated_call():
            assert "Structured Logging for Python" == structlog.__description__

    def test_uri(self):
        """
        structlog.__uri__ returns the correct project URL.
        """
        with pytest.deprecated_call():
            assert "https://www.structlog.org/" == structlog.__uri__

    def test_email(self):
        """
        structlog.__email__ returns Hynek's email address.
        """
        with pytest.deprecated_call():
            assert "hs@ox.cx" == structlog.__email__

    def test_does_not_exist(self):
        """
        Asking for unsupported dunders raises an AttributeError.
        """
        with pytest.raises(
            AttributeError, match="module structlog has no attribute __yolo__"
        ):
            structlog.__yolo__


@pytest.mark.skipif(
    sys.version_info < (3, 15), reason="PEP 810 lazy imports need Python 3.15+"
)
class TestLazyImports:
    def test_import_does_not_load_asyncio(self):
        """
        Importing structlog in a fresh interpreter does not import asyncio,
        because modules that are only needed when logging are imported lazily.
        """
        script = (
            "import json, sys\n"
            "before = set(sys.modules)\n"
            "import structlog\n"
            "print(json.dumps(sorted(set(sys.modules) - before)))\n"
        )
        out = subprocess.run(
            [sys.executable, "-c", script],
            check=True,
            capture_output=True,
            text=True,
        ).stdout

        assert "asyncio" not in json.loads(out)
