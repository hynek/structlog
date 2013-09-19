# Copyright 2013 Hynek Schlawack
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import, division, print_function

from structlog._loggers import PrintLogger, ReturnLogger


def test_return_logger():
    obj = ['hello']
    assert obj is ReturnLogger().msg(obj)


class TestPrintLogger(object):
    def test_prints_to_stdout_by_default(self, capsys):
        PrintLogger().msg('hello')
        out, err = capsys.readouterr()
        assert 'hello\n' == out
        assert '' == err

    def test_prints_to_correct_file(self, tmpdir, capsys):
        f = tmpdir.join('test.log')
        fo = f.open('w')
        PrintLogger(fo).msg('hello')
        out, err = capsys.readouterr()
        assert '' == out == err
        fo.close()
        assert 'hello\n' == f.read()

    def test_repr(self):
        assert repr(PrintLogger()).startswith(
            "<PrintLogger(file="
        )
