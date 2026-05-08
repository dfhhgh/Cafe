from .ast import *
from Scanner.TokenType import TokenType as TT


class Symbol:
    def __init__(self, name, data_type, param_types=None):
        self.name = name
        self.data_type = data_type
        self.param_types = param_types


class SymbolTable:
    def __init__(self):
        self.table = {}
        self.history = []
        self._scope_markers = [(0, set())]

    _MISSING = object()

    def push_scope(self):
        self._scope_markers.append((len(self.history), set()))

    def pop_scope(self):
        if len(self._scope_markers) <= 1:
            raise Exception("Cannot pop the global scope")

        start_index, _ = self._scope_markers.pop()
        while len(self.history) > start_index:
            name, previous = self.history.pop()
            if previous is self._MISSING:
                del self.table[name]
            else:
                self.table[name] = previous

    def declare(self, name, symbol):
        _, current_scope_vars = self._scope_markers[-1]
        if name in current_scope_vars:
            raise Exception(f"Variable '{name}' already declared in this scope")

        previous = self.table.get(name, self._MISSING)
        self.history.append((name, previous))
        self.table[name] = symbol
        current_scope_vars.add(name)

    def lookup(self, name):
        if name not in self.table:
            raise Exception(f"Undeclared variable '{name}'")
        return self.table[name]


class RecursiveDescentParser:
    TYPE_TOKENS = {TT.COUNT, TT.NOTE, TT.COIN, TT.MEASURE, TT.EMO}
    REL_OPS = {TT.GT, TT.LT, TT.EQ, TT.NE, TT.GTE, TT.LTE}
    STATEMENT_STARTS = {
        TT.COUNT,
        TT.NOTE,
        TT.COIN,
        TT.MEASURE,
        TT.EMO,
        TT.CHECK,
        TT.STIR,
        TT.REFILL,
        TT.MENU,
        TT.SERVE,
        TT.BILL,
        TT.IDENTIFIER,
        TT.LBRACE,
    }

    def __init__(self, tokens):
        self.tokens = tokens
        self.current = 0
        self.symbol_table = SymbolTable()
        self.current_function_type = None
        self.function_type_stack = []
        self.errors = []

    # ------------------------------------------------------------------
    # Token navigation
    # ------------------------------------------------------------------
    def parse(self):
        return self.parse_program()

    def parse_program(self):
        statements = []
        while not self.is_at_end():
            try:
                statements.append(self.parse_declaration_or_statement())
            except SyntaxError as error:
                self.errors.append(str(error))
                self.synchronize()
        if self.errors:
            raise SyntaxError("\n".join(self.errors))
        return ProgramNode(statements)

    def advance(self):
        if not self.is_at_end():
            self.current += 1
        return self.previous()

    def peek(self):
        return self.tokens[self.current]

    def previous(self):
        return self.tokens[self.current - 1]

    def check(self, token_type):
        if self.is_at_end():
            return False
        return self.peek().type == token_type

    def check_any(self, token_types):
        if self.is_at_end():
            return False
        return self.peek().type in token_types

    def match(self, *token_types):
        for token_type in token_types:
            if self.check(token_type):
                self.advance()
                return True
        return False

    def consume(self, token_type, message):
        if self.check(token_type):
            return self.advance()
        raise self.error(self.peek(), message)

    def is_at_end(self):
        return self.peek().type == TT.EOF

    def error(self, token, message):
        return SyntaxError(
            f"{message} at line {token.lineNumber}, col {token.columnNumber}"
        )

    def synchronize(self, stop_tokens=None):
        stop_tokens = stop_tokens or set()
        if self.check_any(stop_tokens):
            return

        if not self.is_at_end():
            self.advance()

        while not self.is_at_end():
            if self.previous().type == TT.SEMICOLON:
                return
            if self.check_any(stop_tokens):
                return
            if self.check_any(self.STATEMENT_STARTS):
                return
            self.advance()

    # ------------------------------------------------------------------
    # Types and semantic helpers
    # ------------------------------------------------------------------
    def map_type(self, token_type):
        return {
            TT.COUNT: "number",
            TT.MEASURE: "number",
            TT.COIN: "bool",
            TT.NOTE: "string",
            TT.EMO: "char",
        }.get(token_type, "unknown")

    def check_types(self, left, right):
        return left == right

    def consume_type(self):
        if not self.check_any(self.TYPE_TOKENS):
            raise self.error(self.peek(), "Expected type")
        return self.map_type(self.advance().type)

    def consume_identifier_name(self, message="Expected identifier"):
        return self.consume(TT.IDENTIFIER, message).value

    def declare_variable(self, name, data_type, param_types=None):
        self.symbol_table.declare(name, Symbol(name, data_type, param_types))

    def resolve_identifier(self, name):
        try:
            return self.symbol_table.lookup(name)
        except Exception:
            raise Exception(f"Undefined identifier: {name}")

    # ------------------------------------------------------------------
    # Statements and declarations
    # ------------------------------------------------------------------
    def parse_declaration_or_statement(self):
        if self.check_any(self.TYPE_TOKENS):
            if self.peek_next_type() == TT.RECIPE:
                return self.parse_function()
            if self.peek_next_type() == TT.PACKAGE:
                return self.parse_array()
            return self.parse_variable_declaration()

        return self.parse_statement()

    def parse_statement(self):
        if self.match(TT.LBRACE):
            return self.parse_block(open_scope=True)
        if self.match(TT.CHECK):
            return self.parse_if()
        if self.match(TT.STIR):
            return self.parse_while()
        if self.match(TT.REFILL):
            return self.parse_for()
        if self.match(TT.MENU):
            return self.parse_switch()
        if self.match(TT.SERVE):
            return self.parse_output()
        if self.match(TT.BILL):
            return self.parse_return()
        if self.check(TT.IDENTIFIER):
            return self.parse_identifier_statement()

        raise self.error(self.peek(), "Expected statement")

    def parse_block(self, open_scope=True):
        if open_scope:
            self.symbol_table.push_scope()

        try:
            statements = self.parse_statement_list_until({TT.RBRACE})
            self.consume(TT.RBRACE, "Expected '}' after block")
            return BlockNode(statements)
        finally:
            if open_scope:
                self.symbol_table.pop_scope()

    def parse_statement_list_until(self, stop_tokens):
        statements = []
        while not self.check_any(stop_tokens) and not self.is_at_end():
            try:
                statements.append(self.parse_declaration_or_statement())
            except SyntaxError as error:
                self.errors.append(str(error))
                self.synchronize(stop_tokens)
        return statements

    def parse_variable_declaration(self):
        var_type, name, value = self.parse_variable_declaration_parts()
        self.consume(TT.SEMICOLON, "Expected ';' after variable declaration")
        self.declare_variable(name, var_type)
        return VarDeclNode(var_type, name, value)

    def parse_variable_declaration_parts(self):
        var_type = self.consume_type()
        name = self.consume_identifier_name()

        value = None
        if self.match(TT.ASSIGN):
            value = self.parse_expression()
            if not self.check_types(var_type, value.dtype):
                raise Exception(f"Type mismatch in declaration of '{name}'")

        return var_type, name, value

    def parse_array(self):
        data_type = self.consume_type()
        self.consume(TT.PACKAGE, "Expected 'package' in array declaration")
        name = self.consume_identifier_name()
        self.consume(TT.LBRACKET, "Expected '[' after array name")
        size_token = self.consume(TT.NUMBER, "Expected array size")
        self.consume(TT.RBRACKET, "Expected ']' after array size")
        self.consume(TT.ASSIGN, "Expected '=' in array declaration")
        values = self.parse_array_values(expected_type=data_type)
        self.consume(TT.SEMICOLON, "Expected ';' after array declaration")

        self.declare_variable(name, f"array<{data_type}>")
        return ArrayDeclNode(data_type, name, int(float(size_token.value)), values)

    def parse_array_values(self, expected_type=None):
        self.consume(TT.LBRACE, "Expected '{' before array values")
        values = []

        if not self.check(TT.RBRACE):
            while True:
                value = self.parse_expression()
                if expected_type is not None and value.dtype != expected_type:
                    raise Exception(
                        f"Array type mismatch: expected '{expected_type}', got '{value.dtype}'"
                    )
                if values and values[0].dtype != value.dtype:
                    raise Exception(
                        f"Array type mismatch: expected '{values[0].dtype}', got '{value.dtype}'"
                    )
                values.append(value)
                if not self.match(TT.COMMA):
                    break

        self.consume(TT.RBRACE, "Expected '}' after array values")
        return ArrayValuesNode(values)

    def parse_identifier_statement(self):
        name = self.consume_identifier_name()

        if self.match(TT.LBRACKET):
            target = self.finish_array_access(name)
            self.consume(TT.ASSIGN, "Expected '=' after array access")
            value = self.parse_expression()
            self.consume(TT.SEMICOLON, "Expected ';' after assignment")
            return self.finish_assignment(target, value)

        if self.match(TT.ASSIGN):
            value = self.parse_expression()
            self.consume(TT.SEMICOLON, "Expected ';' after assignment")
            return self.finish_assignment(name, value)

        if self.match(TT.LPAREN):
            call = self.finish_function_call(name)
            self.consume(TT.SEMICOLON, "Expected ';' after function call")
            return call

        raise self.error(self.peek(), "Expected assignment or function call")

    def finish_assignment(self, name, value):
        target_type = name.dtype if isinstance(name, ArrayAccessNode) else self.symbol_table.lookup(name).data_type
        if not self.check_types(target_type, value.dtype):
            raise Exception(
                f"Type mismatch in assignment to '{name}': expected '{target_type}', got '{value.dtype}'"
            )
        return AssignNode(name, value)

    def parse_output(self):
        self.consume(TT.SHIFT_LEFT, "Expected '<<' after 'serve'")
        expr = self.parse_expression()
        self.consume(TT.SEMICOLON, "Expected ';' after output statement")
        return IOOutputNode(expr)

    def parse_return(self):
        expr = self.parse_expression()
        self.consume(TT.SEMICOLON, "Expected ';' after return statement")

        if self.current_function_type is not None:
            if not self.check_types(expr.dtype, self.current_function_type):
                raise Exception(
                    f"Return type mismatch: expected '{self.current_function_type}', got '{expr.dtype}'"
                )

        return ReturnNode(expr)

    # ------------------------------------------------------------------
    # Control flow
    # ------------------------------------------------------------------
    def parse_if(self):
        self.consume(TT.LPAREN, "Expected '(' after 'check'")
        condition = self.parse_expression()
        self.consume(TT.RPAREN, "Expected ')' after condition")
        then_block = self.consume_block("Expected block after if condition")

        return IfNode(condition, then_block, self.parse_else_branch())

    def parse_else_branch(self):
        if self.match(TT.ANOTHER_CHECK):
            self.consume(TT.LPAREN, "Expected '(' after 'another_check'")
            condition = self.parse_expression()
            self.consume(TT.RPAREN, "Expected ')' after condition")
            block = self.consume_block("Expected block after another_check condition")
            return IfNode(condition, block, self.parse_else_branch())

        if self.match(TT.INSTEAD):
            return self.consume_block("Expected block after 'instead'")

        return None

    def parse_while(self):
        self.consume(TT.LPAREN, "Expected '(' after 'stir'")
        condition = self.parse_expression()
        self.consume(TT.RPAREN, "Expected ')' after condition")
        block = self.consume_block("Expected block after while condition")
        return WhileNode(condition, block)

    def parse_for(self):
        self.consume(TT.LPAREN, "Expected '(' after 'refill'")
        self.symbol_table.push_scope()
        try:
            init = self.parse_for_initializer()
            self.consume(TT.SEMICOLON, "Expected ';' after for initializer")

            condition = None
            if not self.check(TT.SEMICOLON):
                condition = self.parse_expression()
            self.consume(TT.SEMICOLON, "Expected ';' after for condition")

            update = None
            if not self.check(TT.RPAREN):
                update = self.parse_for_update()
            self.consume(TT.RPAREN, "Expected ')' after for clauses")

            block = self.consume_block("Expected block after for statement")
            return ForNode(init, condition, update, block)
        finally:
            self.symbol_table.pop_scope()

    def parse_for_initializer(self):
        if self.check(TT.SEMICOLON):
            return None

        if self.check_any(self.TYPE_TOKENS):
            var_type, name, value = self.parse_variable_declaration_parts()
            self.declare_variable(name, var_type)
            return VarDeclNode(var_type, name, value)

        return self.parse_assignment_without_semicolon()

    def parse_for_update(self):
        if self.check(TT.IDENTIFIER) and self.peek_next_type() == TT.ASSIGN:
            return self.parse_assignment_without_semicolon()
        return self.parse_expression()

    def parse_assignment_without_semicolon(self):
        name = self.consume_identifier_name()
        if self.match(TT.LBRACKET):
            name = self.finish_array_access(name)
        self.consume(TT.ASSIGN, "Expected assignment")
        return self.finish_assignment(name, self.parse_expression())

    def finish_array_access(self, array_name):
        index_expr = self.parse_expression()
        self.consume(TT.RBRACKET, "Expected ']' after array index")

        symbol = self.symbol_table.lookup(array_name)
        if not symbol.data_type.startswith("array<") or not symbol.data_type.endswith(">"):
            raise Exception(f"'{array_name}' is not an array")
        if index_expr.dtype != "number":
            raise Exception(
                f"Array index for '{array_name}' must be number, got '{index_expr.dtype}'"
            )

        node = ArrayAccessNode(array_name, index_expr)
        node.dtype = symbol.data_type[6:-1]
        return node

    def parse_switch(self):
        self.consume(TT.LPAREN, "Expected '(' after 'menu'")
        expr = self.parse_expression()
        self.consume(TT.RPAREN, "Expected ')' after switch expression")
        self.consume(TT.LBRACE, "Expected '{' before switch cases")

        cases = []
        default = None
        while not self.check(TT.RBRACE) and not self.is_at_end():
            try:
                if self.match(TT.ITEM):
                    value = self.consume(TT.NUMBER, "Expected case value").value
                    self.consume(TT.COLON, "Expected ':' after case value")
                    body = self.parse_case_body()
                    self.consume(TT.DONE, "Expected 'done' after case body")
                    self.consume(TT.SEMICOLON, "Expected ';' after 'done'")
                    cases.append(CaseNode(value, body))
                elif self.match(TT.ANY_DRINK):
                    self.consume(TT.COLON, "Expected ':' after default case")
                    default = DefaultCaseNode(self.parse_case_body())
                else:
                    raise self.error(self.peek(), "Expected switch case")
            except SyntaxError as error:
                self.errors.append(str(error))
                self.synchronize({TT.ITEM, TT.ANY_DRINK, TT.RBRACE})

        self.consume(TT.RBRACE, "Expected '}' after switch")
        switch_expr = expr.name if isinstance(expr, IdentifierNode) else expr
        return SwitchNode(switch_expr, cases, default)

    def parse_case_body(self):
        return BlockNode(self.parse_statement_list_until({
            TT.DONE,
            TT.ITEM,
            TT.ANY_DRINK,
            TT.RBRACE,
        }))

    def consume_block(self, message):
        self.consume(TT.LBRACE, message)
        return self.parse_block(open_scope=True)

    # ------------------------------------------------------------------
    # Functions
    # ------------------------------------------------------------------
    def parse_function(self):
        return_type = self.consume_type()
        self.consume(TT.RECIPE, "Expected 'recipe' after function return type")
        name = self.consume_identifier_name("Expected function name")
        self.consume(TT.LPAREN, "Expected '(' after function name")
        params = self.parse_parameters()
        self.consume(TT.RPAREN, "Expected ')' after parameters")

        self.declare_variable(
            name,
            f"func<{return_type}>",
            param_types=[param.type for param in params],
        )

        self.consume(TT.LBRACE, "Expected function body")
        self.symbol_table.push_scope()
        previous_function_type = self.current_function_type
        self.function_type_stack.append(previous_function_type)
        self.current_function_type = return_type

        try:
            for param in params:
                self.declare_variable(param.name, param.type)
            body = self.parse_block(open_scope=False)
        finally:
            self.symbol_table.pop_scope()
            self.current_function_type = self.function_type_stack.pop()

        return FunctionNode(return_type, name, params, body)

    def parse_parameters(self):
        params = []
        if self.check(TT.RPAREN):
            return params

        while True:
            param_type = self.consume_type()
            name = self.consume_identifier_name("Expected parameter name")
            params.append(ParamNode(param_type, name))
            if not self.match(TT.COMMA):
                break

        return params

    def parse_function_call(self):
        name = self.consume_identifier_name("Expected function name")
        self.consume(TT.LPAREN, "Expected '(' after function name")
        return self.finish_function_call(name)

    def finish_function_call(self, name):
        args = []
        if not self.check(TT.RPAREN):
            while True:
                args.append(self.parse_expression())
                if not self.match(TT.COMMA):
                    break
        self.consume(TT.RPAREN, "Expected ')' after arguments")

        try:
            symbol = self.symbol_table.lookup(name)
        except Exception:
            raise Exception(f"Call to undefined function '{name}'")

        if not symbol.data_type.startswith("func<"):
            raise Exception(f"'{name}' is not a function; found '{symbol.data_type}'")

        expected_types = getattr(symbol, "param_types", None)
        if expected_types is not None:
            if len(args) != len(expected_types):
                raise Exception(
                    f"Function '{name}' expects {len(expected_types)} argument(s) "
                    f"({', '.join(expected_types) or 'none'}), got {len(args)}"
                )

            for index, (arg, expected_type) in enumerate(zip(args, expected_types), start=1):
                if not self.check_types(arg.dtype, expected_type):
                    raise Exception(
                        f"Function '{name}' argument {index} type mismatch: "
                        f"expected '{expected_type}', got '{arg.dtype}'"
                    )

        node = FuncCallNode(name, args)
        node.dtype = symbol.data_type[5:-1]
        return node

    # ------------------------------------------------------------------
    # Expressions
    # ------------------------------------------------------------------
    def parse_expression(self):
        return self.parse_comparison()

    def parse_comparison(self):
        expr = self.parse_addition()

        while self.check_any(self.REL_OPS):
            op = self.advance()
            right = self.parse_addition()
            if not self.check_types(expr.dtype, right.dtype):
                raise Exception("Type mismatch in condition")
            expr = ConditionNode(expr, op.type, right)
            expr.dtype = "bool"

        return expr

    def parse_addition(self):
        expr = self.parse_multiplication()

        while self.match(TT.PLUS, TT.MINUS):
            op = self.previous()
            right = self.parse_multiplication()
            if not self.check_types(expr.dtype, right.dtype):
                raise Exception("Type mismatch in expression")
            expr = BinaryExprNode(expr, op.type, right)
            expr.dtype = right.dtype

        return expr

    def parse_multiplication(self):
        expr = self.parse_unary()

        while self.match(TT.MULTIPLY, TT.DIVIDE):
            op = self.previous()
            right = self.parse_unary()
            if not self.check_types(expr.dtype, right.dtype):
                raise Exception("Type mismatch in expression")
            expr = BinaryExprNode(expr, op.type, right)
            expr.dtype = right.dtype

        return expr

    def parse_term(self):
        return self.parse_addition()

    def parse_factor(self):
        return self.parse_multiplication()

    def parse_unary(self):
        if self.match(TT.MINUS):
            op = self.previous()
            right = self.parse_unary()
            zero = LiteralNode(0.0)
            zero.dtype = "number"
            if right.dtype != "number":
                raise Exception("Type mismatch in expression")
            node = BinaryExprNode(zero, op.type, right)
            node.dtype = "number"
            return node

        return self.parse_primary()

    def parse_primary(self):
        if self.match(TT.NUMBER):
            node = LiteralNode(float(self.previous().value))
            node.dtype = "number"
            return node

        if self.match(TT.STRING):
            node = LiteralNode(self.previous().value)
            node.dtype = "string"
            return node

        if self.match(TT.CHARACTER):
            node = LiteralNode(self.previous().value)
            node.dtype = "char"
            return node

        if self.match(TT.HOT):
            node = LiteralNode(True)
            node.dtype = "bool"
            return node

        if self.match(TT.COLD):
            node = LiteralNode(False)
            node.dtype = "bool"
            return node

        if self.check(TT.IDENTIFIER):
            name = self.consume_identifier_name()
            if self.match(TT.LPAREN):
                return self.finish_function_call(name)
            if self.match(TT.LBRACKET):
                return self.finish_array_access(name)

            symbol = self.resolve_identifier(name)
            node = IdentifierNode(name)
            node.dtype = symbol.data_type
            return node

        if self.match(TT.LPAREN):
            expr = self.parse_expression()
            self.consume(TT.RPAREN, "Expected ')' after expression")
            return expr

        raise self.error(self.peek(), "Expected expression")

    def peek_next_type(self):
        if self.current + 1 >= len(self.tokens):
            return None
        return self.tokens[self.current + 1].type


class BottomUpParser(RecursiveDescentParser):
    """Compatibility name for existing imports.

    The implementation is now a top-down handwritten recursive descent parser.
    """

    pass


TopDownParser = RecursiveDescentParser
