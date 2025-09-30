from __future__ import annotations

from typing import List, Optional

from .tokens import Token
from .ast_nodes import (
	Type,
	VarDecl,
	Param,
	FunctionDecl,
	Block,
	IfStmt,
	WhileStmt,
	ReturnStmt,
	ExprStmt,
	Number,
	Var,
	Assign,
	Binary,
	Unary,
	Call,
)


class Parser:
	def __init__(self, tokens: List[Token]) -> None:
		self.tokens = tokens
		self.pos = 0

	def _peek(self, n: int = 0) -> Token:
		if self.pos + n >= len(self.tokens):
			return Token("EOF", "", -1, -1)
		return self.tokens[self.pos + n]

	def _advance(self) -> Token:
		t = self._peek()
		self.pos = min(self.pos + 1, len(self.tokens))
		return t

	def _match(self, *kinds: str) -> Optional[Token]:
		t = self._peek()
		if t.type in kinds or t.lexeme in kinds:
			self._advance()
			return t
		return None

	def _expect(self, kind: str, message: str) -> Token:
		t = self._peek()
		if t.type == kind or t.lexeme == kind:
			self._advance()
			return t
		raise SyntaxError(message + f" at {t.line}:{t.column}")

	def parse(self) -> List[FunctionDecl]:
		functions: List[FunctionDecl] = []
		while self._peek().type != "EOF":
			functions.append(self._function())
		return functions

	def _type(self) -> Type:
		t = self._expect("KEYWORD", "Expected type keyword")
		if t.lexeme not in ("int", "void"):
			raise SyntaxError(f"Unsupported type {t.lexeme}")
		return Type(t.lexeme)

	def _ident(self) -> str:
		t = self._peek()
		if t.type in ("IDENT",):
			self._advance()
			return t.lexeme
		raise SyntaxError(f"Expected identifier at {t.line}:{t.column}")

	def _function(self) -> FunctionDecl:
		ret = self._type()
		name = self._ident()
		self._expect("(", "Expected '('")
		params: List[Param] = []
		if not self._match(")"):
			while True:
				ptype = self._type()
				pname = self._ident()
				params.append(Param(ptype, pname))
				if self._match(","):
					continue
				self._expect(")", "Expected ')'")
				break
		self._expect("{", "Expected '{'")
		body = self._block()
		return FunctionDecl(ret, name, params, body)

	def _block(self) -> Block:
		stmts: List = []
		while not self._match("}"):
			stmts.append(self._statement())
		return Block(stmts)

	def _statement(self):
		t = self._peek()
		if t.type == "KEYWORD" and t.lexeme == "if":
			self._advance()
			self._expect("(", "Expected '('")
			cond = self._expression()
			self._expect(")", "Expected ')'")
			self._expect("{", "Expected '{'")
			thenb = self._block()
			elseb = None
			# Only consume 'else' if the next token is exactly the 'else' keyword
			nxt = self._peek()
			if nxt.type == "KEYWORD" and nxt.lexeme == "else":
				self._advance()
				self._expect("{", "Expected '{'")
				elseb = self._block()
			return IfStmt(cond, thenb, elseb)
		if t.type == "KEYWORD" and t.lexeme == "while":
			self._advance()
			self._expect("(", "Expected '('")
			cond = self._expression()
			self._expect(")", "Expected ')'")
			self._expect("{", "Expected '{'")
			body = self._block()
			return WhileStmt(cond, body)
		if t.type == "KEYWORD" and t.lexeme == "return":
			self._advance()
			if not self._match(";"):
				value = self._expression()
				self._expect(";", "Expected ';'")
				return ReturnStmt(value)
			return ReturnStmt(None)
		# local var decl: int x; or int x = expr;
		if t.type == "KEYWORD" and t.lexeme in ("int",):
			typ = self._type()
			name = self._ident()
			if self._match("="):
				value = self._expression()
				self._expect(";", "Expected ';'")
				return ExprStmt(Assign(name, value))
			self._expect(";", "Expected ';'")
			return VarDecl(typ, name)
		# expression statement
		ex = None
		if not self._match(";"):
			ex = self._expression()
			self._expect(";", "Expected ';'")
		return ExprStmt(ex)

	def _expression(self):
		return self._assignment()

	def _assignment(self):
		expr = self._logical_or()
		if self._match("="):
			if isinstance(expr, Var):
				value = self._assignment()
				return Assign(expr.name, value)
			raise SyntaxError("Invalid assignment target")
		return expr

	def _logical_or(self):
		expr = self._logical_and()
		while self._match("||"):
			right = self._logical_and()
			expr = Binary(expr, "||", right)
		return expr

	def _logical_and(self):
		expr = self._equality()
		while self._match("&&"):
			right = self._equality()
			expr = Binary(expr, "&&", right)
		return expr

	def _equality(self):
		expr = self._comparison()
		while True:
			if self._match("=="):
				expr = Binary(expr, "==", self._comparison())
				continue
			if self._match("!="):
				expr = Binary(expr, "!=", self._comparison())
				continue
			break
		return expr

	def _comparison(self):
		expr = self._term()
		while True:
			if self._match("<"):
				expr = Binary(expr, "<", self._term())
				continue
			if self._match("<="):
				expr = Binary(expr, "<=", self._term())
				continue
			if self._match(">"):
				expr = Binary(expr, ">", self._term())
				continue
			if self._match(">="):
				expr = Binary(expr, ">=", self._term())
				continue
			break
		return expr

	def _term(self):
		expr = self._factor()
		while True:
			if self._match("+"):
				expr = Binary(expr, "+", self._factor())
				continue
			if self._match("-"):
				expr = Binary(expr, "-", self._factor())
				continue
			break
		return expr

	def _factor(self):
		expr = self._unary()
		while True:
			if self._match("*"):
				expr = Binary(expr, "*", self._unary())
				continue
			if self._match("/"):
				expr = Binary(expr, "/", self._unary())
				continue
			if self._match("%"):
				expr = Binary(expr, "%", self._unary())
				continue
			break
		return expr

	def _unary(self):
		if self._match("-"):
			return Unary("-", self._unary())
		if self._match("!"):
			return Unary("!", self._unary())
		return self._call()

	def _call(self):
		expr = self._primary()
		# only simple calls: name(args)
		if isinstance(expr, Var) and self._match("("):
			args: List = []
			if not self._match(")"):
				while True:
					args.append(self._expression())
					if self._match(","):
						continue
					self._expect(")", "Expected ')'")
					break
			return Call(expr.name, args)
		return expr

	def _primary(self):
		t = self._peek()
		if t.type == "NUMBER":
			self._advance()
			return Number(t.value or 0)
		if t.type == "IDENT":
			self._advance()
			return Var(t.lexeme)
		if t.lexeme == "(":
			self._advance()
			ex = self._expression()
			self._expect(")", "Expected ')'")
			return ex
		raise SyntaxError(f"Unexpected token {t}")



