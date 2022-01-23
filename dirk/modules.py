import ast
import os
from importlib.machinery import ModuleSpec, PathFinder
import typing

from attr import define, field


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


def get_value_from_scopes(
    scopes: typing.List[typing.Dict[str, "Node"]], dotted_path: str
) -> typing.Union["Node", None]:
    parts = dotted_path.split(".")
    for scope in reversed(scopes):
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


@define
class Node(object):
    t: ast.AST
    children: typing.Union[typing.Dict[str, "Node"], None] = field(default=None)

    def get_descendant(self, dotted_path: str) -> typing.Union["Node", None]:
        return get_value_from_scopes([self.children], dotted_path)


@define
class NodeFactory(object):
    paths: typing.List[str]
    module_asts: typing.Dict[str, ast.Module] = field(factory=dict)
    module_nodes: typing.Dict[str, Node] = field(factory=dict)

    def build_module_from_filepath(self, filepath: str) -> "Node":
        if not os.path.isfile(filepath):
            raise ValueError("not a file path: %s" % filepath)
        parent, filename = os.path.split(filepath)
        return self.build_module(trim_suffix(filename, ".py"), [parent])

    def find_module(
        self,
        module_name: str,
        parent_module_paths: typing.Union[typing.List[str], None] = None,
    ) -> typing.Union[ModuleSpec, None]:
        parts = module_name.split(".")
        paths = (
            self.paths
            if parent_module_paths is None
            else parent_module_paths + self.paths
        )
        for name in parts:
            spec = PathFinder.find_spec(name, paths)
            if spec is None:
                return None
            paths = getattr(spec, "submodule_search_locations", [])
        return spec

    def parse_module(self, origin: str) -> ast.Module:
        if origin in self.module_asts:
            return self.module_asts[origin]
        with open(origin, "r") as f:
            root = ast.parse(f.read(), os.path.split(origin)[-1])
            self.module_asts[origin] = root
            return root

    def collect_submodules(self, spec: ModuleSpec, node: Node):
        for filename in spec.loader.get_resource_reader().contents():
            if filename == "__init__.py":
                continue
            if filename.endswith(".py"):
                name = trim_suffix(filename, ".py")
                node.children[name] = self.build_module(
                    name, spec.submodule_search_locations
                )
            elif os.path.isdir(
                os.path.join(spec.submodule_search_locations[0], filename)
            ) and os.path.exists(
                os.path.join(
                    spec.submodule_search_locations[0], filename, "__init__.py"
                )
            ):
                node.children[filename] = self.build_module(
                    filename, spec.submodule_search_locations
                )

    def build_module(
        self,
        module_name: str,
        parent_module_paths: typing.Union[typing.List[str], None] = None,
    ) -> typing.Union[Node, None]:
        spec = self.find_module(module_name, parent_module_paths)
        if spec is None:
            return None
        if spec.origin in self.module_nodes:
            return self.module_nodes[spec.origin]
        mod = self.parse_module(spec.origin)
        node = self.build_from_ast(mod, spec.submodule_search_locations, [])
        if os.path.split(spec.origin)[-1] == "__init__.py":
            self.collect_submodules(spec, node)
        self.module_nodes[spec.origin] = node
        return node

    def build_from_ast(
        self,
        t: ast.AST,
        peer_module_paths: typing.Union[typing.List[str], None],
        scopes: typing.List[typing.Dict[str, "Node"]],
    ) -> "Node":
        """Builds a tree from an ast"""
        if hasattr(t, "body"):
            children = dict()
            for stmt in t.body:
                if isinstance(stmt, ast.Import):
                    for alias in stmt.names:
                        node = self.build_module(alias.name, peer_module_paths)
                        if node is not None:
                            children[
                                alias.name if alias.asname is None else alias.asname
                            ] = node
                elif isinstance(stmt, ast.ImportFrom):
                    node = self.build_module(stmt.module, peer_module_paths)
                    if node is not None:
                        for alias in stmt.names:
                            children[
                                alias.name if alias.asname is None else alias.asname
                            ] = node.get_descendant(alias.name)
                elif isinstance(stmt, ast.FunctionDef) or isinstance(
                    stmt, ast.AsyncFunctionDef
                ):
                    # ignore instance methods
                    if isinstance(t, ast.ClassDef):
                        instmed = True
                        for name in stmt.decorator_list:
                            if name.id in ["classmethod", "staticmethod"]:
                                instmed = False
                                break
                        if instmed:
                            continue
                    children[stmt.name] = Node(stmt)
                elif isinstance(stmt, ast.ClassDef):
                    children[stmt.name] = self.build_from_ast(
                        stmt, peer_module_paths, scopes + [children]
                    )
                elif isinstance(stmt, ast.Assign):
                    if isinstance(stmt.value, ast.Name):
                        node = get_value_from_scopes(scopes + [children], stmt.value.id)
                    elif isinstance(stmt.value, ast.Attribute):
                        stack = []
                        expr = stmt.value
                        while isinstance(expr, ast.Attribute):
                            stack.append(expr)
                            expr = expr.value
                        if not isinstance(expr, ast.Name):
                            continue
                        node = get_value_from_scopes(scopes + [children], expr.id)
                        if node is not None:
                            while len(stack) > 0:
                                attr = stack.pop()
                                node = node.get_descendant(attr.attr)
                    else:
                        node = self.build_from_ast(
                            stmt.value, peer_module_paths, scopes + [children]
                        )
                    for tgt in stmt.targets:
                        if isinstance(tgt, ast.Tuple):
                            if isinstance(node.t, ast.Tuple):
                                for idx, el in enumerate(tgt.elts):
                                    if isinstance(el, ast.Name):
                                        children[el.id] = self.build_from_ast(
                                            node.t.elts[idx],
                                            peer_module_paths,
                                            scopes + [children],
                                        )
                        elif isinstance(tgt, ast.Name):
                            children[tgt.id] = self.build_from_ast(
                                node.t, peer_module_paths, scopes + [children]
                            )
        else:
            children = None
        return Node(t, children)
