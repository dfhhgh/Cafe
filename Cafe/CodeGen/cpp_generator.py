from pathlib import Path
import subprocess

from Parser_cafe.ast import (
    ArrayAccessNode,
    ArrayDeclNode,
    ArrayValuesNode,
    AssignNode,
    BinaryExprNode,
    BlockNode,
    CaseNode,
    ConditionNode,
    DefaultCaseNode,
    ForNode,
    FuncCallNode,
    FunctionNode,
    IdentifierNode,
    IfNode,
    IOOutputNode,
    LiteralNode,
    ParamNode,
    ProgramNode,
    ReturnNode,
    SwitchNode,
    VarDeclNode,
    WhileNode,
)
from Scanner.TokenType import TokenType as TT


class CodeGenerationError(Exception):
    """Raised when AST to C++ generation cannot be completed."""


class CppGenerator:
    """Visitor-based C++ source generator for Cafe ASTs."""

    OPERATOR_MAP = {
        TT.PLUS: "+",
        TT.MINUS: "-",
        TT.MULTIPLY: "*",
        TT.DIVIDE: "/",
        TT.GT: ">",
        TT.LT: "<",
        TT.EQ: "==",
        TT.NE: "!=",
        TT.GTE: ">=",
        TT.LTE: "<=",
    }

    TYPE_MAP = {
        "count": "int",
        "measure": "double",
        "note": "std::string",
        "coin": "bool",
        "emo": "char",
        "number": "double",
        "string": "std::string",
        "bool": "bool",
        "char": "char",
    }

    def __init__(self, ast, output_path="output.cpp", indent_text="    "):
        self.ast = ast
        self.output_path = Path(output_path)
        self.indent_text = indent_text
        self.indent_level = 0
        self.lines = []

    def generate(self, write_file=True):
        self.lines = []
        self.indent_level = 0
        self.visit(self.ast)
        source = "\n".join(self.lines) + "\n"

        if write_file:
            self.output_path.write_text(source, encoding="utf-8")

        return source

    def visit(self, node):
        if node is None:
            return ""

        method_name = f"visit_{type(node).__name__}"
        method = getattr(self, method_name, None)
        if method is None:
            raise CodeGenerationError(f"No C++ generator visitor for {type(node).__name__}")
        return method(node)

    def emit(self, text=""):
        self.lines.append(text)

    def emit_line(self, text=""):
        if text:
            self.lines.append(f"{self.indent_text * self.indent_level}{text}")
        else:
            self.lines.append("")

    def cpp_type(self, cafe_type):
        if cafe_type is None:
            return "auto"

        if cafe_type.startswith("array<") and cafe_type.endswith(">"):
            return self.cpp_type(cafe_type[6:-1])

        if cafe_type.startswith("func<") and cafe_type.endswith(">"):
            return self.cpp_type(cafe_type[5:-1])

        return self.TYPE_MAP.get(cafe_type, cafe_type)

    # ------------------------------------------------------------------
    # Program structure
    # ------------------------------------------------------------------
    def visit_ProgramNode(self, node):
        functions = [stmt for stmt in node.statements if isinstance(stmt, FunctionNode)]
        top_level = [stmt for stmt in node.statements if not isinstance(stmt, FunctionNode)]

        self.emit_line("#include <iostream>")
        self.emit_line("#include <string>")
        self.emit_line("")
        self.emit_line("using namespace std;")
        self.emit_line("")

        for function in functions:
            self.emit_line(f"{self.function_signature(function)};")

        if functions:
            self.emit_line("")

        for function in functions:
            self.visit(function)
            self.emit_line("")

        self.emit_line("int main() {")
        self.indent_level += 1
        for statement in top_level:
            self.emit_statement(statement)
        self.emit_line("return 0;")
        self.indent_level -= 1
        self.emit_line("}")

    def function_signature(self, node):
        params = ", ".join(self.visit(param) for param in node.params)
        return f"{self.cpp_type(node.return_type)} {node.name}({params})"

    # ------------------------------------------------------------------
    # Statements
    # ------------------------------------------------------------------
    def visit_BlockNode(self, node):
        self.emit_line("{")
        self.indent_level += 1
        for statement in node.statements:
            self.emit_statement(statement)
        self.indent_level -= 1
        self.emit_line("}")

    def visit_VarDeclNode(self, node):
        if node.value is None:
            self.emit_line(f"{self.cpp_type(node.data_type)} {node.name};")
            return
        self.emit_line(
            f"{self.cpp_type(node.data_type)} {node.name} = {self.visit(node.value)};"
        )

    def visit_AssignNode(self, node):
        self.emit_line(f"{self.assignment_source(node)};")

    def visit_IOOutputNode(self, node):
        self.emit_line(f"cout << {self.visit(node.expr)} << endl;")

    def visit_IfNode(self, node):
        self.emit_line(f"if ({self.visit(node.condition)}) {{")
        self.indent_level += 1
        self.emit_block_contents(node.then_block)
        self.indent_level -= 1

        if isinstance(node.else_block, IfNode):
            self.emit_line(f"}} else if ({self.visit(node.else_block.condition)}) {{")
            self.indent_level += 1
            self.emit_block_contents(node.else_block.then_block)
            self.indent_level -= 1
            self.emit_else_tail(node.else_block.else_block)
        elif node.else_block is not None:
            self.emit_line("} else {")
            self.indent_level += 1
            self.emit_block_contents(node.else_block)
            self.indent_level -= 1
            self.emit_line("}")
        else:
            self.emit_line("}")

    def emit_else_tail(self, else_block):
        if isinstance(else_block, IfNode):
            self.emit_line(f"}} else if ({self.visit(else_block.condition)}) {{")
            self.indent_level += 1
            self.emit_block_contents(else_block.then_block)
            self.indent_level -= 1
            self.emit_else_tail(else_block.else_block)
        elif else_block is not None:
            self.emit_line("} else {")
            self.indent_level += 1
            self.emit_block_contents(else_block)
            self.indent_level -= 1
            self.emit_line("}")
        else:
            self.emit_line("}")

    def visit_WhileNode(self, node):
        self.emit_line(f"while ({self.visit(node.condition)}) {{")
        self.indent_level += 1
        self.emit_block_contents(node.block)
        self.indent_level -= 1
        self.emit_line("}")

    def visit_ForNode(self, node):
        init = self.for_clause(node.init)
        condition = self.visit(node.condition) if node.condition is not None else ""
        update = self.for_clause(node.update)

        self.emit_line(f"for ({init}; {condition}; {update}) {{")
        self.indent_level += 1
        self.emit_block_contents(node.block)
        self.indent_level -= 1
        self.emit_line("}")

    def visit_FunctionNode(self, node):
        self.emit_line(f"{self.function_signature(node)} {{")
        self.indent_level += 1
        self.emit_block_contents(node.body)
        self.indent_level -= 1
        self.emit_line("}")

    def visit_ReturnNode(self, node):
        self.emit_line(f"return {self.visit(node.value)};")

    def visit_ArrayDeclNode(self, node):
        self.emit_line(f"{self.array_declaration_source(node)};")

    def visit_SwitchNode(self, node):
        self.emit_line(f"switch ({self.switch_expression(node.expr)}) {{")
        self.indent_level += 1

        for case in node.cases:
            self.visit(case)

        if node.default is not None:
            self.visit(node.default)

        self.indent_level -= 1
        self.emit_line("}")

    def visit_CaseNode(self, node):
        self.emit_line(f"case {self.case_value(node.value)}:")
        self.indent_level += 1
        self.emit_block_contents(node.body)
        self.emit_line("break;")
        self.indent_level -= 1

    def visit_DefaultCaseNode(self, node):
        self.emit_line("default:")
        self.indent_level += 1
        self.emit_block_contents(node.body)
        self.indent_level -= 1

    # ------------------------------------------------------------------
    # Expressions
    # ------------------------------------------------------------------
    def visit_LiteralNode(self, node):
        if isinstance(node.value, bool):
            return "true" if node.value else "false"
        if isinstance(node.value, str):
            if node.dtype == "char":
                return self.quote_char(self.unquote_literal(node.value))
            return self.quote_string(self.unquote_literal(node.value))
        if isinstance(node.value, float) and node.value.is_integer():
            return str(int(node.value))
        return str(node.value)

    def visit_IdentifierNode(self, node):
        return node.name

    def visit_BinaryExprNode(self, node):
        return self.infix_expression(node.left, node.op, node.right)

    def visit_ConditionNode(self, node):
        return self.infix_expression(node.left, node.op, node.right)

    def visit_FuncCallNode(self, node):
        args = ", ".join(self.visit(arg) for arg in node.args)
        return f"{node.name}({args})"

    def visit_ArrayValuesNode(self, node):
        return self.array_initializer_source(node)

    def visit_ArrayAccessNode(self, node):
        return self.array_access_source(node)

    def visit_ParamNode(self, node):
        return f"{self.cpp_type(node.type)} {node.name}"

    # ------------------------------------------------------------------
    # Formatting helpers
    # ------------------------------------------------------------------
    def emit_block_contents(self, block):
        if not isinstance(block, BlockNode):
            self.visit(block)
            return

        for statement in block.statements:
            self.emit_statement(statement)

    def infix_expression(self, left, op, right):
        unary = self.unary_minus_expression(left, op, right)
        if unary is not None:
            return unary

        operator = self.OPERATOR_MAP.get(op)
        if operator is None:
            raise CodeGenerationError(f"Unsupported C++ operator: {op}")
        return f"({self.visit(left)} {operator} {self.visit(right)})"

    def unary_minus_expression(self, left, op, right):
        if op != TT.MINUS:
            return None
        if not isinstance(left, LiteralNode):
            return None
        if left.value not in (0, 0.0):
            return None
        return f"(-{self.visit(right)})"

    def emit_statement(self, node):
        if isinstance(node, FuncCallNode):
            self.emit_line(f"{self.visit(node)};")
            return
        self.visit(node)

    def assignment_source(self, node):
        return f"{self.visit_assignment_target(node.name)} = {self.visit(node.value)}"

    def visit_assignment_target(self, target):
        if isinstance(target, str):
            return target
        return self.visit(target)

    def for_clause(self, node):
        if node is None:
            return ""
        if isinstance(node, VarDeclNode):
            if node.value is None:
                return f"{self.cpp_type(node.data_type)} {node.name}"
            return f"{self.cpp_type(node.data_type)} {node.name} = {self.visit(node.value)}"
        if isinstance(node, AssignNode):
            return self.assignment_source(node)
        return self.visit(node)

    def switch_expression(self, expr):
        if isinstance(expr, str):
            return f"static_cast<int>({expr})"
        source = self.visit(expr)
        if getattr(expr, "dtype", None) == "number":
            return f"static_cast<int>({source})"
        return source

    def case_value(self, value):
        try:
            return str(int(float(value)))
        except (TypeError, ValueError):
            return str(value)

    def is_quoted_literal(self, value):
        return (
            len(value) >= 2
            and ((value[0] == '"' and value[-1] == '"') or (value[0] == "'" and value[-1] == "'"))
        )

    def unquote_literal(self, value):
        if self.is_quoted_literal(value):
            return value[1:-1]
        return value

    def quote_string(self, value):
        escaped = self.escape_string(value)
        return f'"{escaped}"'

    def quote_char(self, value):
        if len(value) != 1:
            raise CodeGenerationError(f"Character literal must contain exactly one character: {value!r}")
        escaped = self.escape_char(value)
        return f"'{escaped}'"

    def escape_string(self, value):
        return (
            value
            .replace("\\", "\\\\")
            .replace("\n", "\\n")
            .replace("\t", "\\t")
            .replace("\r", "\\r")
            .replace('"', '\\"')
        )

    def escape_char(self, value):
        return {
            "\\": "\\\\",
            "'": "\\'",
            "\n": "\\n",
            "\t": "\\t",
            "\r": "\\r",
        }.get(value, value)

    # ------------------------------------------------------------------
    # Array helpers
    # ------------------------------------------------------------------
    def array_declaration_source(self, node):
        return self.c_style_array_declaration_source(node)

    def c_style_array_declaration_source(self, node):
        values = self.array_initializer_source(node.values)
        return f"{self.cpp_type(node.data_type)} {node.name}[{node.size}] = {values}"

    def array_initializer_source(self, node):
        return "{ " + ", ".join(self.visit(value) for value in node.values) + " }"

    def array_access_source(self, node):
        return f"{node.array_name}[{self.visit(node.index_expr)}]"


def generate_cpp(ast, output_path="output.cpp"):
    return CppGenerator(ast, output_path=output_path).generate(write_file=True)


def compile_cpp(source_path="output.cpp", executable_path="output"):
    command = [
        "g++",
        str(Path(source_path)),
        "-std=c++17",
        "-Wall",
        "-Wextra",
        "-o",
        str(Path(executable_path)),
    ]
    return subprocess.run(command, capture_output=True, text=True, check=False)


def run_executable(executable_path):
    return subprocess.run([str(Path(executable_path).resolve())], capture_output=True, text=True, check=False)
