from .ast import *
from Scanner.TokenType import TokenType as TT


class BottomUpParser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.stack = []
        self.current = 0

        # 🔥 operators collection (cleaner)
        self.REL_OPS = {
            TT.GT, TT.LT, TT.EQ, TT.NE, TT.GTE, TT.LTE
        }

    # =========================
    # 🚀 MAIN PARSE
    # =========================
    def parse(self):
        while self.current < len(self.tokens):
            token = self.tokens[self.current]
            self.stack.append(token)
            self.current += 1
            self._reduce()

        return self._build_program()

    # =========================
    # 🧱 PROGRAM BUILD
    # =========================
    def _build_program(self):
        leftover = [x for x in self.stack if not isinstance(x, Node)]
        if leftover:
            raise SyntaxError(f"Unparsed tokens: {leftover}")
        return ProgramNode([x for x in self.stack if isinstance(x, Node)])

    # =========================
    # 🔁 REDUCE LOOP
    # =========================
    def _reduce(self):
        while True:
            if self._remove_eof(): continue
            if self._literal(): continue
            if self._identifier(): continue
            if self._parenthesis(): continue

            if self._mul_div(): continue
            if self._add_sub(): continue
            if self._condition(): continue

            if self._block(): continue
            if self._if_stmt(): continue
            if self._while_stmt(): continue

            if self._var_decl(): continue
            if self._var_decl_no_init(): continue
            if self._assignment(): continue
            if self._print(): continue

            break

    # =========================
    # BASIC
    # =========================

    def _remove_eof(self):
        if self._match_token(-1, TT.EOF):
            self.stack.pop()
            return True
        return False

    def _literal(self):
        if self._match_token(-1, TT.NUMBER):
            token = self.stack.pop()
            self.stack.append(LiteralNode(float(token.value)))
            return True

        if self._match_token(-1, TT.STRING):
            token = self.stack.pop()
            self.stack.append(LiteralNode(token.value))
            return True
        return False

    def _identifier(self):
        if self._match_token(-1, TT.IDENTIFIER):
            token = self.stack.pop()
            self.stack.append(IdentifierNode(token.value))
            return True
        return False

    # =========================
    # EXPRESSIONS
    # =========================

    def _parenthesis(self):
        if len(self.stack) >= 3:
            lp, inner, rp = self.stack[-3:]
            if self._is_token(lp, TT.LPAREN) and isinstance(inner, Node) and self._is_token(rp, TT.RPAREN):
                self._pop(3)
                self.stack.append(inner)
                return True
        return False

    def _mul_div(self):
        return self._binary_expr([TT.MULTIPLY, TT.DIVIDE])

    def _add_sub(self):
        if len(self.stack) < 3:
            return False

        left, op, right = self.stack[-3:]

        if isinstance(left, Node) and self._is_token(op, [TT.PLUS, TT.MINUS]) and isinstance(right, Node):
            next_token = self._peek()
            if next_token and next_token.type in [TT.MULTIPLY, TT.DIVIDE]:
                return False

            self._pop(3)
            self.stack.append(BinaryExprNode(left, op.type, right))
            return True

        return False

    def _binary_expr(self, ops):
        if len(self.stack) < 3:
            return False

        left, op, right = self.stack[-3:]

        if isinstance(left, Node) and self._is_token(op, ops) and isinstance(right, Node):
            self._pop(3)
            self.stack.append(BinaryExprNode(left, op.type, right))
            return True

        return False

    # =========================
    # CONDITION (🔥 FIXED)
    # =========================

    def _condition(self):
        if len(self.stack) < 3:
            return False

        left, op, right = self.stack[-3:]

        if (
            isinstance(left, Node) and
            hasattr(op, "type") and op.type in self.REL_OPS and
            isinstance(right, Node)
        ):
            self._pop(3)
            self.stack.append(ConditionNode(left, op, right))
            return True

        return False

    # =========================
    # BLOCK
    # =========================

    def _block(self):
        if len(self.stack) >= 3:
            l, stmt, r = self.stack[-3:]
            if self._is_token(l, TT.LBRACE) and isinstance(stmt, Node) and self._is_token(r, TT.RBRACE):
                self._pop(3)
                self.stack.append(BlockNode([stmt]))
                return True
        return False

    # =========================
    # IF
    # =========================

    def _if_stmt(self):
        if len(self.stack) >= 5:
            check, lp, cond, rp, block = self.stack[-5:]
            if (
                self._is_token(check, TT.CHECK) and
                self._is_token(lp, TT.LPAREN) and
                isinstance(cond, ConditionNode) and
                self._is_token(rp, TT.RPAREN) and
                isinstance(block, BlockNode)
            ):
                self._pop(5)
                self.stack.append(IfNode(cond, block))
                return True
        return False

    # =========================
    # WHILE
    # =========================

    def _while_stmt(self):
        if len(self.stack) >= 5:
            stir, lp, cond, rp, block = self.stack[-5:]
            if (
                self._is_token(stir, TT.STIR) and
                self._is_token(lp, TT.LPAREN) and
                isinstance(cond, ConditionNode) and
                self._is_token(rp, TT.RPAREN) and
                isinstance(block, BlockNode)
            ):
                self._pop(5)
                self.stack.append(WhileNode(cond, block))
                return True
        return False

    # =========================
    # STATEMENTS
    # =========================

    def _var_decl(self):
        if len(self.stack) < 5:
            return False

        dtype, name, eq, expr, semi = self.stack[-5:]

        if (
            self._is_token(dtype, [TT.COUNT, TT.NOTE, TT.COIN, TT.MEASURE, TT.EMO]) and
            isinstance(name, IdentifierNode) and
            self._is_token(eq, TT.ASSIGN) and
            isinstance(expr, Node) and
            self._is_token(semi, TT.SEMICOLON)
        ):
            self._pop(5)
            self.stack.append(VarDeclNode(dtype.type, name.name, expr))
            return True

        return False

    def _var_decl_no_init(self):
        if len(self.stack) < 3:
            return False

        dtype, name, semi = self.stack[-3:]

        if (
            self._is_token(dtype, [TT.COUNT, TT.NOTE, TT.COIN, TT.MEASURE, TT.EMO]) and
            isinstance(name, IdentifierNode) and
            self._is_token(semi, TT.SEMICOLON)
        ):
            self._pop(3)
            self.stack.append(VarDeclNode(dtype.type, name.name, None))
            return True

        return False

    def _assignment(self):
        if len(self.stack) < 4:
            return False

        name, eq, expr, semi = self.stack[-4:]

        if (
            isinstance(name, IdentifierNode) and
            self._is_token(eq, TT.ASSIGN) and
            isinstance(expr, Node) and
            self._is_token(semi, TT.SEMICOLON)
        ):
            self._pop(4)
            self.stack.append(AssignNode(name.name, expr))
            return True

        return False

    def _print(self):
        if len(self.stack) < 4:
            return False

        serve, op, expr, semi = self.stack[-4:]

        if (
            self._is_token(serve, TT.SERVE) and
            self._is_token(op, TT.SHIFT_LEFT) and
            isinstance(expr, Node) and
            self._is_token(semi, TT.SEMICOLON)
        ):
            self._pop(4)
            self.stack.append(IOOutputNode(expr))
            return True

        return False

    # =========================
    # HELPERS
    # =========================

    def _pop(self, n):
        for _ in range(n):
            self.stack.pop()

    def _peek(self):
        return self.tokens[self.current] if self.current < len(self.tokens) else None

    def _match_token(self, index, token_type):
        if len(self.stack) >= abs(index):
            item = self.stack[index]
            return hasattr(item, "type") and item.type == token_type
        return False

    def _is_token(self, obj, types):
        if not hasattr(obj, "type"):
            return False
        return obj.type in types if isinstance(types, list) else obj.type == types