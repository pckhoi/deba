import ast
from importlib.machinery import ModuleSpec
import typing

from attr import define, field


@define
class Node(object):
    t: ast.AST
    spec: ModuleSpec = field(default=None)
    children: typing.Union[typing.Dict[str, "Node"], None] = field(default=None)

    def get_descendant(self, dotted_path: str) -> typing.Union["Node", None]:
        return Stack([self.children]).get_value(dotted_path)


@define
class Stack(object):
    layers: typing.List[typing.Dict[str, Node]] = field(factory=lambda: [dict()])

    def push(self) -> "Stack":
        return Stack(self.layers + [dict()])

    def pop(self) -> "Stack":
        return Stack(self.layers[:-1])

    def store(self, key: str, node: Node):
        self.layers[-1][key] = node

    def current_scope(self) -> dict:
        return self.layers[-1].copy()

    def get_value(self, dotted_path: str) -> typing.Union["Node", None]:
        parts = dotted_path.split(".")
        for scope in reversed(self.layers):
            if parts[0] not in scope:
                continue
            for name in parts:
                if scope is None:
                    return None
                node = scope.get(name, None)
                if node is None:
                    return None
                scope = node.children
            return node

    def dereference(self, t: ast.AST) -> typing.Union[Node, None]:
        if isinstance(t, ast.Name):
            return self.get_value(t.id)
        elif isinstance(t, ast.Attribute):
            stack = []
            expr = t
            while isinstance(expr, ast.Attribute):
                stack.append(expr)
                expr = expr.value
            if not isinstance(expr, ast.Name):
                return None
            node = self.get_value(expr.id)
            if node is not None:
                while len(stack) > 0:
                    attr = stack.pop()
                    node = node.get_descendant(attr.attr)
            return node
