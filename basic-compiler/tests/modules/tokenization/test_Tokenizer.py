from pathlib import Path
from unittest.mock import call, MagicMock

import pytest

from basic_compiler.fsm import FsmError
from basic_compiler.modules.tokenization.AsciiCategorizer import AsciiCategorizer
from basic_compiler.modules.tokenization.Tokenizer import Tokenizer


@pytest.mark.parametrize('source_line,tokens', [
    (('ascii_line', '1 IF S(P) = 0 THEN GOTO 3\n'), [
        call(('number', '1')),
        call(('identifier', 'IF')),
        call(('variable', 'S')),
        call(('special', '(')),
        call(('variable', 'P')),
        call(('special', ')')),
        call(('special', '=')),
        call(('number', '0')),
        call(('identifier', 'THEN')),
        call(('identifier', 'GOTO')),
        call(('number', '3')),
        call(('end_of_line', '\n')),
    ]),
    (('ascii_line', '1 IF S2(P) <= -5 THEN GOTO 3\n'), [
        call(('number', '1')),
        call(('identifier', 'IF')),
        call(('variable', 'S2')),
        call(('special', '(')),
        call(('variable', 'P')),
        call(('special', ')')),
        call(('special', '<=')),
        call(('special', '-')),
        call(('number', '5')),
        call(('identifier', 'THEN')),
        call(('identifier', 'GOTO')),
        call(('number', '3')),
        call(('end_of_line', '\n')),
    ]),
    (('ascii_line', '-1.23E-4\n'), [
        call(('special', '-')),
        call(('number', '1.23E-4')),
    ]),
    (('ascii_line', '-1.2.3E-4.5E6\n'), [
        call(('special', '-')),
        call(('number', '1.2.3E-4.5E6')),
    ]),
])
def test_filters_ascii_chars(source_line, tokens):
    add_external_event = MagicMock()
    tokenizer = Tokenizer(add_external_event)
    categorizer = AsciiCategorizer(tokenizer.handle_event)
    categorizer.handle_event(source_line)
    tokenizer.handle_event(('eof', None))
    for event in categorizer:
        categorizer.handle_event(event)
    add_external_event.assert_has_calls(tokens)


@pytest.mark.parametrize('source_line,expected_call', [
    (('ascii_line', 'A\n'), ('variable', 'A')),
    (('ascii_line', 'X1\n'), ('variable', 'X1')),
    (('ascii_line', 'GO\n'), ('identifier', 'GO')),
    (('ascii_line', 'GOTO\n'), ('identifier', 'GOTO')),
])
def test_identifier_vs_variable(source_line, expected_call):
    add_external_event = MagicMock()
    tokenizer = Tokenizer(add_external_event)
    categorizer = AsciiCategorizer(tokenizer.handle_event)
    categorizer.handle_event(source_line)
    for event in categorizer:
        categorizer.handle_event(event)
    add_external_event.assert_has_calls([call(expected_call)])


@pytest.mark.xfail(raises=FsmError)
def test_fail_at_invalid_identifier():
    add_external_event = MagicMock()
    tokenizer = Tokenizer(add_external_event)
    tokenizer.handle_event(('ascii_character', 'X'))
    tokenizer.handle_event(('ascii_character', 'Y'))
    tokenizer.handle_event(('ascii_digit', '0'))
    tokenizer.handle_event(('ascii_ctrl', '\n'))


@pytest.mark.parametrize('source_line,expected_call', [
    (('ascii_line', '"String 0 X1 y14"\n'), ('string', '"String 0 X1 y14"')),
    (('ascii_line', '"String with ""escaped double quote"""\n'), ('string', '"String with ""escaped double quote"""')),
])
def test_string(source_line, expected_call):
    add_external_event = MagicMock()
    tokenizer = Tokenizer(add_external_event)
    categorizer = AsciiCategorizer(tokenizer.handle_event)
    categorizer.handle_event(source_line)
    for event in categorizer:
        categorizer.handle_event(event)
    add_external_event.assert_has_calls([call(expected_call)])


@pytest.mark.parametrize('source_line', [
    ('ascii_line', '"""\n'),
    ('ascii_line', '"\n"\n'),
])
@pytest.mark.xfail(raises=FsmError)
def test_invalid_string(source_line):
    add_external_event = MagicMock()
    tokenizer = Tokenizer(add_external_event)
    categorizer = AsciiCategorizer(tokenizer.handle_event)
    categorizer.handle_event(source_line)
    tokenizer.handle_event(('eof', None))
    for event in categorizer:
        categorizer.handle_event(event)


@pytest.mark.parametrize('source_line,expected_call', [
    (('ascii_line', '10\n'), [call(('number', '10'))]),
    (('ascii_line', '-20\n'), [call(('special', '-')), call(('number', '20'))]),
    (('ascii_line', '30\n'), [call(('number', '30'))]),
    (('ascii_line', '3.14E-0\n'), [call(('number', '3.14E-0'))]),
    (('ascii_line', '-.5\n'), [call(('special', '-')), call(('number', '.5'))]),
])
def test_numbers(source_line,expected_call):
    add_external_event = MagicMock()
    tokenizer = Tokenizer(add_external_event)
    categorizer = AsciiCategorizer(tokenizer.handle_event)
    categorizer.handle_event(source_line)
    for event in categorizer:
        categorizer.handle_event(event)
    add_external_event.assert_has_calls(expected_call)
