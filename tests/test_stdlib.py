# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

from __future__ import absolute_import, division, print_function

import os

import logging

import pytest
from pretend import call_recorder

from structlog._loggers import ReturnLogger
from structlog.exceptions import DropEvent
from structlog.stdlib import (
    BoundLogger,
    CRITICAL,
    LoggerFactory,
    PositionalArgumentsFormatter,
    WARN,
    filter_by_level,
    add_log_level,
    add_logger_name,
    _FixedFindCallerLogger,
)

from .additional_frame import additional_frame
from .utils import py3_only


def build_bl(logger=None, processors=None, context=None):
    """
    Convenience function to build BoundLogger with sane defaults.
    """
    return BoundLogger(
        logger or ReturnLogger(),
        processors,
        {}
    )


def return_method_name(_, method_name, __):
    """
    A final renderer that returns the name of the logging method.
    """
    return method_name


class TestLoggerFactory(object):
    def setup_method(self, method):
        """
        The stdlib logger factory modifies global state to fix caller
        identification.
        """
        self.original_logger = logging.getLoggerClass()

    def teardown_method(self, method):
        logging.setLoggerClass(self.original_logger)

    def test_deduces_correct_name(self):
        """
        The factory isn't called directly but from structlog._config so
        deducing has to be slightly smarter.
        """
        assert 'tests.additional_frame' == (
            additional_frame(LoggerFactory()).name
        )
        assert 'tests.test_stdlib' == LoggerFactory()().name

    def test_ignores_frames(self):
        """
        The name guesser walks up the frames until it reaches a frame whose
        name is not from structlog or one of the configurable other names.
        """
        assert '__main__' == additional_frame(LoggerFactory(
            ignore_frame_names=['tests.', '_pytest.'])
        ).name

    def test_deduces_correct_caller(self):
        logger = _FixedFindCallerLogger('test')
        file_name, line_number, func_name = logger.findCaller()[:3]
        assert file_name == os.path.realpath(__file__)
        assert func_name == 'test_deduces_correct_caller'

    @py3_only
    def test_stack_info(self):
        logger = _FixedFindCallerLogger('test')
        testing, is_, fun, stack_info = logger.findCaller(stack_info=True)
        assert 'testing, is_, fun' in stack_info

    @py3_only
    def test_no_stack_info_by_default(self):
        logger = _FixedFindCallerLogger('test')
        testing, is_, fun, stack_info = logger.findCaller()
        assert None is stack_info

    def test_find_caller(self, monkeypatch):
        logger = LoggerFactory()()
        log_handle = call_recorder(lambda x: None)
        monkeypatch.setattr(logger, 'handle', log_handle)
        logger.error('Test')
        log_record = log_handle.calls[0].args[0]
        assert log_record.funcName == 'test_find_caller'
        assert log_record.name == __name__
        assert log_record.filename == os.path.basename(__file__)

    def test_sets_correct_logger(self):
        assert logging.getLoggerClass() is logging.Logger
        LoggerFactory()
        assert logging.getLoggerClass() is _FixedFindCallerLogger

    def test_positional_argument_avoids_guessing(self):
        """
        If a positional argument is passed to the factory, it's used as the
        name instead of guessing.
        """
        l = LoggerFactory()('foo')
        assert 'foo' == l.name


class TestFilterByLevel(object):
    def test_filters_lower_levels(self):
        logger = logging.Logger(__name__)
        logger.setLevel(CRITICAL)
        with pytest.raises(DropEvent):
            filter_by_level(logger, 'warn', {})

    def test_passes_higher_levels(self):
        logger = logging.Logger(__name__)
        logger.setLevel(WARN)
        event_dict = {'event': 'test'}
        assert event_dict is filter_by_level(logger, 'warn', event_dict)
        assert event_dict is filter_by_level(logger, 'error', event_dict)
        assert event_dict is filter_by_level(logger, 'exception', event_dict)


class TestBoundLogger(object):
    @pytest.mark.parametrize(('method_name'), [
        'debug', 'info', 'warning', 'error', 'critical',
    ])
    def test_proxies_to_correct_method(self, method_name):
        """
        The basic proxied methods are proxied to the correct counterparts.
        """
        bl = BoundLogger(ReturnLogger(), [return_method_name], {})
        assert method_name == getattr(bl, method_name)('event')

    def test_proxies_exception(self):
        """
        BoundLogger.exception is proxied to Logger.error.
        """
        bl = BoundLogger(ReturnLogger(), [return_method_name], {})
        assert "error" == bl.exception("event")

    def test_proxies_log(self):
        """
        BoundLogger.exception.log() is proxied to the apropriate method.
        """
        bl = BoundLogger(ReturnLogger(), [return_method_name], {})
        assert "critical" == bl.log(50, "event")
        assert "debug" == bl.log(10, "event")

    def test_positional_args_proxied(self):
        """
        Positional arguments supplied are proxied as kwarg.
        """
        bl = BoundLogger(ReturnLogger(), [], {})
        args, kwargs = bl.debug('event', 'foo', bar='baz')
        assert 'baz' == kwargs.get('bar')
        assert ('foo',) == kwargs.get('positional_args')

    @pytest.mark.parametrize('method_name,method_args', [
        ('addHandler', [None]),
        ('removeHandler', [None]),
        ('hasHandlers', None),
        ('callHandlers', [None]),
        ('handle', [None]),
        ('setLevel', [None]),
        ('getEffectiveLevel', None),
        ('isEnabledFor', [None]),
        ('findCaller', None),
        ('makeRecord', ['name', 'debug', 'test_func', '1',
                        'test msg', ['foo'], False]),
        ('getChild', [None]),
        ])
    def test_stdlib_passthrough_methods(self, method_name, method_args):
        """
        stdlib logger methods are also available in stdlib BoundLogger.
        """
        called_stdlib_method = [False]

        def validate(*args, **kw):
            called_stdlib_method[0] = True

        stdlib_logger = logging.getLogger('Test')
        stdlib_logger_method = getattr(stdlib_logger, method_name, None)
        if stdlib_logger_method:
            setattr(stdlib_logger, method_name, validate)
            bl = BoundLogger(stdlib_logger, [], {})
            bound_logger_method = getattr(bl, method_name)
            assert bound_logger_method is not None
            if method_args:
                bound_logger_method(*method_args)
            else:
                bound_logger_method()
            assert called_stdlib_method[0] is True

    def test_exception_exc_info(self):
        """
        BoundLogger.exception sets exc_info=True.
        """
        bl = BoundLogger(ReturnLogger(), [], {})
        assert ((),
                {"exc_info": True, "event": "event"}) == bl.exception('event')

    def test_exception_maps_to_error(self):
        bl = BoundLogger(ReturnLogger(), [return_method_name], {})
        assert "error" == bl.exception("event")


class TestPositionalArgumentsFormatter(object):
    def test_formats_tuple(self):
        """
        Positional arguments as simple types are rendered.
        """
        formatter = PositionalArgumentsFormatter()
        event_dict = formatter(None, None, {'event': '%d %d %s',
                                            'positional_args': (1, 2, 'test')})
        assert '1 2 test' == event_dict['event']
        assert 'positional_args' not in event_dict

    def test_formats_dict(self):
        """
        Positional arguments as dict are rendered.
        """
        formatter = PositionalArgumentsFormatter()
        event_dict = formatter(None, None, {'event': '%(foo)s bar',
                                            'positional_args': (
                                                {'foo': 'bar'},)})
        assert 'bar bar' == event_dict['event']
        assert 'positional_args' not in event_dict

    def test_positional_args_retained(self):
        """
        Positional arguments are retained if remove_positional_args
        argument is set to False.
        """
        formatter = PositionalArgumentsFormatter(remove_positional_args=False)
        positional_args = (1, 2, 'test')
        event_dict = formatter(
            None, None,
            {'event': '%d %d %s', 'positional_args': positional_args})
        assert 'positional_args' in event_dict
        assert positional_args == event_dict['positional_args']

    def test_nop_no_args(self):
        """
        If no positional args are passed, nothing happens.
        """
        formatter = PositionalArgumentsFormatter()
        assert {} == formatter(None, None, {})


class TestAddLogLevel(object):
    def test_log_level_added(self):
        """
        The log level is added to the event dict.
        """
        event_dict = add_log_level(None, 'error', {})
        assert 'error' == event_dict['level']

    def test_log_level_alias_normalized(self):
        """
        The normalized name of the log level is added to the event dict.
        """
        event_dict = add_log_level(None, 'warn', {})
        assert 'warning' == event_dict['level']


class TestAddLoggerName(object):
    def test_logger_name_added(self):
        """
        The logger name is added to the event dict.
        """
        name = 'sample-name'
        logger = logging.getLogger(name)
        event_dict = add_logger_name(logger, None, {})
        assert name == event_dict['logger']
