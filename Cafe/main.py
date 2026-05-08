import argparse
from pathlib import Path

from CodeGen.cpp_generator import (
    CodeGenerationError,
    CppGenerator,
    compile_cpp,
    run_executable,
)
from Parser_cafe.parser import BottomUpParser
from Scanner.Scanner import Scanner


class CompilerResult:
    def __init__(self, ast=None, cpp_source=None, output_path=None):
        self.ast = ast
        self.cpp_source = cpp_source
        self.output_path = output_path


def scan_source(source):
    try:
        return Scanner(source).scan_tokens()
    except Exception as error:
        raise RuntimeError(f"Scanner Error: {error}") from error


def parse_tokens(tokens):
    try:
        return BottomUpParser(tokens).parse()
    except SyntaxError as error:
        raise RuntimeError(f"Parser Error: {error}") from error
    except Exception as error:
        raise RuntimeError(f"Semantic Error: {error}") from error


def generate_cpp_source(ast, output_path):
    try:
        return CppGenerator(ast, output_path=output_path).generate()
    except CodeGenerationError as error:
        raise RuntimeError(f"Code Generation Error: {error}") from error
    except Exception as error:
        raise RuntimeError(f"Code Generation Error: {error}") from error


def compile_source(source, output_path="output.cpp", compile_output=False, run_output=False):
    tokens = scan_source(source)
    ast = parse_tokens(tokens)
    cpp_source = generate_cpp_source(ast, output_path)

    if compile_output or run_output:
        executable_path = Path(output_path).with_suffix(".exe")
        try:
            result = compile_cpp(output_path, executable_path)
        except OSError as error:
            raise RuntimeError(f"C++ Compile Error: could not start g++ ({error})") from error
        if result.returncode != 0:
            raise RuntimeError(f"C++ Compile Error:\n{result.stderr.strip()}")

        if run_output:
            try:
                run_result = run_executable(executable_path)
            except OSError as error:
                raise RuntimeError(f"Runtime Error: could not start executable ({error})") from error
            if run_result.returncode != 0:
                raise RuntimeError(f"Runtime Error:\n{run_result.stderr.strip()}")
            print(run_result.stdout, end="")

    return CompilerResult(ast=ast, cpp_source=cpp_source, output_path=output_path)


def run_code(source, output_path="output.cpp", compile_output=False, run_output=False, verbose=True):
    if verbose:
        print("\n========== SOURCE ==========")
        print(source)

    try:
        result = compile_source(source, output_path, compile_output, run_output)
    except RuntimeError as error:
        print(f"\n{error}\n")
        return None

    if verbose:
        print("\n========== AST ==========")
        print(result.ast)

        print("\n========== GENERATED C++ ==========")
        print(result.cpp_source)
        print(f"\nGenerated: {result.output_path}")
        print("\nSUCCESS: Compilation pipeline completed\n")

    return result


def read_source(path):
    return Path(path).read_text(encoding="utf-8")


def build_arg_parser():
    parser = argparse.ArgumentParser(description="Cafe compiler driver")
    parser.add_argument("source", nargs="?", help="Cafe source file to compile")
    parser.add_argument("-o", "--output", default="output.cpp", help="Generated C++ output path")
    parser.add_argument("--compile", action="store_true", help="Compile generated C++ with g++")
    parser.add_argument("--run", action="store_true", help="Compile and run generated executable")
    parser.add_argument("--quiet", action="store_true", help="Only print errors and program output")
    return parser


def demo_sources():
    return [
        """
        count x = 5;
        count y = 10;
        serve << x + y;
        """,
        """
        count recipe add(count a, count b) {
            bill a + b;
        }
        serve << add(2, 3);
        """,
    ]


def main(argv=None):
    args = build_arg_parser().parse_args(argv)
    compile_flag = args.compile or args.run

    if args.source:
        return 0 if run_code(
            read_source(args.source),
            output_path=args.output,
            compile_output=compile_flag,
            run_output=args.run,
            verbose=not args.quiet,
        ) else 1

    status = 0
    for source in demo_sources():
        if run_code(
            source,
            output_path=args.output,
            compile_output=compile_flag,
            run_output=args.run,
            verbose=not args.quiet,
        ) is None:
            status = 1
    return status


if __name__ == "__main__":
    raise SystemExit(main())
