# ast.py

class Node:
    def __init__(self):
        self.dtype = None

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
        super().__init__()
        self.value = value

    def __repr__(self):
        return str(self.value)


class IdentifierNode(Node):
    def __init__(self, name):
        super().__init__()
        self.name = name

    def __repr__(self):
        return self.name


# =========================
# EXPRESSIONS
# =========================

class BinaryExprNode(Node):
    def __init__(self, left, op, right):
        super().__init__()
        self.left = left
        self.op = op
        self.right = right

    def __repr__(self):
        return f"({self.left} {self.op.name} {self.right})"


class ConditionNode(Node):
    def __init__(self, left, op, right):
        super().__init__()
        self.left = left
        self.op = op
        self.right = right

    def __repr__(self):
        return f"({self.left} {self.op.name} {self.right})"


# =========================
# PROGRAM
# =========================

class ProgramNode(Node):
    def __init__(self, statements):
        super().__init__()
        self.statements = statements or []

    def __repr__(self):
        return "\n".join(str(s) for s in self.statements)


class BlockNode(Node):
    def __init__(self, statements):
        super().__init__()
        self.statements = statements or []

    def __repr__(self):
        return "{ " + "; ".join(str(s) for s in self.statements) + " }"


# =========================
# STATEMENTS
# =========================

class VarDeclNode(Node):
    def __init__(self, data_type, name, value=None):
        super().__init__()
        self.data_type = data_type
        self.name = name
        self.value = value

    def __repr__(self):
        if self.value is not None:
            return f"{self.data_type} {self.name} = {self.value}"
        return f"{self.data_type} {self.name}"


class AssignNode(Node):
    def __init__(self, name, value):
        super().__init__()
        self.name = name
        self.value = value

    def __repr__(self):
        return f"{self.name} = {self.value}"


class IOOutputNode(Node):
    def __init__(self, expr):
        super().__init__()
        self.expr = expr

    def __repr__(self):
        return f"print({self.expr})"


# =========================
# CONTROL FLOW
# =========================

class IfNode(Node):
    def __init__(self, condition, then_block, else_block=None):
        super().__init__()
        self.condition = condition
        self.then_block = then_block
        self.else_block = else_block

    def __repr__(self):
        if self.else_block:
            return f"if {self.condition} {self.then_block} else {self.else_block}"
        return f"if {self.condition} {self.then_block}"


class WhileNode(Node):
    def __init__(self, condition, block):
        super().__init__()
        self.condition = condition
        self.block = block

    def __repr__(self):
        return f"while {self.condition} {self.block}"


class ForNode(Node):
    def __init__(self, init, condition, update, block):
        super().__init__()
        self.init = init
        self.condition = condition
        self.update = update
        self.block = block

    def __repr__(self):
        return f"for ({self.init}; {self.condition}; {self.update}) {self.block}"


# =========================
# SWITCH
# =========================

class CaseNode(Node):
    def __init__(self, value, body):
        super().__init__()
        self.value = value
        self.body = body

    def __repr__(self):
        return f"case {self.value}: {self.body}"


class DefaultCaseNode(Node):
    def __init__(self, body):
        super().__init__()
        self.body = body

    def __repr__(self):
        return f"default: {self.body}"


class SwitchNode(Node):
    def __init__(self, expr, cases, default):
        super().__init__()
        self.expr = expr
        self.cases = cases or []
        self.default = default

    def __repr__(self):
        cases_str = " ".join(str(c) for c in self.cases)
        default_str = f" {self.default}" if self.default else ""
        return f"switch({self.expr}) {{ {cases_str}{default_str} }}"


# =========================
# FUNCTIONS
# =========================

class ParamNode(Node):
    def __init__(self, param_type, name):
        super().__init__()
        self.type = param_type
        self.name = name

    def __repr__(self):
        return f"{self.type} {self.name}"


class ParamListNode(Node):
    def __init__(self, params):
        super().__init__()
        self.params = params

    def __repr__(self):
        return ", ".join(str(p) for p in self.params)


class FunctionNode(Node):
    def __init__(self, return_type, name, params, body):
        super().__init__()
        self.return_type = return_type
        self.name = name
        self.params = params
        self.body = body

    def __repr__(self):
        params = ", ".join(str(p) for p in self.params)
        return f"{self.return_type} {self.name}({params}) {self.body}"


class FuncCallNode(Node):
    def __init__(self, name, args):
        super().__init__()
        self.name = name
        self.args = args

    def __repr__(self):
        return f"{self.name}({', '.join(map(str, self.args))})"


class ReturnNode(Node):
    def __init__(self, value):
        super().__init__()
        self.value = value

    def __repr__(self):
        return f"return {self.value}"


# =========================
# ARRAYS
# =========================

class ArrayValuesNode(Node):
    def __init__(self, values):
        super().__init__()
        self.values = values

    def __repr__(self):
        return "{ " + ", ".join(map(str, self.values)) + " }"


class ArrayAccessNode(Node):
    def __init__(self, array_name, index_expr):
        super().__init__()
        self.array_name = array_name
        self.index_expr = index_expr

    def __repr__(self):
        return f"{self.array_name}[{self.index_expr}]"


class ArrayDeclNode(Node):
    def __init__(self, data_type, name, size, values):
        super().__init__()
        self.data_type = data_type
        self.name = name
        self.size = size
        self.values = values

    def __repr__(self):
        return f"{self.data_type} {self.name}[{self.size}] = {self.values}"
