from Cafe.Parser_cafe.parser import BottomUpParser
from Cafe.Scanner.Scanner import Scanner

code = """
count x = 5;
"""

scanner = Scanner(code)
tokens = scanner.scan_tokens()

print("TOKENS:")
for t in tokens:
    print(f"  {t.type.name}('{t.value}') at line {t.line}")

print("\n---Parsing---")

# Add debug to parser
import Cafe.Parser_cafe.parser as parser_module
original_var_decl = parser_module.BottomUpParser._var_decl

def debug_var_decl(self):
    if len(self.stack) >= 5:
        dtype, name, eq, expr, semi = self.stack[-5:]
        print(f"DEBUG _var_decl: dtype={type(dtype).__name__}({getattr(dtype, 'type', '?')}), name={type(name).__name__}({getattr(name, 'name', '?')}), eq={type(eq).__name__}({getattr(eq, 'type', '?')}), expr={type(expr).__name__}({getattr(expr, 'dtype', '?')}), semi={type(semi).__name__}({getattr(semi, 'type', '?')})")
    return original_var_decl(self)

parser_module.BottomUpParser._var_decl = debug_var_decl

parser = BottomUpParser(tokens)
try:
    ast = parser.parse()
    print("SUCCESS")
except Exception as e:
    print(f"ERROR: {e}")

print(f"\nSymbol table scopes: {parser.symbol_table.scopes}")
