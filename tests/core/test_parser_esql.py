"""Tests for IBM ESQL parser."""

from __future__ import annotations

import pytest

from axon.core.parsers.base import ParseResult
from axon.core.parsers.esql_lang import ESQLParser


@pytest.fixture
def parser() -> ESQLParser:
    return ESQLParser()


class TestParseSimpleProcedure:
    CODE = """\
CREATE PROCEDURE MyProcedure()
BEGIN
    DECLARE @result INT;
    SET @result = 1;
END;
"""

    def test_symbol_count(self, parser: ESQLParser) -> None:
        result = parser.parse(self.CODE, "test.esql")
        assert len(result.symbols) == 1

    def test_procedure_name(self, parser: ESQLParser) -> None:
        result = parser.parse(self.CODE, "test.esql")
        assert result.symbols[0].name == "MyProcedure"

    def test_procedure_kind(self, parser: ESQLParser) -> None:
        result = parser.parse(self.CODE, "test.esql")
        assert result.symbols[0].kind == "function"

    def test_procedure_lines(self, parser: ESQLParser) -> None:
        result = parser.parse(self.CODE, "test.esql")
        assert result.symbols[0].start_line == 1
        assert result.symbols[0].end_line >= 5


class TestParseFunction:
    CODE = """\
CREATE FUNCTION GetValue()
RETURNS INT
BEGIN
    RETURN 42;
END;
"""

    def test_function_extracted(self, parser: ESQLParser) -> None:
        result = parser.parse(self.CODE, "test.esql")
        assert len(result.symbols) == 1
        assert result.symbols[0].name == "GetValue"
        assert result.symbols[0].kind == "function"


class TestParseCallStatements:
    CODE = """\
CREATE PROCEDURE Main()
BEGIN
    CALL MyProcedure();
    CALL AnotherProc();
END;
"""

    def test_calls_extracted(self, parser: ESQLParser) -> None:
        result = parser.parse(self.CODE, "test.esql")
        call_names = [c.name for c in result.calls]
        assert "MyProcedure" in call_names
        assert "AnotherProc" in call_names


class TestParseModule:
    CODE = """\
CREATE MODULE MyModule
BEGIN
    CREATE PROCEDURE Proc1() BEGIN END;
END;
"""

    def test_module_extracted(self, parser: ESQLParser) -> None:
        result = parser.parse(self.CODE, "test.esql")
        # Should have at least the module
        modules = [s for s in result.symbols if s.kind == "class"]
        assert any(m.name == "MyModule" for m in modules)


class TestEdgeCases:
    def test_empty_file(self, parser: ESQLParser) -> None:
        result = parser.parse("", "empty.esql")
        assert isinstance(result, ParseResult)
        assert len(result.symbols) == 0

    def test_syntax_error_does_not_crash(self, parser: ESQLParser) -> None:
        code = "CREATE PROCEDURE Broken("
        result = parser.parse(code, "broken.esql")
        # Should return empty ParseResult, not crash
        assert isinstance(result, ParseResult)