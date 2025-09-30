from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Union


# Types
@dataclass
class Type:
	name: str  # "int" or "void"


# Declarations
@dataclass
class VarDecl:
	type: Type
	name: str


@dataclass
class Param:
	type: Type
	name: str


@dataclass
class FunctionDecl:
	return_type: Type
	name: str
	params: List[Param]
	body: "Block"


# Statements
@dataclass
class Block:
	statements: List["Stmt"]


@dataclass
class IfStmt:
	cond: "Expr"
	then_block: Block
	else_block: Optional[Block]


@dataclass
class WhileStmt:
	cond: "Expr"
	body: Block


@dataclass
class ReturnStmt:
	value: Optional["Expr"]


@dataclass
class ExprStmt:
	expr: Optional["Expr"]


Stmt = Union[IfStmt, WhileStmt, ReturnStmt, ExprStmt, VarDecl]


# Expressions
@dataclass
class Number:
	value: int


@dataclass
class Var:
	name: str


@dataclass
class Assign:
	name: str
	value: "Expr"


@dataclass
class Binary:
	left: "Expr"
	op: str
	right: "Expr"


@dataclass
class Unary:
	op: str
	value: "Expr"


@dataclass
class Call:
	name: str
	args: List["Expr"]


Expr = Union[Number, Var, Assign, Binary, Unary, Call]



