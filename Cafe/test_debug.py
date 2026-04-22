import sys
import traceback
sys.path.insert(0, '.')

from Parser_cafe.parser import BottomUpParser
from Parser_cafe.ast import Node, IdentifierNode, LiteralNode
from Scanner.Scanner import Scanner

code = """
count x = 5;
"""

scanner = Scanner(code)
tokens = scanner.scan_tokens()

print("TOKENS:")
for t in tokens:
    print(f"  {t.type.name}('{t.value}')")

print("\n---Parsing with debug---")

parser = BottomUpParser(tokens)
try:
    ast = parser.parse()
    print("\nSUCCESS")
except Exception as e:
    print(f"\nERROR: {e}")
    traceback.print_exc()

print(f"\nFinal stack: {parser.stack}")
print(f"Symbol table scopes: {parser.symbol_table.scopes}")


