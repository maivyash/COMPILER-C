from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from .ast_nodes import Type, Param


@dataclass
class VariableSymbol:
	name: str
	type: Type


@dataclass
class FunctionSymbol:
	name: str
	return_type: Type
	params: tuple[Param, ...]


class SymbolTable:
	def __init__(self, parent: Optional["SymbolTable"] = None) -> None:
		self.parent = parent
		self.vars: Dict[str, VariableSymbol] = {}
		self.funcs: Dict[str, FunctionSymbol] = {}

	def define_var(self, name: str, type_: Type) -> None:
		self.vars[name] = VariableSymbol(name, type_)

	def resolve_var(self, name: str) -> Optional[VariableSymbol]:
		if name in self.vars:
			return self.vars[name]
		if self.parent:
			return self.parent.resolve_var(name)
		return None

	def define_func(self, name: str, return_type: Type, params: tuple[Param, ...]) -> None:
		self.funcs[name] = FunctionSymbol(name, return_type, params)

	def resolve_func(self, name: str) -> Optional[FunctionSymbol]:
		if name in self.funcs:
			return self.funcs[name]
		if self.parent:
			return self.parent.resolve_func(name)
		return None



