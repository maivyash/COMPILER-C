from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


KEYWORDS = {
	"int",
	"return",
	"if",
	"else",
	"while",
	"void",
	"extern",
}


SYMBOLS = {
	"+",
	"-",
	"*",
	"/",
	"%",
	"=",
	"==",
	"!=",
	"<",
	"<=",
	">",
	">=",
	"&&",
	"||",
	"!",
	";",
	",",
	"(",
	")",
	"{",
	"}",
}


@dataclass
class Token:
	type: str
	lexeme: str
	line: int
	column: int
	value: Optional[int] = None

	def __repr__(self) -> str:
		return f"Token(type={self.type}, lexeme={self.lexeme!r}, line={self.line}, col={self.column}, value={self.value})"



