from Parser_cafe.parser import BottomUpParser
from Scanner.Scanner import Scanner

# with open("test.cafe") as f:
#     source = f.read()
source = """
count x = 5 ;
count y = 10 ;
serve << x + y ;
"""

tokens = Scanner(source).scan_tokens()

parser = BottomUpParser(tokens)
ast = parser.parse()

print(ast)

for stmt in ast.statements:
    print(stmt)