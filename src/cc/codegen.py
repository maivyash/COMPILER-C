from __future__ import annotations

from typing import Dict, List, Optional

from .ast_nodes import *  # noqa: F401,F403
from .symbols import SymbolTable


class IRBuilder:
	def __init__(self) -> None:
		self.lines: List[str] = []
		self.temp_counter = 0
		self.label_counter = 0

	def emit(self, line: str) -> None:
		self.lines.append(line)

	def new_temp(self) -> str:
		self.temp_counter += 1
		return f"%t{self.temp_counter}"

	def new_label(self, base: str) -> str:
		self.label_counter += 1
		return f"{base}{self.label_counter}"

	def build(self) -> str:
		return "\n".join(self.lines) + ("\n" if self.lines else "")


class Codegen:
	def __init__(self) -> None:
		self.builder = IRBuilder()
		self.globals = SymbolTable()

	def generate(self, functions: List[FunctionDecl]) -> str:
		self.builder.emit("declare i32 @printf(i8*, ...)")
		self.builder.emit('@.fmt = private constant [4 x i8] c"%d\0A\00"')
		for fn in functions:
			self._emit_function(fn)
		return self.builder.build()

	def _llvm_type(self, t: Type) -> str:
		if t.name == "int":
			return "i32"
		if t.name == "void":
			return "void"
		raise ValueError("Unsupported type")

	def _emit_function(self, fn: FunctionDecl) -> None:
		ret_ty = self._llvm_type(fn.return_type)
		params_sig = ", ".join(f"{self._llvm_type(p.type)} %{p.name}" for p in fn.params)
		self.builder.emit(f"define {ret_ty} @{fn.name}({params_sig}) {{")
		self.builder.emit("entry:")
		local = SymbolTable(self.globals)
		for p in fn.params:
			allptr = self.builder.new_temp()
			self.builder.emit(f"  {allptr} = alloca {self._llvm_type(p.type)}")
			self.builder.emit(f"  store {self._llvm_type(p.type)} %{p.name}, {self._llvm_type(p.type)}* {allptr}")
			local.define_var(p.name, p.type)
			setattr(local, f"addr_{p.name}", allptr)
		self._emit_block(fn.body, local)
		if fn.return_type.name == "void":
			self.builder.emit("  ret void")
		self.builder.emit("}")

	def _emit_block(self, block: Block, syms: SymbolTable) -> None:
		for st in block.statements:
			self._emit_stmt(st, syms)

	def _emit_stmt(self, st: Stmt, syms: SymbolTable) -> None:
		if isinstance(st, VarDecl):
			addr = self.builder.new_temp()
			self.builder.emit(f"  {addr} = alloca {self._llvm_type(st.type)}")
			syms.define_var(st.name, st.type)
			setattr(syms, f"addr_{st.name}", addr)
			return
		if isinstance(st, ExprStmt):
			if st.expr is not None:
				self._emit_expr(st.expr, syms)
			return
		if isinstance(st, ReturnStmt):
			if st.value is None:
				self.builder.emit("  ret void")
				return
			val, vty = self._emit_expr(st.value, syms)
			self.builder.emit(f"  ret {vty} {val}")
			return
		if isinstance(st, IfStmt):
			cond_val, _ = self._emit_expr(st.cond, syms)
			cmp = self.builder.new_temp()
			self.builder.emit(f"  {cmp} = icmp ne i32 {cond_val}, 0")
			then_lbl = self.builder.new_label("then")
			else_lbl = self.builder.new_label("else") if st.else_block else None
			end_lbl = self.builder.new_label("endif")
			if else_lbl:
				self.builder.emit(f"  br i1 {cmp}, label %{then_lbl}, label %{else_lbl}")
				self.builder.emit(f"{then_lbl}:")
				self._emit_block(st.then_block, syms)
				self.builder.emit(f"  br label %{end_lbl}")
				self.builder.emit(f"{else_lbl}:")
				self._emit_block(st.else_block, syms)  # type: ignore[arg-type]
				self.builder.emit(f"  br label %{end_lbl}")
				self.builder.emit(f"{end_lbl}:")
				return
			self.builder.emit(f"  br i1 {cmp}, label %{then_lbl}, label %{end_lbl}")
			self.builder.emit(f"{then_lbl}:")
			self._emit_block(st.then_block, syms)
			self.builder.emit(f"  br label %{end_lbl}")
			self.builder.emit(f"{end_lbl}:")
			return
		if isinstance(st, WhileStmt):
			cond_lbl = self.builder.new_label("while.cond")
			body_lbl = self.builder.new_label("while.body")
			end_lbl = self.builder.new_label("while.end")
			self.builder.emit(f"  br label %{cond_lbl}")
			self.builder.emit(f"{cond_lbl}:")
			cond_val, _ = self._emit_expr(st.cond, syms)
			cmp = self.builder.new_temp()
			self.builder.emit(f"  {cmp} = icmp ne i32 {cond_val}, 0")
			self.builder.emit(f"  br i1 {cmp}, label %{body_lbl}, label %{end_lbl}")
			self.builder.emit(f"{body_lbl}:")
			self._emit_block(st.body, syms)
			self.builder.emit(f"  br label %{cond_lbl}")
			self.builder.emit(f"{end_lbl}:")
			return
		raise NotImplementedError(str(st))

	def _emit_expr(self, e: Expr, syms: SymbolTable) -> tuple[str, str]:
		if isinstance(e, Number):
			return str(e.value), "i32"
		if isinstance(e, Var):
			addr = getattr(syms, f"addr_{e.name}")
			res = self.builder.new_temp()
			self.builder.emit(f"  {res} = load i32, i32* {addr}")
			return res, "i32"
		if isinstance(e, Assign):
			val, _ = self._emit_expr(e.value, syms)
			addr = getattr(syms, f"addr_{e.name}")
			self.builder.emit(f"  store i32 {val}, i32* {addr}")
			return val, "i32"
		if isinstance(e, Unary):
			v, _ = self._emit_expr(e.value, syms)
			if e.op == "-":
				res = self.builder.new_temp()
				self.builder.emit(f"  {res} = sub i32 0, {v}")
				return res, "i32"
			if e.op == "!":
				cmp = self.builder.new_temp()
				self.builder.emit(f"  {cmp} = icmp eq i32 {v}, 0")
				zext = self.builder.new_temp()
				self.builder.emit(f"  {zext} = zext i1 {cmp} to i32")
				return zext, "i32"
			raise NotImplementedError(e.op)
		if isinstance(e, Binary):
			l, _ = self._emit_expr(e.left, syms)
			r, _ = self._emit_expr(e.right, syms)
			res = self.builder.new_temp()
			if e.op == "+":
				self.builder.emit(f"  {res} = add i32 {l}, {r}")
				return res, "i32"
			if e.op == "-":
				self.builder.emit(f"  {res} = sub i32 {l}, {r}")
				return res, "i32"
			if e.op == "*":
				self.builder.emit(f"  {res} = mul i32 {l}, {r}")
				return res, "i32"
			if e.op == "/":
				self.builder.emit(f"  {res} = sdiv i32 {l}, {r}")
				return res, "i32"
			if e.op == "%":
				self.builder.emit(f"  {res} = srem i32 {l}, {r}")
				return res, "i32"
			if e.op in ("<", "<=", ">", ">=", "==", "!="):
				cmp = self.builder.new_temp()
				pred = {
					"<": "slt",
					"<=": "sle",
					">": "sgt",
					">=": "sge",
					"==": "eq",
					"!=": "ne",
				}[e.op]
				self.builder.emit(f"  {cmp} = icmp {pred} i32 {l}, {r}")
				zext = self.builder.new_temp()
				self.builder.emit(f"  {zext} = zext i1 {cmp} to i32")
				return zext, "i32"
			if e.op == "&&":
				# simple: compute both, and
				andv = self.builder.new_temp()
				self.builder.emit(f"  {andv} = and i32 {l}, {r}")
				cmp = self.builder.new_temp()
				self.builder.emit(f"  {cmp} = icmp ne i32 {andv}, 0")
				zext = self.builder.new_temp()
				self.builder.emit(f"  {zext} = zext i1 {cmp} to i32")
				return zext, "i32"
			if e.op == "||":
				orv = self.builder.new_temp()
				self.builder.emit(f"  {orv} = or i32 {l}, {r}")
				cmp = self.builder.new_temp()
				self.builder.emit(f"  {cmp} = icmp ne i32 {orv}, 0")
				zext = self.builder.new_temp()
				self.builder.emit(f"  {zext} = zext i1 {cmp} to i32")
				return zext, "i32"
			raise NotImplementedError(e.op)
		if isinstance(e, Call):
			args_vals = []
			for a in e.args:
				v, vty = self._emit_expr(a, syms)
				args_vals.append(f"{vty} {v}")
			res = self.builder.new_temp()
			self.builder.emit(f"  {res} = call i32 @{e.name}({', '.join(args_vals)})")
			return res, "i32"
		raise NotImplementedError(str(e))



