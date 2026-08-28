import ast
import operator
import math
import os
from .base import BaseProvider, SearchResult
from i18n import t

class SafeMathEval(ast.NodeVisitor):
    def __init__(self):
        self.operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Mod: operator.mod,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,
            ast.UAdd: operator.pos,
        }
        self.functions = {
            'sqrt': math.sqrt,
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'abs': abs,
            'round': round,
            'log': math.log10,
            'ln': math.log,
        }

    def visit_BinOp(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        op_type = type(node.op)
        if op_type is ast.Pow:
            if isinstance(right, (int, float)) and abs(right) > 1000:
                raise ValueError("Exponent too large")
        if op_type in self.operators:
            return self.operators[op_type](left, right)
        raise ValueError("Unsupported operation")

    def visit_UnaryOp(self, node):
        operand = self.visit(node.operand)
        op_type = type(node.op)
        if op_type in self.operators:
            return self.operators[op_type](operand)
        raise ValueError("Unsupported unary operation")

    def visit_Constant(self, node):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("Unsupported constant type")

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name in self.functions:
                args = [self.visit(arg) for arg in node.args]
                return self.functions[func_name](*args)
        raise ValueError("Unsupported function")

    def visit_Name(self, node):
        if node.id == 'pi': return math.pi
        if node.id == 'e': return math.e
        raise ValueError("Unknown variable")

    def generic_visit(self, node):
        raise ValueError(f"Unsupported syntax: {type(node).__name__}")


def safe_eval(expr_string: str):
    if not any(char in expr_string for char in "+-*/%^0123456789("):
        return None
    try:
        expr_string = expr_string.replace('^', '**')
        tree = ast.parse(expr_string, mode='eval')
        evaluator = SafeMathEval()
        result = evaluator.visit(tree.body)
        
        if isinstance(result, float) and result.is_integer():
            return int(result)
        if isinstance(result, float):
            return round(result, 6)
        return result
    except Exception:
        return None


class CalculatorProvider(BaseProvider):
    def __init__(self, history_manager=None):
        super().__init__(history_manager)
        self.history_file = os.path.expanduser("~/.local/share/echo/calc_history.json")
        self.history = []
        self._load_history()

    def _load_history(self):
        try:
            import json
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    self.history = json.load(f)
        except Exception:
            pass

    def _save_history(self, expr: str, res: str):
        self.history = [{"expr": expr, "res": res}] + [h for h in self.history if h["expr"] != expr][:9]
        try:
            import json
            os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
            with open(self.history_file, 'w') as f:
                json.dump(self.history, f)
        except Exception:
            pass

    def _create_result(self, query: str, result: str) -> SearchResult:
        res_str = str(result)
        if len(res_str) > 500:
            res_str = res_str[:50] + "..."

        def _copy_callback():
            try:
                self._save_history(query, res_str)
                import gi
                gi.require_version('Gtk', '4.0')
                from gi.repository import Gdk
                display = Gdk.Display.get_default()
                if display:
                    display.get_clipboard().set(str(result))
            except Exception:
                pass

        return SearchResult(
            id=f"math_{query}",
            title=str(result),
            subtitle=t("provider_math_subtitle", query=query),
            icon="accessories-calculator",
            score=200,
            category="Math",
            provider="CalculatorProvider",
            preview_data={"result": str(result), "history": self.history},
            action_execute=_copy_callback,
            action_copy=_copy_callback
        )

    def search(self, query: str, limit: int = 10, category_filter: str = None) -> list[SearchResult]:
        if category_filter not in (None, "All"):
            return []
        try:
            math_res = safe_eval(query)
            if math_res is not None:
                return [self._create_result(query, math_res)]
        except Exception:
            return []
        return []
