import sys
sys.path.insert(0, '.')

from Parser_cafe.parser import BottomUpParser
from Scanner.Scanner import Scanner

code = """
count recipe add(count a, count b) {
    bill a + b;
}
"""

scanner = Scanner(code)
tokens = scanner.scan_tokens()

print("TOKENS:")
for i, t in enumerate(tokens):
    print(f"  [{i}] {t.type.name}('{t.value}')")

print("\n---Parsing---")

# Debug _on_lbrace_shifted
import Parser_cafe.parser as pm
orig_on_lbrace = pm.BottomUpParser._on_lbrace_shifted

def debug_on_lbrace(self):
    print(f"\n_on_lbrace_shifted called! Stack has {len(self.stack)} items")
    for i, item in enumerate(self.stack[-5:]):
        print(f"  stack[{i}] = {item}")
    
    func_params = self._detect_function_header()
    print(f"  _detect_function_header returned: {func_params}")
    
    orig_on_lbrace(self)

pm.BottomUpParser._on_lbrace_shifted = debug_on_lbrace

parser = BottomUpParser(tokens)
try:
    ast = parser.parse()
    print("\nSUCCESS")
except Exception as e:
    print(f"\nERROR: {e}")

print(f"\nFinal symbol table scopes: {parser.symbol_table.scopes}")


