import sys
import re
import ast
import json
import subprocess
import os
import shutil

COMPILER_FUNCTIONS = {
    "python": ["print", "math.sqrt", "sqrt", "len", "str", "int", "math.pow"],
    "javascript": ["console.log", "Math.sqrt", "parseInt", "parseFloat"],
    "c": ["printf", "scanf", "malloc", "free", "sqrt"],
    "cpp": ["printf", "cout", "cin", "sqrt", "std::cout"],
    "java": ["System.out.println", "System.out.print", "Math.sqrt"]
}

DEFAULT_COMPILER_ORDER = ["python", "javascript", "java", "cpp", "c"]

class AmbiguityError(Exception): pass
class NotFoundError(Exception): pass

_compilers = {}

def get_compiler_path(lang):
    if lang in _compilers:
        return _compilers[lang]
    return lang

def resolve_function(func_name, default_compiler, imported_compilers):
    # Check if clearly in default compiler
    if default_compiler in COMPILER_FUNCTIONS and func_name in COMPILER_FUNCTIONS[default_compiler]:
        return default_compiler
        
    found_in = []
    for comp in imported_compilers:
        if comp == default_compiler: continue
        if comp in COMPILER_FUNCTIONS and func_name in COMPILER_FUNCTIONS[comp]:
            found_in.append(comp)
            
    if len(found_in) == 1:
        return found_in[0]
    elif len(found_in) > 1:
        raise AmbiguityError(f"Function '{func_name}' is ambiguous. Found in: {', '.join(found_in)}. Please use compiler_run.")
    else:
        # Default fallback
        return default_compiler

def __oython_exec__(compiler, func_name, *args):
    path = get_compiler_path(compiler)
    if compiler == "javascript":
        args_js = ", ".join(json.dumps(a) for a in args)
        script = f"""
        const fs = require('fs');
        const res = {func_name}({args_js});
        if (res !== undefined) {{
            fs.writeFileSync('.oython_out.json', JSON.stringify({{result: res}}));
        }}
        """
        if os.path.exists(".oython_out.json"):
            os.remove(".oython_out.json")
        with open(".oython_temp.js", "w") as f:
            f.write(script)
        subprocess.run([path, ".oython_temp.js"], check=True)
        if os.path.exists(".oython_out.json"):
            with open(".oython_out.json") as f:
                res = json.load(f)
                return res.get("result")
        return None
    elif compiler == "python":
        pass
    else:
        print(f"[Oython Prototype] Executing {func_name} in {compiler} (no return value supported in prototype)")
        return None

def __oython_run_block__(compiler, code):
    path = get_compiler_path(compiler)
    if compiler == "c":
        c_code = f"""
        #include <stdio.h>
        #include <stdlib.h>
        #include <math.h>
        int main() {{
            {code}
            return 0;
        }}
        """
        with open(".oython_temp.c", "w") as f:
            f.write(c_code)
        subprocess.run([path, ".oython_temp.c", "-o", ".oython_temp_c.exe"], check=True)
        subprocess.run([".\\.oython_temp_c.exe"], check=True)
    elif compiler == "cpp":
        cpp_code = f"""
        #include <iostream>
        #include <cmath>
        using namespace std;
        int main() {{
            {code}
            return 0;
        }}
        """
        with open(".oython_temp.cpp", "w") as f:
            f.write(cpp_code)
        subprocess.run([path, ".oython_temp.cpp", "-o", ".oython_temp_cpp.exe"], check=True)
        subprocess.run([".\\.oython_temp_cpp.exe"], check=True)
    else:
        print(f"[Oython Prototype] Unsupported compiler_run block for {compiler}")

class OythonTransformer(ast.NodeTransformer):
    def __init__(self, local_funcs, default_compiler, imported_compilers):
        self.local_funcs = local_funcs
        self.default_compiler = default_compiler
        self.imported_compilers = imported_compilers

    def visit_Call(self, node):
        self.generic_visit(node)
        
        func_name = None
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                func_name = f"{node.func.value.id}.{node.func.attr}"
        
        if not func_name:
            return node
            
        if func_name in self.local_funcs or func_name == "__oython_run_block__" or func_name == "__oython_exec__":
            return node
            
        compiler = resolve_function(func_name, self.default_compiler, self.imported_compilers)
        
        if compiler == "python":
            if func_name == "sqrt":
                node.func = ast.parse("math.sqrt", mode='eval').body
            return node
        else:
            new_node = ast.Call(
                func=ast.Name(id="__oython_exec__", ctx=ast.Load()),
                args=[ast.Constant(value=compiler), ast.Constant(value=func_name)] + node.args,
                keywords=node.keywords
            )
            return ast.copy_location(new_node, node)

def preprocess(code):
    import_compilers = {}
    m = re.search(r"import_compilers\s*\(\s*\{(.*?)\}\s*\)", code, re.DOTALL)
    if m:
        inner = m.group(1)
        for line in inner.split('\n'):
            line = line.strip()
            if not line: continue
            if ':' in line:
                k, v = line.split(':', 1)
                k = k.strip(' "\'')
                v = v.strip(' "\',')
                import_compilers[k] = v
        code = code[:m.start()] + code[m.end():]

    out_code = ""
    i = 0
    while i < len(code):
        m = re.match(r'compiler_run\s*\(\s*"([^"]+)"\s*\)\s*\{', code[i:])
        if m:
            lang = m.group(1)
            start_brace = i + m.end() - 1
            brace_count = 1
            j = start_brace + 1
            while j < len(code) and brace_count > 0:
                if code[j] == '{': brace_count += 1
                elif code[j] == '}': brace_count -= 1
                j += 1
            body = code[start_brace+1:j-1]
            out_code += f'__oython_run_block__("{lang}", r"""{body}""")'
            i = j
        else:
            out_code += code[i]
            i += 1
    code = out_code

    code = re.sub(r"\bfunc\b", "def", code)

    lines = code.split('\n')
    new_lines = []
    indent = 0
    for line in lines:
        s = line.strip()
        if s.endswith('{'):
            new_lines.append("    " * indent + s[:-1].strip() + ":")
            indent += 1
        elif s == '}':
            indent -= 1
        else:
            if s:
                new_lines.append("    " * indent + s)
            else:
                new_lines.append("")

    return import_compilers, "\n".join(new_lines)

def run(filepath):
    with open(filepath, 'r') as f:
        code = f.read()
        
    compilers, py_code = preprocess(code)
    
    global _compilers
    
    if not compilers:
        for c in DEFAULT_COMPILER_ORDER:
            if shutil.which(c) or c == "python":
                _compilers[c] = c
                break
    else:
        _compilers.update(compilers)
        
    imported_compilers = list(_compilers.keys())
    default_compiler = imported_compilers[0] if imported_compilers else "python"
    
    tree = ast.parse(py_code)
    local_funcs = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
    
    transformer = OythonTransformer(local_funcs, default_compiler, imported_compilers)
    new_tree = transformer.visit(tree)
    ast.fix_missing_locations(new_tree)
    
    import_math = ast.parse("import math").body[0]
    new_tree.body.insert(0, import_math)
    
    compiled_code = compile(new_tree, filename="<ast>", mode="exec")
    
    exec_globals = {
        "__builtins__": __builtins__,
        "__oython_exec__": __oython_exec__,
        "__oython_run_block__": __oython_run_block__,
        "math": __import__("math")
    }
    
    exec(compiled_code, exec_globals)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python oython.py <file.oy>")
        sys.exit(1)
    run(sys.argv[1])
