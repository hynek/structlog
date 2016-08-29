import logging

import pytest

from structlog.formatters import ProcessorFormatter


@pytest.fixture
def processor_factory(expected_rep):
    class TestArgs(object):
        def __call__(self, *args):
            self.args = list(args)
            return expected_rep
    return TestArgs()


class TestProcessorFormatter(object):

    def test_format__dict(self):
        """
        If ``record.msg`` is a dict, bound processor call result is returned.
        """
        logger = logging.getLogger(__name__)
        msg = {'foo': 'bar'}
        record = logger.makeRecord('foobar', logging.DEBUG, 'foo', 42,
                                   msg, (), False,
                                   extra={'_name': 'debug',
                                          '_logger': logger})
        expected_repr = 'Record representation'
        ppr = processor_factory(expected_repr)
        processor_formatter = ProcessorFormatter(ppr)

        actual_repr = processor_formatter.format(record)

        assert ppr.args == [record._logger, record._name, record.msg.copy()]
        assert expected_repr == actual_repr

    def test_format__not_dict(self):
        """
        If ``record.msg`` is not a dict, ``record.getMessage()`` result
        is returned.
        """
        logger = logging.getLogger(__name__)
        msg = 'not a dict'
        record = logger.makeRecord('foobar', logging.DEBUG, 'foo', 42,
                                   msg, (), False,
                                   extra={'_name': 'debug',
                                          '_logger': logger})
        expected_repr = record.getMessage()
        ppr = processor_factory(expected_repr)
        processor_formatter = ProcessorFormatter(ppr)

        actual_repr = processor_formatter.format(record)

        assert expected_repr == actual_repr
