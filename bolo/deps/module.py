import ast
import typing
import os
from importlib.machinery import ModuleSpec, PathFinder

import zope.interface
from zope.interface.common.collections import IMapping
from attrs import define, field


@zope.interface.implementer(IMapping)
@define
class Node(object):
    ast: ast.AST
    spec: ModuleSpec
    children: typing.Union[typing.Dict[str, "Node"], None] = field(default=None)

    def __getitem__(self, key):
        if self.children is not None:
            return self.children[key]
        raise KeyError("key %s not found" % key)

    def __contains__(self, key):
        if self.children is not None:
            return key in self.children
        return False

    def get(self, key, default=None):
        if self.children is not None:
            return self.children.get(key, default)
        return default

    def keys(self):
        if self.children is not None:
            return self.children.keys()
        return []

    def items(self):
        if self.children is not None:
            return self.children.items()
        return []

    def values(self):
        if self.children is not None:
            return self.children.values()
        return []


@zope.interface.implementer(IMapping)
@define
class Module(object):
    ast: ast.Module
    spec: ModuleSpec
    children: typing.Dict[str, Node] = field(factory=dict)
    loaded: bool = field(default=False)

    def __getitem__(self, key):
        return self.children[key]

    def __contains__(self, key):
        return key in self.children

    def get(self, key, default=None):
        return self.children.get(key, default)

    def keys(self):
        return self.children.keys()

    def items(self):
        return self.children.items()

    def values(self):
        return self.children.values()


@zope.interface.implementer(IMapping)
@define
class Package(object):
    modules: typing.Dict[str, typing.Union[Module, "Package"]] = field(factory=dict)

    def __getitem__(self, key):
        if key in self.modules["__init__"]:
            return self.modules["__init__"][key]
        return self.modules[key]

    def __contains__(self, key):
        if key in self.modules["__init__"]:
            return True
        return key in self.modules

    def get(self, key, default=None):
        if key in self.modules["__init__"]:
            return self.modules["__init__"][key]
        return self.modules.get(key, default)

    def keys(self):
        for k in self.modules["__init__"].keys():
            yield k
        for k in self.modules.keys():
            if k != "__init__":
                yield k

    def items(self):
        for k, v in self.modules["__init__"].items():
            yield k, v
        for k, v in self.modules.items():
            if k != "__init__":
                yield k, v

    def values(self):
        for k, v in self.modules["__init__"].items():
            yield v
        for k, v in self.modules.items():
            if k != "__init__":
                yield v

    @classmethod
    def from_spec(
        cls, loader: "Loader", spec: ModuleSpec, ast: ast.Module
    ) -> "Package":
        package = Package()
        package.modules["__init__"] = Module(ast, spec)
        package.collect_submodules(loader, spec)
        return package

    def collect_submodules(self, loader: "Loader", spec: ModuleSpec):
        for filename in os.listdir(spec.submodule_search_locations[0]):
            if filename in ["__init__.py", "__main__.py"]:
                continue
            if filename.endswith(".py"):
                name = trim_suffix(filename, ".py")
                self.modules[name] = loader.find_module(
                    name, spec.submodule_search_locations
                )
            elif os.path.isdir(
                os.path.join(spec.submodule_search_locations[0], filename)
            ) and os.path.exists(
                os.path.join(
                    spec.submodule_search_locations[0], filename, "__init__.py"
                )
            ):
                self.modules[filename] = loader.find_module(
                    filename, spec.submodule_search_locations
                )


@define
class Stack(object):
    layers: typing.List[typing.Dict[str, object]] = field(factory=lambda: [dict()])

    def push(self) -> "Stack":
        return Stack(self.layers + [dict()])

    def pop(self) -> "Stack":
        return Stack(self.layers[:-1])

    def store(self, key: str, node):
        self.layers[-1][key] = node

    def current_scope(self) -> dict:
        return self.layers[-1].copy()

    def remove(self, key: str):
        self.layers[-1].pop(key)

    def current_keys(self) -> typing.List[str]:
        return list(self.layers[-1].keys())

    def get_value(self, dotted_path: str) -> typing.Union[object, None]:
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
                scope = node
            return node

    def dereference(self, t: ast.AST) -> typing.Union[Node, None]:
        if isinstance(t, ast.Name):
            return self.get_value(t.id)
        elif isinstance(t, ast.Attribute):
            stack: typing.List[ast.Attribute] = []
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
                    node = Stack([node]).get_value(attr.attr)
                    if node is None:
                        break
            return node


def trim_suffix(s: str, suffix: str) -> str:
    if s.endswith(suffix):
        return s[: -len(suffix)]
    return s


class ParseError(Exception):
    pass


@define
class Loader(object):
    paths: typing.List[str]
    module_asts: typing.Dict[str, ast.Module] = field(factory=dict)
    module_nodes: typing.Dict = field(factory=dict)

    def find_spec(
        self,
        module_name: str,
        parent_module_paths: typing.Union[typing.List[str], None] = None,
    ) -> typing.Union[ModuleSpec, None]:
        parts = module_name.split(".")
        paths = list(
            set(
                self.paths
                if parent_module_paths is None
                else parent_module_paths + self.paths
            )
        )
        for name in parts:
            spec = PathFinder.find_spec(name, paths)
            if spec is None:
                return None
            paths = getattr(spec, "submodule_search_locations", [])
        return spec

    def parse_ast(self, origin: str) -> ast.Module:
        if origin in self.module_asts:
            return self.module_asts[origin]
        with open(origin, "r") as f:
            try:
                root = ast.parse(f.read(), os.path.split(origin)[-1])
            except Exception as e:
                raise ParseError("error parsing %s" % origin, e)
            self.module_asts[origin] = root
            return root

    def find_module(
        self,
        module_name: str,
        parent_module_paths: typing.Union[typing.List[str], None] = None,
    ) -> typing.Union[object, None]:
        spec = self.find_spec(module_name, parent_module_paths)
        if spec is None or spec.origin is None or spec.origin.endswith(".pyc"):
            return None
        if spec.origin in self.module_nodes:
            return self.module_nodes[spec.origin]
        mod = self.parse_ast(spec.origin)
        if os.path.split(spec.origin)[-1] == "__init__.py":
            node = Package.from_spec(self, spec, mod)
            self.module_nodes[spec.origin] = node
            self.populate_module_scope(node.modules["__init__"])
        else:
            node = Module(mod, spec)
            self.module_nodes[spec.origin] = node
            self.populate_module_scope(node)
        return node

    def populate_module_scope(self, mod: Module):
        if mod.loaded:
            return
        mod.loaded = True
        stack = Stack()
        for stmt in mod.ast.body:
            self.populate_scope(mod.spec, stack, mod.ast, stmt)
        mod.children = stack.current_scope()

    def populate_scope(
        self,
        spec: ModuleSpec,
        stack: Stack,
        parent_node: ast.AST,
        stmt: ast.stmt,
    ):
        if isinstance(stmt, ast.Import):
            for alias in stmt.names:
                node = self.find_module(alias.name, spec.submodule_search_locations)
                if node is not None:
                    stack.store(
                        alias.name if alias.asname is None else alias.asname, node
                    )
        elif isinstance(stmt, ast.ImportFrom):
            if stmt.module is None:
                level = stmt.level
                package_path = spec.origin
                while level > 0:
                    package_path = os.path.dirname(package_path)
                    level -= 1
                parent, package_name = os.path.split(package_path)
                node = self.find_module(package_name, [parent])
            else:
                node = self.find_module(stmt.module, spec.submodule_search_locations)
            if node is not None:
                for alias in stmt.names:
                    value = Stack([node]).get_value(alias.name)
                    if value is not None:
                        stack.store(
                            alias.name if alias.asname is None else alias.asname,
                            value,
                        )
        elif isinstance(stmt, ast.FunctionDef) or isinstance(
            stmt, ast.AsyncFunctionDef
        ):
            # ignore instance methods
            if isinstance(parent_node, ast.ClassDef):
                instmed = True
                for name in stmt.decorator_list:
                    if name.id in ["classmethod", "staticmethod"]:
                        instmed = False
                        break
                if instmed:
                    return
            stack.store(stmt.name, Node(stmt, spec))
        elif isinstance(stmt, ast.ClassDef):
            if hasattr(stmt, "body"):
                substack = stack.push()
                for cd_stmt in stmt.body:
                    self.populate_scope(spec, substack, stmt, cd_stmt)
                children = substack.current_scope()
            else:
                children = None
            value = Node(stmt, spec, children)
            stack.store(stmt.name, value)
        elif isinstance(stmt, ast.Assign):
            node = self.dereference(spec, stack, stmt.value)
            if node is None:
                return
            for tgt in stmt.targets:
                if isinstance(tgt, ast.Tuple):
                    if isinstance(node.ast, ast.Tuple):
                        for idx, el in enumerate(tgt.elts):
                            if isinstance(el, ast.Name):
                                stack.store(el.id, Node(node.ast.elts[idx], spec))
                elif isinstance(tgt, ast.Name):
                    stack.store(tgt.id, Node(node.ast, spec))

    def dereference(
        self, spec: ModuleSpec, stack: Stack, node: ast.AST
    ) -> typing.Union[Node, None]:
        if isinstance(node, ast.Constant):
            return Node(node, spec)
        elif isinstance(node, ast.Tuple):
            for idx, el in enumerate(node.elts):
                child = self.dereference(spec, stack, el)
                if child is None:
                    return None
                node.elts[idx] = child.ast
            return Node(node, spec)
        else:
            return stack.dereference(node)
