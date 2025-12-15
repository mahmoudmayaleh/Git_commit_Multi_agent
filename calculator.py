#!/usr/bin/env python3
"""Simple safe CLI calculator

Features:
- Safe expression evaluation using Python's AST (no eval)
- Supports +, -, *, /, %, **, unary +/-, parentheses
- Supports math functions: sin, cos, tan, sqrt, log, exp, pow, fabs, floor, ceil
- History navigation (command: history)
- Memory: M+, M-, MR, MC commands
- Other commands: help, clear, exit, quit

Usage: run `python calculator.py` and type expressions at the prompt.
Example:
  > 2 + 3 * (4 - 1)
  11
  > sin(3.14/2)
  0.999999682... 
  > M+ 10      # add 10 to memory
  > MR         # recall memory

This file is intentionally standalone and has no external dependencies.
"""
#adding new comment to test git commit multi agent
from __future__ import annotations

import ast
import math
import operator as op
from typing import Any, Dict


# Allowed binary operators mapping
_BINARY_OPS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.FloorDiv: op.floordiv,
    ast.Mod: op.mod,
    ast.Pow: op.pow,
    ast.BitXor: op.xor,
}

# Allowed unary operators
_UNARY_OPS = {
    ast.UAdd: op.pos,
    ast.USub: op.neg,
}

# Whitelist of functions from math module
_MATH_FUNCS = {
    name: getattr(math, name)
    for name in (
        "sin",
        "cos",
        "tan",
        "asin",
        "acos",
        "atan",
        "sqrt",
        "log",
        "log10",
        "exp",
        "pow",
        "fabs",
        "floor",
        "ceil",
        "degrees",
        "radians",
    )
}


class EvalError(Exception):
    pass


def _eval_node(node: ast.AST, names: Dict[str, Any]) -> Any:
    """Evaluate an AST node safely using whitelisted nodes."""
    if isinstance(node, ast.Expression):
        return _eval_node(node.body, names)

    if isinstance(node, ast.Num):  # type: ignore[attr-defined]
        return node.n

    if isinstance(node, ast.Constant):  # py3.8+
        if isinstance(node.value, (int, float, complex)):
            return node.value
        raise EvalError(f"Unsupported constant: {node.value!r}")

    if isinstance(node, ast.BinOp):
        left = _eval_node(node.left, names)
        right = _eval_node(node.right, names)
        op_type = type(node.op)
        if op_type in _BINARY_OPS:
            try:
                return _BINARY_OPS[op_type](left, right)
            except Exception as e:
                raise EvalError(str(e))
        raise EvalError(f"Unsupported binary operator: {op_type}")

    if isinstance(node, ast.UnaryOp):
        operand = _eval_node(node.operand, names)
        op_type = type(node.op)
        if op_type in _UNARY_OPS:
            return _UNARY_OPS[op_type](operand)
        raise EvalError(f"Unsupported unary operator: {op_type}")

    if isinstance(node, ast.Call):
        # Only allow simple function calls: func(args...)
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name in _MATH_FUNCS:
                func = _MATH_FUNCS[func_name]
                args = [_eval_node(arg, names) for arg in node.args]
                try:
                    return func(*args)
                except Exception as e:
                    raise EvalError(str(e))
            # allow use of 'abs' and 'round'
            if func_name == 'abs':
                args = [_eval_node(arg, names) for arg in node.args]
                return abs(*args)
            if func_name == 'round':
                args = [_eval_node(arg, names) for arg in node.args]
                return round(*args)
        raise EvalError("Only math functions are allowed (e.g. sin, cos, sqrt)")

    if isinstance(node, ast.Name):
        if node.id in names:
            return names[node.id]
        # allow constants from math
        if node.id == 'pi':
            return math.pi
        if node.id == 'e':
            return math.e
        raise EvalError(f"Unknown identifier: {node.id}")

    if isinstance(node, ast.Tuple):
        return tuple(_eval_node(elt, names) for elt in node.elts)

    raise EvalError(f"Unsupported expression: {ast.dump(node)}")


def safe_eval(expr: str, names: Dict[str, Any] | None = None) -> Any:
    """Safely evaluate a math expression string and return the result.

    Raises EvalError on unsupported constructs.
    """
    names = names or {}
    try:
        parsed = ast.parse(expr, mode='eval')
    except SyntaxError as e:
        raise EvalError(f"Syntax error: {e}")
    # Walk AST to ensure no disallowed nodes
    for node in ast.walk(parsed):
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.Attribute, ast.Lambda, ast.Dict, ast.Set, ast.ListComp, ast.GeneratorExp)):
            raise EvalError("Unsupported or unsafe expression")
    return _eval_node(parsed, names)


def print_help() -> None:
    print("Simple CLI calculator")
    print("Enter arithmetic expressions using + - * / % ** and parentheses.")
    print("Available functions: " + ", ".join(sorted(_MATH_FUNCS.keys())))
    print("Commands:")
    print("  help        Show this help")
    print("  history     Show evaluation history")
    print("  last        Recall last calculation result")
    print("  M+ <expr>   Add evaluated expr to memory")
    print("  M- <expr>   Subtract evaluated expr from memory")
    print("  MR          Recall memory")
    print("  MC          Clear memory")
    print("  vars        Show all variables")
    print("  del <name>  Delete a variable")
    print("  clear       Clear screen (if supported)")
    print("  exit/quit   Exit")


def repl() -> None:
    memory = 0.0
    history: list[tuple[str, Any]] = []
    names: Dict[str, Any] = {}
    last_result: Any = None

    print("Calculator — type 'help' for commands. Press Ctrl-C to exit.")

    while True:
        try:
            raw = input('> ').strip()
        except (EOFError, KeyboardInterrupt):
            print('\nGoodbye')
            break

        if not raw:
            continue

        # Commands
        cmd = raw.lower()
        if cmd in ('exit', 'quit'):
            print('Bye')
            break
        if cmd == 'help':
            print_help()
            continue
        if cmd == 'history':
            if not history:
                print('(no history)')
            else:
                for i, (expr, res) in enumerate(history[-50:], start=1):
                    if isinstance(res, float):
                        res_str = format(res, '.12g')
                    else:
                        res_str = str(res)
                    print(f"{i}: {expr} = {res_str}")
            continue
        if cmd == 'mr':
            print(format(memory, '.12g'))
            continue
        if cmd == 'mc':
            memory = 0.0
            print('Memory cleared')
            continue
        if cmd == 'last':
            if last_result is not None:
                if isinstance(last_result, float):
                    print(format(last_result, '.12g'))
                else:
                    print(last_result)
            else:
                print('(no last result)')
            continue
        if cmd == 'vars':
            if not names:
                print('(no variables)')
            else:
                for k, v in names.items():
                    if isinstance(v, float):
                        vstr = format(v, '.12g')
                    else:
                        vstr = str(v)
                    print(f"{k} = {vstr}")
            continue
        if cmd.startswith('del '):
            var = raw[4:].strip()
            if var in names:
                del names[var]
                print(f"Deleted variable '{var}'")
            else:
                print(f"Unknown variable: {var}")
            continue
        if cmd.startswith('m+ ' ) or cmd.startswith('m+'):
            to_eval = raw[2:].strip()
            try:
                val = safe_eval(to_eval, names)
                memory += float(val)
                print(f'Memory = {memory}')
            except EvalError as e:
                print('Error:', e)
            except Exception as e:
                print('Error:', e)
            continue
        if cmd.startswith('m- ') or cmd.startswith('m-'):
            to_eval = raw[2:].strip()
            try:
                val = safe_eval(to_eval, names)
                memory -= float(val)
                print(f'Memory = {memory}')
            except EvalError as e:
                print('Error:', e)
            except Exception as e:
                print('Error:', e)
            continue
        if cmd == 'clear':
            # try to clear screen
            import os
            #import os for some reason is hereg
            os.system('clear' if hasattr(os, 'system') else '')
            continue

        # Assignment handling: name = expr
        if '=' in raw and not raw.strip().startswith(('m+', 'm-',)):
            parts = raw.split('=', 1)
            varname = parts[0].strip()
            expr = parts[1].strip()
            # validate variable name
            import re

            if re.fullmatch(r'[A-Za-z_]\w*', varname):
                try:
                    val = safe_eval(expr, names)
                    names[varname] = val
                    last_result = val
                    if isinstance(val, float):
                        print(f"{varname} = {format(val, '.12g')}")
                    else:
                        print(f"{varname} = {val}")
                    history.append((raw, val))
                except EvalError as e:
                    print('Error:', e)
                except Exception as e:
                    print('Error:', e)
                continue

        # Evaluate expression
        try:
            result = safe_eval(raw, names)
            last_result = result
            # If result is float-like, show nicely
            if isinstance(result, float):
                print(format(result, '.12g'))
            else:
                print(result)
            history.append((raw, result))
        except EvalError as e:
            print('Error:', e)
        except Exception as e:
            print('Error:', e)


if __name__ == '__main__':
    repl()
# Adding a new comment to test git commit multi agent