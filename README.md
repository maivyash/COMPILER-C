🖥️ cc-llvm-mini

A minimal C-subset compiler written in Python that emits LLVM IR and links with clang.

✨ Features

🔹 Supports int and void types

🔹 Functions with parameters & local variables

🔹 Expressions: + - * / % < <= > >= == != && || ! and assignments

🔹 Statements: if/else, while, return, and expression statements

⚡ Lightweight and educational — great for learning how compilers work!

📦 Prerequisites

Python 3.9+

LLVM / clang (to turn .ll into a native executable)

Install clang on Windows (choose one):

# Option A: winget (one-time, admin recommended)
winget install LLVM.LLVM --silent

# Option B: Chocolatey (if you have choco)
choco install llvm -y


Restart PowerShell after install so clang appears on PATH. Verify:

where clang

📥 Install this project (editable)
cd C:\Users\gupta\Desktop\Projects\COMPILER
python -m pip install -e .


If you see a warning that ccmini.exe is not on PATH, that’s okay — use the python -m cc.cli module entry point shown below (it works even if a script wrapper isn’t on PATH).

⚙️ Compile an example to LLVM IR

Using the module entry point (always works):

python -m cc.cli examples/hello.c -o examples/hello.ll


Or, if ccmini is on PATH:

ccmini examples/hello.c -o examples/hello.ll


You should see:

Wrote examples\hello.ll

🚀 Build a native executable with clang (Windows)
clang examples\hello.ll -o examples\hello.exe
.\examples\hello.exe


Check native process exit code:

In PowerShell:

$LASTEXITCODE


In cmd.exe:

echo %ERRORLEVEL%


Note: the example program returns an integer; modify your source to call a print function if you want visible stdout output.

📖 Command reference

Compile a C file to LLVM IR:

python -m cc.cli <input.c> -o <output.ll>

🛠 Troubleshooting
❌ ccmini is not recognized

Use the module entry point (python -m cc.cli ...) or add your Python Scripts folder to PATH.

Add Scripts folder to the current PowerShell session (adjust path for your Python install):

$env:Path += ";C:\Users\gupta\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\LocalCache\local-packages\Python311\Scripts"


To persist the change (reopen PowerShell afterwards):

setx PATH "$($env:Path);C:\Users\gupta\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\LocalCache\local-packages\Python311\Scripts"

❌ clang is not recognized

Install LLVM or add it to PATH:

setx PATH "$($env:Path);C:\Program Files\LLVM\bin"


(Then reopen PowerShell.)

❌ Parser errors

Common causes:

Missing ; at the end of statements

Unmatched braces { }

Unsupported syntax (this project implements only a small subset of C — no pointers/arrays/structs yet)

📂 Project layout
src/cc/
  __init__.py
  tokens.py      # token kinds and Token dataclass
  lexer.py       # turns source into tokens
  ast_nodes.py   # AST node classes
  parser.py      # recursive-descent parser -> AST
  symbols.py     # simple symbol tables
  codegen.py     # emits LLVM IR (.ll)
  cli.py         # CLI entry point

examples/
  hello.c        # sample program

🌱 Example examples/hello.c
int add(int a, int b) {
    int c;
    c = a + b;
    return c;
}

int main() {
    int x;
    x = add(3, 4);
    return x; // program exit code will be 7
}


Compile & run:

python -m cc.cli examples/hello.c -o examples/hello.ll
clang examples/hello.ll -o examples\hello.exe
.\examples\hello.exe
$LASTEXITCODE

🌱 Extend the language (ideas)

This compiler is designed for experimentation. Suggestions for next steps:

Add unary ++ / --

Add for loops and break / continue

Support function prototypes & multiple files

Implement a simple static type checker

Add pointers, arrays, and structs

Emit .data and support string literals + a minimal runtime / stdlib

Add basic optimizations (constant folding, simple dead code elimination)

📜 License

MIT © 2025

(Include a LICENSE file with the MIT text.)

🤝 Contributing

Contributions are welcome! If you plan larger changes, open an issue to discuss design first. Pull requests for bug fixes, minor features, and docs improvements are appreciated.

⭐ Support

If you find this project useful, please star the repo on GitHub — it helps other people discover it!
