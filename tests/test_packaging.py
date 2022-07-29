# SPDX-License-Identifier: MIT OR Apache-2.0
# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

import sys

import pytest

import structlog


if sys.version_info < (3, 8):
    import importlib_metadata as metadata
else:
    from importlib import metadata


class TestLegacyMetadataHack:
    def test_version(self):
        """
        structlog.__version__ returns the correct version.
        """
        with pytest.deprecated_call():
            assert metadata.version("structlog") == structlog.__version__

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
