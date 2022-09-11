import ast
import os
from importlib.machinery import ModuleSpec
import typing
import logging

from deba.deps.module import Loader, Node, Stack

from deba.deps.expr import ExprPattern


logger = logging.getLogger("deba")


class ModuleParseError(ValueError):
    pass


def is_name(node, id) -> bool:
    return isinstance(node, ast.Name) and node.id == id


def is_const(node, val) -> bool:
    return isinstance(node, ast.Constant) and node.value == val


def is_main_block(stmt: ast.stmt) -> bool:
    return (
        isinstance(stmt, ast.If)
        and is_name(stmt.test.left, "__name__")
        and isinstance(stmt.test.ops[0], ast.Eq)
        and is_const(stmt.test.comparators[0], "__main__")
    )


def trim_suffix(s: str, suffix: str) -> str:
    if s.endswith(suffix):
        return s[: -len(suffix)]
    return s


def build_module_from_filepath(loader: Loader, filepath: str) -> Node:
    if not os.path.isfile(filepath):
        if not os.path.isdir(filepath) or not os.path.isfile(
            os.path.join(filepath, "__init__.py")
        ):
            raise ValueError("not a file path: %s" % filepath)
    parent, filename = os.path.split(filepath)
    node = loader.find_module(trim_suffix(filename, ".py"), [parent])
    return node


def find_dependencies(
    loader: Loader,
    filepath: str,
    prerequisite_patterns: typing.List[ExprPattern],
    reference_patterns: typing.List[ExprPattern],
    target_patterns: typing.List[ExprPattern],
) -> typing.Tuple[typing.List[str], typing.List[str]]:
    module_node = build_module_from_filepath(loader, filepath)
    stack = Stack()
    for stmt in module_node.ast.body:
        if is_main_block(stmt):
            return scan(
                loader,
                stmt,
                module_node.spec,
                stack.push(),
                prerequisite_patterns,
                reference_patterns,
                target_patterns,
            )
        else:
            loader.populate_scope(module_node.spec, stack, module_node.ast, stmt)
    raise ModuleParseError("main block not found")


def scan_patterns(
    stack: Stack,
    call: ast.Call,
    patterns: typing.List[ExprPattern],
    extracted: typing.List[str],
) -> bool:
    for tmpl in patterns:
        s = tmpl.match_node(stack, call)
        if s is not None:
            extracted.append(s)
            return True
    return False


def scan(
    loader: Loader,
    node: ast.AST,
    spec: ModuleSpec,
    stack: Stack,
    prerequisite_patterns: typing.List[ExprPattern],
    reference_patterns: typing.List[ExprPattern],
    target_patterns: typing.List[ExprPattern],
) -> typing.Tuple[typing.List[str], typing.List[str], typing.List[str]]:
    prerequisites, references, targets = [], [], []
    for stmt in node.body:
        loader.populate_scope(spec, stack, node, stmt)
        for t in ast.walk(stmt):
            if isinstance(t, ast.Call):
                if scan_patterns(stack, t, target_patterns, targets):
                    continue
                if scan_patterns(stack, t, prerequisite_patterns, prerequisites):
                    continue
                if scan_patterns(stack, t, reference_patterns, references):
                    continue

                func = stack.dereference(t.func)
                if func is None or not isinstance(func.ast, ast.FunctionDef):
                    continue
                pre, ref, tar = scan(
                    loader,
                    func.ast,
                    func.spec,
                    stack.push(),
                    prerequisite_patterns,
                    reference_patterns,
                    target_patterns,
                )
                prerequisites = prerequisites + pre
                references = references + ref
                targets = targets + tar
    return prerequisites, references, targets
