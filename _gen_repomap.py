"""Generate docs/generated/repo-map.md: an AST-based signature map of the backend."""
import ast
import os

ROOT = r"E:\Codes\atlas-ai\backend"
OUT = r"E:\Codes\atlas-ai\docs\generated\repo-map.md"
SKIP_DIRS = {".venv", "__pycache__", ".git"}
SKIP_FILES = {"_gen_repomap.py"}


def sig_from_args(node: ast.arguments) -> str:
    parts = []
    for a in node.posonlyargs + node.args:
        parts.append(a.arg)
    if node.vararg:
        parts.append("*" + node.vararg.arg)
    for a in node.kwonlyargs:
        parts.append(a.arg)
    if node.kwarg:
        parts.append("**" + node.kwarg.arg)
    return ", ".join(parts)


def decorators(node) -> str:
    out = []
    for d in node.decorator_list:
        if isinstance(d, ast.Name):
            out.append("@" + d.id)
        elif isinstance(d, ast.Attribute):
            out.append("@" + d.attr)
        elif isinstance(d, ast.Call):
            if isinstance(d.func, ast.Name):
                out.append("@" + d.func.id + "(...)")
            elif isinstance(d, ast.Attribute):
                out.append("@" + d.func.attr + "(...)")
            else:
                out.append("@<decorator>")
        else:
            out.append("@<decorator>")
    return " ".join(out)


def rel(path):
    return os.path.relpath(path, ROOT).replace("\\", "/")


def process_file(path):
    src = open(path, encoding="utf-8").read()
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        return [f"  ⚠ 解析失败: {e}"], []
    lines = []
    imports = []
    # module docstring
    doc = ast.get_docstring(tree)
    for node in tree.body:
        if isinstance(node, ast.Import):
            for n in node.names:
                imports.append(f"import {n.name}")
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            names = ", ".join(n.name for n in node.names)
            imports.append(f"from {mod} import {names}")
        elif isinstance(node, ast.ClassDef):
            bases = ", ".join(ast.unparse(b) for b in node.bases)
            lines.append(f"class {node.name}({bases}):")
            methods = [n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
            sub = [n for n in node.body if isinstance(n, ast.Assign)]
            for m in methods:
                asyncp = "async " if isinstance(m, ast.AsyncFunctionDef) else ""
                dec = decorators(m)
                lines.append(f"  {dec} {asyncp}def {m.name}({sig_from_args(m.args)})")
            for s in sub:
                for t in s.targets:
                    if isinstance(t, ast.Name):
                        lines.append(f"  {t.id} = ...")
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            asyncp = "async " if isinstance(node, ast.AsyncFunctionDef) else ""
            dec = decorators(node)
            lines.append(f"{dec} {asyncp}def {node.name}({sig_from_args(node.args)})")
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    lines.append(f"{t.id} = ...")
    return lines, imports, doc


def main():
    rows = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in sorted(filenames):
            if not fn.endswith(".py"):
                continue
            full = os.path.join(dirpath, fn)
            if fn in SKIP_FILES:
                continue
            body, imports, doc = process_file(full)
            rows.append((rel(full), doc, imports, body))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("# 源码签名地图（repo-map）\n\n")
        f.write("> 本文件由脚本从 `backend/app/**/*.py` 自动抽取（类/函数签名、导入、导出），\n")
        f.write("> 用于 Agent 快速建立「有哪些文件、有哪些可调用符号」的心智模型。\n")
        f.write("> 重新生成：仓库根保留生成脚本 `_gen_repomap.py`，直接运行 `python _gen_repomap.py` 即可刷新本文件。\n\n")
        f.write("---\n\n")
        for path, doc, imports, body in rows:
            f.write(f"## `{path}`\n\n")
            if doc:
                first = doc.strip().splitlines()[0] if doc.strip() else ""
                if first:
                    f.write(f"> {first}\n\n")
            if imports:
                f.write("**imports**\n\n```\n")
                f.write("\n".join(imports) + "\n```\n\n")
            if body:
                f.write("**symbols**\n\n```\n")
                f.write("\n".join(body) + "\n```\n\n")
            else:
                f.write("_(无顶层类/函数)_\n\n")
            f.write("---\n\n")
    print("WROTE", OUT)


if __name__ == "__main__":
    main()
