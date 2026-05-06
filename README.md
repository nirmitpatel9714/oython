# Oython Programming Language

Oython is an experimental, multi-language prototype programming language designed with Python-like syntax but using curly braces `{}` instead of indentation. It features a unique **Multi-Compiler Execution Engine** that intelligently routes function calls to different runtime environments (Python, Node.js, C, C++, Java) based on where the functions are defined.

## Features

- **Curly Brace Syntax**: Python-like logic but with `{}` blocks instead of significant whitespace, and `func` instead of `def`.
- **Intelligent Function Resolution**: Calls `sqrt()`? Oython finds the compiler that implements it. If it's unambiguous, Oython routes the execution to that compiler automatically.
- **Direct Variable Assignment**: E.g., `x = sqrt(25)` – transparently executes in the appropriate runtime (like JavaScript) and assigns the resulting value back in Python!
- **Explicit Block Execution**: For cases where ambiguity exists (e.g., `printf` in both C and C++), explicitly run blocks using `compiler_run("lang") { ... }`.

## Usage

Create a file named `program.oy`:

```oy
import_compilers({
    python: "python",
    javascript: "node",
    c: "gcc",
    cpp: "g++"
})

func main() {
    // 1. Python execution (default)
    print("Hello from Python")

    // 2. Python standard function resolution
    x = sqrt(25)
    print("Python sqrt(25) =", x)

    // 3. Automatic JavaScript resolution and execution
    console.log("Hello from JS")

    // 4. Explicit C execution block (since printf is in both C and C++)
    compiler_run("c") {
        printf("Hello from C\n");
    }
}

main()
```

### Running Oython

```bash
oython program.oy
```

*Note: Since JavaScript is routed through Node.js, ensure `node` is available in your PATH or configured accurately in `import_compilers`.*
