from __future__ import annotations

import re
from typing import Iterator, List

from .tokens import Token, KEYWORDS


WHITESPACE = re.compile(r"[ \t]+")
IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
NUMBER = re.compile(r"\d+")


class Lexer:
	def __init__(self, source: str) -> None:
		self.source = source
		self.index = 0
		self.line = 1
		self.column = 1

	def _peek(self, n: int = 0) -> str:
		if self.index + n >= len(self.source):
			return "\0"
		return self.source[self.index + n]

	def _advance(self, steps: int = 1) -> str:
		ch = ""
		for _ in range(steps):
			if self.index >= len(self.source):
				return "\0"
			ch = self.source[self.index]
			self.index += 1
			if ch == "\n":
				self.line += 1
				self.column = 1
			else:
				self.column += 1
		return ch

	def _match(self, text: str) -> bool:
		if self.source.startswith(text, self.index):
			for _ in text:
				self._advance()
			return True
		return False

	def _skip_whitespace_and_comments(self) -> None:
		while True:
			m = WHITESPACE.match(self.source, self.index)
			if m:
				span = m.span()
				for _ in range(span[1] - span[0]):
					self._advance()
				continue
			# Windows / Unix newlines
			if self._peek() == "\r" and self._peek(1) == "\n":
				self._advance(2)
				continue
			if self._peek() == "\n":
				self._advance(1)
				continue
			if self._match("//"):
				while self._peek() not in ("\n", "\0"):
					self._advance()
				continue
			if self._match("/*"):
				while not self._match("*/"):
					if self._peek() == "\0":
						return
					self._advance()
				continue
			break

	def tokenize(self) -> List[Token]:
		tokens: List[Token] = []
		while True:
			self._skip_whitespace_and_comments()
			start_line, start_col = self.line, self.column
			ch = self._peek()
			if ch == "\0":
				break

			# Multi-char operators
			for op in ("==", "!=", "<=", ">=", "&&", "||"):
				if self._match(op):
					tokens.append(Token("SYMBOL", op, start_line, start_col))
					break
			else:
				# Single-char symbols
				if ch in "+-*/%(){};,<>!=":
					self._advance()
					tokens.append(Token("SYMBOL", ch, start_line, start_col))
					continue

			m = NUMBER.match(self.source, self.index)
			if m:
				lex = m.group(0)
				for _ in lex:
					self._advance()
				val = int(lex)
				tokens.append(Token("NUMBER", lex, start_line, start_col, val))
				continue

			m = IDENTIFIER.match(self.source, self.index)
			if m:
				lex = m.group(0)
				for _ in lex:
					self._advance()
				type_ = "KEYWORD" if lex in KEYWORDS else "IDENT"
				tokens.append(Token(type_, lex, start_line, start_col))
				continue

			raise SyntaxError(f"Unexpected character {ch!r} at {start_line}:{start_col}")

		return tokens



