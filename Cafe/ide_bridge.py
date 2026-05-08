import json
import re
import sys
from pathlib import Path

from CodeGen.cpp_generator import CppGenerator, compile_cpp, run_executable
from Parser_cafe.parser import BottomUpParser
from Scanner.Scanner import Scanner


DIAGNOSTIC_RE = re.compile(r"line\s+(\d+)(?:,\s*col(?:umn)?\s+(\d+))?", re.IGNORECASE)


def diagnostic(stage, message, severity="error"):
    match = DIAGNOSTIC_RE.search(message)
    line = int(match.group(1)) if match else None
    column = int(match.group(2)) if match and match.group(2) else None
    return {
        "stage": stage,
        "severity": severity,
        "message": message,
        "line": line,
        "column": column,
    }


def compile_request(payload):
    source = payload.get("source", "")
    action = payload.get("action", "generate")
    output_path = Path(payload.get("outputPath") or "output.cpp")

    response = {
        "ok": False,
        "action": action,
        "diagnostics": [],
        "logs": [],
        "tokens": [],
        "ast": "",
        "cppSource": "",
        "runtimeOutput": "",
        "outputPath": str(output_path),
    }

    try:
        scanner = Scanner(source)
        tokens = scanner.scan_tokens()
        response["tokens"] = [
            {
                "type": token.type.name,
                "value": token.value,
                "line": token.lineNumber,
                "column": token.columnNumber,
            }
            for token in tokens
        ]
        response["logs"].append("Scanner completed")
    except Exception as error:
        message = str(error)
        response["diagnostics"].append(diagnostic("Scanner", message))
        response["logs"].append(f"Scanner Error: {message}")
        return response

    try:
        ast = BottomUpParser(tokens).parse()
        response["ast"] = str(ast)
        response["logs"].append("Parser and semantic analysis completed")
    except SyntaxError as error:
        for message in str(error).splitlines() or [str(error)]:
            response["diagnostics"].append(diagnostic("Parser", message))
        response["logs"].append(f"Parser Error: {error}")
        return response
    except Exception as error:
        message = str(error)
        response["diagnostics"].append(diagnostic("Semantic", message))
        response["logs"].append(f"Semantic Error: {message}")
        return response

    try:
        cpp_source = CppGenerator(ast, output_path=output_path).generate(write_file=True)
        response["cppSource"] = cpp_source
        response["logs"].append(f"Generated C++: {output_path}")
    except Exception as error:
        message = str(error)
        response["diagnostics"].append(diagnostic("Code Generation", message))
        response["logs"].append(f"Code Generation Error: {message}")
        return response

    if action in {"compile", "run"}:
        executable_path = output_path.with_suffix(".exe")
        try:
            compile_result = compile_cpp(output_path, executable_path)
        except OSError as error:
            message = f"could not start g++ ({error})"
            response["diagnostics"].append(diagnostic("C++ Compile", message))
            response["logs"].append(f"C++ Compile Error: {message}")
            return response

        if compile_result.stdout:
            response["logs"].append(compile_result.stdout.strip())
        if compile_result.stderr:
            response["logs"].append(compile_result.stderr.strip())
        if compile_result.returncode != 0:
            response["diagnostics"].append(diagnostic("C++ Compile", compile_result.stderr.strip()))
            return response

        response["logs"].append(f"Compiled executable: {executable_path}")

        if action == "run":
            try:
                run_result = run_executable(executable_path)
            except OSError as error:
                message = f"could not start executable ({error})"
                response["diagnostics"].append(diagnostic("Runtime", message))
                response["logs"].append(f"Runtime Error: {message}")
                return response

            response["runtimeOutput"] = run_result.stdout
            if run_result.stderr:
                response["logs"].append(run_result.stderr.strip())
            if run_result.returncode != 0:
                response["diagnostics"].append(diagnostic("Runtime", run_result.stderr.strip()))
                return response

            response["logs"].append("Program executed successfully")

    response["ok"] = True
    return response


def main():
    try:
        payload = json.loads(sys.stdin.read() or "{}")
        result = compile_request(payload)
    except Exception as error:
        result = {
            "ok": False,
            "diagnostics": [diagnostic("Bridge", str(error))],
            "logs": [f"Bridge Error: {error}"],
        }

    print(json.dumps(result))


if __name__ == "__main__":
    main()
