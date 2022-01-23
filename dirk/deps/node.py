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
        return Scopes([self.children]).get_value(dotted_path)


@define
class Scopes(object):
    layers: typing.List[typing.Dict[str, Node]] = field(factory=list)

    def add_scope(self, scope: typing.Dict[str, Node]) -> "Scopes":
        return Scopes(self.layers + [scope])

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
