from .ast import *
from Scanner.TokenType import TokenType as TT


class BottomUpParser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.stack = []
        self.current = 0

    def parse(self):
        while self.current < len(self.tokens):
            token = self.tokens[self.current]
            self.stack.append(token)
            self.current += 1
            self._reduce()

        return self._build_program()

    def _build_program(self):
        leftover_tokens = [x for x in self.stack if not isinstance(x, Node)]
        if leftover_tokens:
            raise SyntaxError(
                f"Syntax Error: tokens دي ما اتعملهاش parse صح: {leftover_tokens}\n"
                f"تأكد إن الكود مكتوب صح."
            )

        return ProgramNode([x for x in self.stack if isinstance(x, Node)])

    def _reduce(self):
        while True:

            if len(self.stack) >= 1:
                top = self.stack[-1]
                if hasattr(top, "type") and top.type == TT.EOF:
                    self.stack.pop()
                    continue

            if len(self.stack) >= 1:
                top = self.stack[-1]
                if hasattr(top, "type") and top.type == TT.NUMBER:
                    token = self.stack.pop()
                    self.stack.append(LiteralNode(float(token.value)))
                    continue

            if len(self.stack) >= 1:
                top = self.stack[-1]
                if hasattr(top, "type") and top.type == TT.STRING:
                    token = self.stack.pop()
                    self.stack.append(LiteralNode(token.value))
                    continue

            if len(self.stack) >= 1:
                top = self.stack[-1]
                if hasattr(top, "type") and top.type == TT.IDENTIFIER:
                    token = self.stack.pop()
                    self.stack.append(IdentifierNode(token.value))
                    continue

            if len(self.stack) >= 3:
                lp, inner, rp = self.stack[-3], self.stack[-2], self.stack[-1]

                if (
                    hasattr(lp, "type") and lp.type == TT.LPAREN and
                    isinstance(inner, Node) and
                    hasattr(rp, "type") and rp.type == TT.RPAREN
                ):
                    self.stack.pop()
                    self.stack.pop()
                    self.stack.pop()
                    self.stack.append(inner)
                    continue

            if len(self.stack) >= 3:
                left, op, right = self.stack[-3], self.stack[-2], self.stack[-1]

                if (
                    isinstance(left, Node) and
                    hasattr(op, "type") and op.type in [TT.MULTIPLY, TT.DIVIDE] and
                    isinstance(right, Node)
                ):
                    self.stack.pop()
                    self.stack.pop()
                    self.stack.pop()
                    self.stack.append(BinaryExprNode(left, op.type, right))
                    continue

            if len(self.stack) >= 3:
                left, op, right = self.stack[-3], self.stack[-2], self.stack[-1]

                if (
                    isinstance(left, Node) and
                    hasattr(op, "type") and op.type in [TT.PLUS, TT.MINUS] and
                    isinstance(right, Node)
                ):
                    next_token = (
                        self.tokens[self.current]
                        if self.current < len(self.tokens)
                        else None
                    )

                    if (
                        next_token is not None and
                        hasattr(next_token, "type") and
                        next_token.type in [TT.MULTIPLY, TT.DIVIDE]
                    ):
                        break

                    self.stack.pop()
                    self.stack.pop()
                    self.stack.pop()
                    self.stack.append(BinaryExprNode(left, op.type, right))
                    continue

            if len(self.stack) >= 5:
                dtype, name, eq, expr, semi = (
                    self.stack[-5], self.stack[-4], self.stack[-3],
                    self.stack[-2], self.stack[-1]
                )

                if (
                    hasattr(dtype, "type") and
                    dtype.type in [TT.COUNT, TT.NOTE, TT.COIN, TT.MEASURE, TT.EMO] and
                    isinstance(name, IdentifierNode) and
                    hasattr(eq, "type") and eq.type == TT.ASSIGN and
                    isinstance(expr, Node) and
                    hasattr(semi, "type") and semi.type == TT.SEMICOLON
                ):
                    self.stack.pop()
                    self.stack.pop()
                    self.stack.pop()
                    self.stack.pop()
                    self.stack.pop()
                    self.stack.append(VarDeclNode(dtype.type, name.name, expr))
                    continue

            if len(self.stack) >= 4:
                name, eq, expr, semi = (
                    self.stack[-4], self.stack[-3],
                    self.stack[-2], self.stack[-1]
                )

                if (
                    isinstance(name, IdentifierNode) and
                    hasattr(eq, "type") and eq.type == TT.ASSIGN and
                    isinstance(expr, Node) and
                    hasattr(semi, "type") and semi.type == TT.SEMICOLON
                ):
                    self.stack.pop()
                    self.stack.pop()
                    self.stack.pop()
                    self.stack.pop()
                    self.stack.append(AssignNode(name.name, expr))
                    continue

            if len(self.stack) >= 4:
                serve, op, expr, semi = (
                    self.stack[-4], self.stack[-3],
                    self.stack[-2], self.stack[-1]
                )

                if (
                    hasattr(serve, "type") and serve.type == TT.SERVE and
                    hasattr(op, "type") and op.type == TT.SHIFT_LEFT and
                    isinstance(expr, Node) and
                    hasattr(semi, "type") and semi.type == TT.SEMICOLON
                ):
                    self.stack.pop()
                    self.stack.pop()
                    self.stack.pop()
                    self.stack.pop()
                    self.stack.append(IOOutputNode(expr))
                    continue

            break