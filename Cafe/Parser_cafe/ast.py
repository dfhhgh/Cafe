# ast.py

class Node:
    def accept(self, visitor):
        method_name = f"visit_{type(self).__name__}"
        method = getattr(visitor, method_name, None)

        if method is None:
            raise Exception(f"Unknown node: {type(self).__name__}")

        return method(self)


# =========================
# BASIC
# =========================

class LiteralNode(Node):
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return str(self.value)


class IdentifierNode(Node):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name


# =========================
# EXPRESSIONS
# =========================

class BinaryExprNode(Node):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

    def __repr__(self):
        return f"({self.left} {self.op.name} {self.right})"


class ConditionNode(Node):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right


# =========================
# PROGRAM
# =========================

class ProgramNode(Node):
    def __init__(self, statements):
        self.statements = statements or []

    def __repr__(self):
        return "\n".join(str(s) for s in self.statements)


class BlockNode(Node):
    def __init__(self, statements):
        self.statements = statements or []

    def __repr__(self):
        return "{ " + "; ".join(str(s) for s in self.statements) + " }"


# =========================
# STATEMENTS
# =========================

class VarDeclNode(Node):
    def __init__(self, data_type, name, value=None):
        self.data_type = data_type
        self.name = name
        self.value = value

    def __repr__(self):
        return f"{self.data_type.name} {self.name} = {self.value}"


class AssignNode(Node):
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def __repr__(self):
        return f"{self.name} = {self.value}"


class IOOutputNode(Node):
    def __init__(self, expr):
        self.expr = expr

    def __repr__(self):
        return f"print({self.expr})"


# =========================
# CONTROL FLOW
# =========================

class IfNode(Node):
    def __init__(self, condition, then_block, else_block=None):
        self.condition = condition
        self.then_block = then_block
        self.else_block = else_block


class WhileNode(Node):
    def __init__(self, condition, block):
        self.condition = condition
        self.block = block


class ForNode(Node):
    def __init__(self, init, condition, update, block):
        self.init = init
        self.condition = condition
        self.update = update
        self.block = block


# =========================
# SWITCH
# =========================

class CaseNode(Node):
    def __init__(self, value, body):
        self.value = value
        self.body = body


class SwitchNode(Node):
    def __init__(self, expr, cases, default):
        self.expr = expr
        self.cases = cases
        self.default = default


# =========================
# FUNCTIONS
# =========================

class FunctionNode(Node):
    def __init__(self, return_type, name, params, body):
        self.return_type = return_type
        self.name = name
        self.params = params
        self.body = body


class ReturnNode(Node):
    def __init__(self, value):
        self.value = value