import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAFE_DIR = ROOT / "Cafe"
sys.path.insert(0, str(CAFE_DIR))

from CodeGen.cpp_generator import CppGenerator
from Parser_cafe.ast import LiteralNode
from Parser_cafe.parser import BottomUpParser
from Scanner.Scanner import Scanner


def generate(source):
    tokens = Scanner(source).scan_tokens()
    ast = BottomUpParser(tokens).parse()
    return CppGenerator(ast, output_path=ROOT / "tests" / "tmp_output.cpp").generate(write_file=False)


def test_expressions_and_conditions():
    cpp = generate("""
    count x = 2 + 3 * 4;
    check (x < 20) {
        serve << x;
    } instead {
        serve << 0;
    }
    """)

    assert "double x = (2 + (3 * 4));" in cpp
    assert "if ((x < 20)) {" in cpp
    assert "} else {" in cpp


def test_functions_and_recursive_calls():
    cpp = generate("""
    count recipe fact(count n) {
        check (n < 2) {
            bill 1;
        }
        bill n * fact(n - 1);
    }
    serve << fact(5);
    """)

    assert "double fact(double n);" in cpp
    assert "double fact(double n) {" in cpp
    assert "return (n * fact((n - 1)));" in cpp
    assert "cout << fact(5) << endl;" in cpp


def test_arrays_and_array_access():
    cpp = generate("""
    count package prices[3] = {10, 20, 30};
    prices[2] = 50;
    serve << prices[2];
    """)

    assert "double prices[3] = { 10, 20, 30 };" in cpp
    assert "prices[2] = 50;" in cpp
    assert "cout << prices[2] << endl;" in cpp


def test_loops_and_switch():
    cpp = generate("""
    count i = 0;
    refill (i = 0; i < 3; i = i + 1) {
        serve << i;
    }
    menu (i) {
        item 3:
            serve << i;
        done;
        any_drink:
            serve << 0;
    }
    """)

    assert "for (i = 0; (i < 3); i = (i + 1)) {" in cpp
    assert "switch (static_cast<int>(i)) {" in cpp
    assert "case 3:" in cpp
    assert "default:" in cpp


def test_bool_and_char_literals():
    cpp = generate("""
    coin ready = hot;
    emo mark = 'x';
    serve << ready;
    serve << mark;
    """)

    assert "bool ready = true;" in cpp
    assert "char mark = 'x';" in cpp


def test_string_escaping_helper():
    literal = LiteralNode("line\nnext\tend\r")
    literal.dtype = "string"

    cpp = CppGenerator(literal).visit(literal)

    assert cpp == '"line\\nnext\\tend\\r"'
