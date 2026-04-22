from Parser_cafe.parser import BottomUpParser
from Scanner.Scanner import Scanner


def run_code(source):
    print("\n========== SOURCE ==========")
    print(source)

    try:
        # =========================
        # 1. SCANNING
        # =========================
        scanner = Scanner(source)
        tokens = scanner.scan_tokens()

        print("\n========== TOKENS ==========")
        for t in tokens:
            print(t)

        # =========================
        # 2. PARSING + SEMANTIC
        # =========================
        parser = BottomUpParser(tokens)
        ast = parser.parse()

        print("\n========== AST ==========")
        print(ast)

        print("\n========== STATEMENTS ==========")
        for stmt in ast.statements:
            print(stmt)

        print("\n✅ SUCCESS: Parsing + Semantic Passed\n")

    except Exception as e:
        print("\n❌ ERROR:")
        print(e)
        print()


# =========================
# TEST CASES
# =========================

if __name__ == "__main__":

    # ✅ Test 1 (Correct)
    code1 = """
    count x = 5;
    count y = 10;
    serve << x + y;
    """

    # ❌ Test 2 (Type error)
    code2 = """
    count x = 5;
    note y = "hello";
    serve << x + y;
    """

    # ❌ Test 3 (Undeclared variable)
    code3 = """
    serve << z;
    """

    # ✅ Test 4 (Function)
    code4 = """
    count recipe add(count a, count b) {
        bill a + b;
    }
    """

    # ❌ Test 5 (Return mismatch)
    code5 = """
    count recipe add(count a, count b) {
        note result = a + b;
        bill result;
    }
    """
    code6 = """
    count x=5;
    count y = 10;
    serve << x+ y;
    
    """
    # =========================
    # RUN
    # =========================

    run_code(code1)
    run_code(code2)
    run_code(code3)
    run_code(code4)
    run_code(code5)
    run_code(code6)