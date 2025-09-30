from __future__ import annotations

import argparse
from pathlib import Path

from .lexer import Lexer
from .parser import Parser
from .codegen import Codegen


def compile_to_ll(source_path: Path, out_path: Path) -> None:
	src = source_path.read_text(encoding="utf-8")
	lex = Lexer(src)
	tokens = lex.tokenize()
	parser = Parser(tokens)
	funcs = parser.parse()
	ll = Codegen().generate(funcs)
	out_path.write_text(ll, encoding="utf-8")


def main() -> None:
	ap = argparse.ArgumentParser(description="C-subset to LLVM IR compiler")
	ap.add_argument("input", type=Path, help="Input .c file")
	ap.add_argument("-o", "--output", type=Path, help="Output .ll file")
	args = ap.parse_args()

	inp: Path = args.input
	outp: Path = args.output or inp.with_suffix(".ll")
	compile_to_ll(inp, outp)
	print(f"Wrote {outp}")


if __name__ == "__main__":
	main()



