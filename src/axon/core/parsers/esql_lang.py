"""IBM ESQL language parser using regex patterns.

Extracts procedures, functions, modules, and CALL statements
from IBM ESQL source code without tree-sitter dependency.
"""

from __future__ import annotations

import re

from axon.core.parsers.base import (
    CallInfo,
    LanguageParser,
    ParseResult,
    SymbolInfo,
)


class ESQLParser(LanguageParser):
    """Parses IBM ESQL using regex patterns.
    
    Extracts:
    - CREATE PROCEDURE definitions -> "procedure" kind
    - CREATE FUNCTION definitions -> "function" kind
    - CREATE MODULE definitions -> "module" kind
    - CREATE ROUTE definitions -> "route" kind
    - CALL statements
    """

    # Regex patterns for ESQL constructs
    PROCEDURE_PATTERN = re.compile(
        r'CREATE\s+PROCEDURE\s+(\w+)\s*\(',
        re.IGNORECASE | re.MULTILINE,
    )
    FUNCTION_PATTERN = re.compile(
        r'CREATE\s+FUNCTION\s+(\w+)\s*\(',
        re.IGNORECASE | re.MULTILINE,
    )
    MODULE_PATTERN = re.compile(
        r'CREATE\s+MODULE\s+(\w+)',
        re.IGNORECASE | re.MULTILINE,
    )
    ROUTE_PATTERN = re.compile(
        r'CREATE\s+ROUTE\s+(\w+)',
        re.IGNORECASE | re.MULTILINE,
    )
    CALL_PATTERN = re.compile(
        r'CALL\s+(\w+)\s*\(',
        re.IGNORECASE | re.MULTILINE,
    )

    def parse(self, content: str, file_path: str) -> ParseResult:
        """Parse ESQL source and return structured information."""
        result = ParseResult()

        # Extract procedures with kind="procedure" (not "function")
        self._extract_matches(
            content,
            self.PROCEDURE_PATTERN,
            result,
            kind="procedure",
        )

        # Extract functions with kind="function"
        self._extract_matches(
            content,
            self.FUNCTION_PATTERN,
            result,
            kind="function",
        )

        # Extract modules with kind="module" (not "class")
        self._extract_matches(
            content,
            self.MODULE_PATTERN,
            result,
            kind="module",
        )

        # Extract routes with kind="route"
        self._extract_matches(
            content,
            self.ROUTE_PATTERN,
            result,
            kind="route",
        )

        # Extract CALL statements
        self._extract_calls(content, result)

        return result

    def _extract_matches(
        self,
        content: str,
        pattern: re.Pattern,
        result: ParseResult,
        kind: str,
    ) -> None:
        """Extract symbol definitions matching a regex pattern."""
        for match in pattern.finditer(content):
            name = match.group(1)
            start_line = content[: match.start()].count("\n") + 1
            
            # Find the END; statement to determine end line
            end_pos = self._find_end_position(content, match.end())
            end_line = content[:end_pos].count("\n") + 1
            
            # Extract the full content of this definition
            definition_content = content[match.start() : end_pos]

            result.symbols.append(
                SymbolInfo(
                    name=name,
                    kind=kind,
                    start_line=start_line,
                    end_line=end_line,
                    content=definition_content,
                    signature=match.group(0).strip(),
                )
            )

    def _find_end_position(self, content: str, start_pos: int) -> int:
        """Find the position of the END; statement after start_pos."""
        # Look for END; pattern
        end_pattern = re.compile(r'\bEND\s*;', re.IGNORECASE)
        match = end_pattern.search(content, start_pos)
        if match:
            return match.end()
        # Fallback: return end of content
        return len(content)

    def _extract_calls(self, content: str, result: ParseResult) -> None:
        """Extract CALL statements from content."""
        for match in self.CALL_PATTERN.finditer(content):
            name = match.group(1)
            line = content[: match.start()].count("\n") + 1

            result.calls.append(
                CallInfo(
                    name=name,
                    line=line,
                    arguments=[],
                )
            )