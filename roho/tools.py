"""Virtual tools only. No host filesystem, network, SQL execution, or eval."""
import ast
import json
import operator
from pathlib import PurePosixPath

TOOL_DOCS = {
    "read_file": '{"path":"input.txt"} -> file text',
    "write_file": '{"path":"result.txt","content":"text"} -> writes virtual file',
    "calculate": '{"expression":"(2+3)*4"} -> integer result; only +,-,* allowed',
    "sum_table": '{"path":"table.json","column":"amount","where_column":"group","equals":"A"} -> integer sum',
    "finish": '{"answer":"your final answer"} -> ends task; required files must already exist',
}


def path_check(path):
    if not isinstance(path, str) or not path or len(path) > 200 or "\\" in path:
        raise ValueError("Invalid path")
    p = PurePosixPath(path)
    if p.is_absolute() or ".." in p.parts or path != str(p):
        raise ValueError("Path outside virtual workspace")
    return path


def calculate(expression):
    if not isinstance(expression, str) or len(expression) > 128:
        raise ValueError("Invalid expression")
    tree = ast.parse(expression, mode="eval")
    if len(list(ast.walk(tree))) > 64:
        raise ValueError("Expression too complex")
    operations = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul}

    def visit(node):
        if isinstance(node, ast.Constant) and type(node.value) is int:
            result = node.value
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            result = -visit(node.operand)
        elif isinstance(node, ast.BinOp) and type(node.op) in operations:
            result = operations[type(node.op)](visit(node.left), visit(node.right))
        else:
            raise ValueError("Unsupported expression")
        if abs(result) > 10**12:
            raise ValueError("Arithmetic bound exceeded")
        return result
    return str(visit(tree.body))


def execute(tool, args, files):
    if not isinstance(args, dict):
        raise ValueError("args must be object")
    required = {"read_file": {"path"}, "write_file": {"path", "content"}, "calculate": {"expression"}, "sum_table": {"path", "column", "where_column", "equals"}}
    if tool not in required or set(args) != required[tool]:
        raise ValueError("Unknown tool or wrong argument keys")
    if tool == "calculate":
        return calculate(args["expression"])
    path = path_check(args["path"])
    if tool == "write_file":
        if not isinstance(args["content"], str) or len(args["content"]) > 4096 or len(files) >= 20:
            raise ValueError("File resource limit")
        files[path] = args["content"]
        return "written"
    if path not in files:
        raise ValueError("File not found")
    if tool == "read_file":
        return files[path]
    rows = json.loads(files[path])
    return str(sum(row[args["column"]] for row in rows if row[args["where_column"]] == args["equals"]))

