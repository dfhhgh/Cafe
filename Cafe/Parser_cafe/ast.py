class Node:
    def accept(self, visitor):
        method_name = f"visit_{type(self).__name__}"
        method = getattr(visitor, method_name, None)

        if method is None:
            raise Exception(f"الـ interpreter مش عارف يتعامل مع: {type(self).__name__}")

        return method(self)


class LiteralNode(Node):
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f"{self.value}"


class IdentifierNode(Node):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"{self.name}"


class BinaryExprNode(Node):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

    def __repr__(self):
        op_map = {
            "PLUS": "+",
            "MINUS": "-",
            "MULTIPLY": "*",
            "DIVIDE": "/"
        }
        op_str = op_map.get(self.op.name, self.op.name)
        return f"({self.left} {op_str} {self.right})"

class UnaryExprNode(Node):
    def __init__(self, op, operand):
        self.op = op
        self.operand = operand

    def __repr__(self):
        return f"({self.op}{self.operand})"


class FunctionCallNode(Node):
    def __init__(self, name, args):
        self.name = name
        self.args = args or []

    def __repr__(self):
        return f"{self.name}({self.args})"


class ArrayAccessNode(Node):
    def __init__(self, name, index):
        self.name = name
        self.index = index

    def __repr__(self):
        return f"{self.name}[{self.index}]"


class ProgramNode(Node):
    def __init__(self, statements):
        self.statements = statements or []

    def __repr__(self):
        return f"Program({len(self.statements)} stmts)"

    def __iter__(self):
        return iter(self.statements)


class VarDeclNode(Node):
    def __init__(self, data_type, name, initializer=None):
        self.data_type = data_type
        self.name = name
        self.initializer = initializer

    def __repr__(self):
        return f"{self.data_type.name.lower()} {self.name} = {self.initializer}"

class ArrayDeclNode(Node):
    def __init__(self, data_type, name, elements=None):
        self.data_type = data_type
        self.name = name
        self.elements = elements or []

    def __repr__(self):
        return f"Array({self.name})"


class AssignNode(Node):
    def __init__(self, name, value=None, op="="):
        self.name = name
        self.value = value
        self.op = op

    def __repr__(self):
        return f"{self.name} {self.op} {self.value}"


class IOOutputNode(Node):
    def __init__(self, expression):
        self.expression = expression

    def __repr__(self):
        return f"print({self.expression})"


class IOInputNode(Node):
    def __init__(self, identifier):
        self.identifier = identifier

    def __repr__(self):
        return f"input({self.identifier})"


class IfNode(Node):
    def __init__(self, condition, then_body, elseif_clauses=None, else_body=None):
        self.condition = condition
        self.then_body = then_body or []
        self.elseif_clauses = elseif_clauses or []
        self.else_body = else_body

    def __repr__(self):
        return f"If({self.condition})"


class WhileNode(Node):
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body or []

    def __repr__(self):
        return f"While({self.condition})"


class ForNode(Node):
    def __init__(self, init, condition, update, body):
        self.init = init
        self.condition = condition
        self.update = update
        self.body = body or []

    def __repr__(self):
        return f"For({self.init}; {self.condition}; {self.update})"


class SwitchCaseNode(Node):
    def __init__(self, value, body):
        self.value = value
        self.body = body or []

    def __repr__(self):
        return f"Case({self.value})"


class SwitchNode(Node):
    def __init__(self, expression, cases, default_body=None):
        self.expression = expression
        self.cases = cases or []
        self.default_body = default_body

    def __repr__(self):
        return f"Switch({self.expression})"


class ParamNode(Node):
    def __init__(self, data_type, name):
        self.data_type = data_type
        self.name = name

    def __repr__(self):
        return f"{self.data_type} {self.name}"


class FunctionDeclNode(Node):
    def __init__(self, return_type, name, params, body):
        self.return_type = return_type
        self.name = name
        self.params = params or []
        self.body = body or []

    def __repr__(self):
        return f"Function({self.name})"


class ReturnNode(Node):
    def __init__(self, value=None):
        self.value = value

    def __repr__(self):
        return f"Return({self.value})"


class TryCatchNode(Node):
    def __init__(self, try_body, catch_var, catch_body):
        self.try_body = try_body or []
        self.catch_var = catch_var
        self.catch_body = catch_body or []

    def __repr__(self):
        return f"TryCatch({self.catch_var})"


class ImportNode(Node):
    def __init__(self, module_name):
        self.module_name = module_name

    def __repr__(self):
        return f"Import({self.module_name})"


class ExprStmtNode(Node):
    def __init__(self, expression):
        self.expression = expression

    def __repr__(self):
        return f"{self.expression}"