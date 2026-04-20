import re
from Scanner.TokenType import TokenType
from Scanner.Token import Token
class Scanner:

    KEYWORDS = {

        "count": TokenType.COUNT,
        "note": TokenType.NOTE,
        "coin": TokenType.COIN,
        "measure": TokenType.MEASURE,
        "emo": TokenType.EMO,
        "package": TokenType.PACKAGE,
        "hot": TokenType.HOT,
        "cold": TokenType.COLD,
        "waiter": TokenType.WAITER,
        "serve": TokenType.SERVE,
        "check": TokenType.CHECK,
        "another_check": TokenType.ANOTHER_CHECK,
        "instead": TokenType.INSTEAD,
        "menu": TokenType.MENU,
        "item": TokenType.ITEM,
        "any_drink": TokenType.ANY_DRINK,
        "done": TokenType.DONE,
        "stir": TokenType.STIR,
        "refill": TokenType.REFILL,
        "recipe": TokenType.RECIPE,
        "bill": TokenType.BILL,
        "safe_order": TokenType.SAFE_ORDER,
        "spilled": TokenType.SPILLED,
    }

    def __init__(self, source):

        self.source = source
        self.tokens = []

        self.token_regex = re.compile(
    r"""
    (?P<STRING>"[^"]*")
    | (?P<CHARACTER>'[^']')
    | (?P<NUMBER>\d+(\.\d+)?)
    | (?P<IDENTIFIER>[a-zA-Z_][a-zA-Z0-9_]*)

    # Operators (IMPORTANT: longer first)
    | (?P<GTE>>=)
    | (?P<LTE><=)
    | (?P<EQ>==)
    | (?P<NE>!=)
    | (?P<SHIFT_LEFT><<)
    | (?P<SHIFT_RIGHT>>)

    # Single operators
    | (?P<GT>>)
    | (?P<LT><)
    | (?P<PLUS>\+)
    | (?P<MINUS>-)
    | (?P<MULTIPLY>\*)
    | (?P<DIVIDE>/)
    | (?P<ASSIGN>=)

    # Symbols
    | (?P<LPAREN>\()
    | (?P<RPAREN>\))
    | (?P<LBRACE>\{)
    | (?P<RBRACE>\})
    | (?P<LBRACKET>\[)
    | (?P<RBRACKET>\])
    | (?P<SEMICOLON>;)
    | (?P<COMMA>,)
    | (?P<COLON>:)

    | (?P<WHITESPACE>\s+)
    | (?P<MISMATCH>.)
    """,
    re.VERBOSE
)

    def get_line_column(self, position):
        line = self.source.count("\n", 0, position) + 1
        last_newline = self.source.rfind("\n", 0, position)
        column = position - last_newline
        return line, column

    def scan_tokens(self):

        for match in self.token_regex.finditer(self.source):

            kind = match.lastgroup
            value = match.group()
            pos = match.start()

            line, column = self.get_line_column(pos)

            if kind == "WHITESPACE":
                continue

            if kind == "MISMATCH":
                raise SyntaxError(
                    f"Unexpected character '{value}' at line {line} column {column}"
                )

            if kind == "NUMBER":
                token_type = TokenType.NUMBER

            elif kind == "IDENTIFIER":
                token_type = Scanner.KEYWORDS.get(value, TokenType.IDENTIFIER)

            else:
                token_type = getattr(TokenType, kind)

            self.tokens.append(Token(token_type, value, column, line))

        self.tokens.append(Token(TokenType.EOF, "", column, line))

        return self.tokens