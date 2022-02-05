from importlib.machinery import PathFinder
import typing
from unittest import TestCase
import os
import tempfile
import ast
from dirk.deps.expr import ExprPattern

from dirk.deps.finder import Node, DepsFinder, trim_suffix
from dirk.test_utils import ASTMixin, TempDirMixin


class DepsFinderTestCase(ASTMixin, TempDirMixin, TestCase):
    def assertNodeEqual(
        self,
        a: typing.Union[Node, None],
        b: typing.Union[Node, None],
        msg: typing.Union[str, None] = None,
    ):
        if a is None or b is None:
            self.assertEqual(a, b, msg)
        else:
            self.assertASTEqual(a.t, b.t)
            if b.spec is None:
                print("a:", ast.dump(a.t), a.spec)
                print("b:", ast.dump(b.t), b.spec)
            self.assertEqual(a.spec, b.spec, msg)
            if b.children is None:
                self.assertIsNone(a.children, msg)
            else:
                for k in b.children:
                    if k not in a.children:
                        raise AssertionError(
                            "%s: %s not found in %s" % (k, b.children[k], a.children)
                        )
                for k, v in a.children.items():
                    if k not in b.children:
                        raise AssertionError(
                            "%s: %s not found in %s" % (k, v, b.children)
                        )
                    self.assertNodeEqual(v, b.children[k], msg)

    def test_find_module(self):
        finder = DepsFinder([self._dir.name])
        self.write_file("a.py", ["a = 1"])
        self.write_file("b/__init__.py", [""])
        self.write_file("b/c.py", ["b = r'abc'"])

        spec = finder.find_module("a")
        self.assertIsNotNone(spec)
        self.assertEqual(spec.origin, self.file_path("a.py"))

        spec = finder.find_module("b")
        self.assertIsNotNone(spec)
        self.assertEqual(spec.origin, self.file_path("b/__init__.py"))

        self.assertIsNone(finder.find_module("c"))

        spec = finder.find_module("c", spec.submodule_search_locations)
        self.assertIsNotNone(spec)
        self.assertEqual(spec.origin, self.file_path("b/c.py"))

        spec = finder.find_module("b.c")
        self.assertIsNotNone(spec)
        self.assertEqual(spec.origin, self.file_path("b/c.py"))

        self.assertIsNone(finder.find_module("b.d"))

    def test_parse_module_spec(self):
        finder = DepsFinder([self._dir.name])
        self.write_file("a.py", ["a = 1"])
        mod = finder.parse_module(self.file_path("a.py"))
        self.assertASTEqual(
            mod,
            ast.Module(
                [
                    ast.Assign(
                        targets=[ast.Name(id="a", ctx=ast.Store())],
                        value=ast.Constant(value=1),
                    )
                ],
                type_ignores=[],
            ),
        )

        os.remove(self.file_path("a.py"))
        # returns from cache
        self.assertASTEqual(finder.parse_module(self.file_path("a.py")), mod)

    def spec(self, s: str):
        path, name = os.path.split(self.file_path(s))
        return PathFinder.find_spec(trim_suffix(name, ".py"), [path])

    def test_build_module(self):
        finder = DepsFinder([self._dir.name])
        self.write_file("a.py", ["a = 1"])
        self.write_file("b/__init__.py", ["b = r'b'"])
        self.write_file("b/c.py", ["b = r'abc'"])
        self.write_file("b/d/__init__.py", ["d = r'd'"])
        self.write_file("b/d/e.py", ["e = 2"])

        node_a = finder.build_module("a")
        self.assertNodeEqual(
            node_a,
            Node(
                ast.Module(
                    [
                        ast.Assign(
                            targets=[ast.Name(id="a", ctx=ast.Store())],
                            value=ast.Constant(value=1),
                        )
                    ],
                    type_ignores=[],
                ),
                spec=self.spec("a.py"),
                children={"a": Node(ast.Constant(value=1), self.spec("a.py"))},
            ),
        )

        node_b = finder.build_module("b")
        self.assertEqual(node_b.spec.origin, self.file_path("b/__init__.py"))
        self.assertNodeEqual(
            node_b,
            Node(
                ast.Module(
                    [
                        ast.Assign(
                            targets=[ast.Name(id="b", ctx=ast.Store())],
                            value=ast.Constant(value="b"),
                        )
                    ],
                    type_ignores=[],
                ),
                self.spec("b"),
                children={
                    "b": Node(
                        ast.Constant(value="b"),
                        self.spec("b"),
                    ),
                    "c": Node(
                        ast.Module(
                            [
                                ast.Assign(
                                    targets=[ast.Name(id="b", ctx=ast.Store())],
                                    value=ast.Constant(value="abc"),
                                )
                            ],
                            type_ignores=[],
                        ),
                        self.spec("b/c.py"),
                        children={
                            "b": Node(ast.Constant(value="abc"), self.spec("b/c.py"))
                        },
                    ),
                    "d": Node(
                        ast.Module(
                            [
                                ast.Assign(
                                    targets=[ast.Name(id="d", ctx=ast.Store())],
                                    value=ast.Constant(value="d"),
                                )
                            ],
                            type_ignores=[],
                        ),
                        self.spec("b/d"),
                        children={
                            "d": Node(
                                ast.Constant(value="d"),
                                self.spec("b/d"),
                            ),
                            "e": Node(
                                ast.Module(
                                    [
                                        ast.Assign(
                                            targets=[ast.Name(id="e", ctx=ast.Store())],
                                            value=ast.Constant(value=2),
                                        )
                                    ],
                                    type_ignores=[],
                                ),
                                self.spec("b/d/e.py"),
                                children={
                                    "e": Node(
                                        ast.Constant(value=2),
                                        self.spec("b/d/e.py"),
                                    )
                                },
                            ),
                        },
                    ),
                },
            ),
        )

    def test_import_package(self):
        finder = DepsFinder([self._dir.name])
        self.write_file("a.py", ["my_a = 1"])
        self.write_file("b.py", ["import a"])
        self.assertNodeEqual(
            finder.build_module_from_filepath(self.file_path("b.py")),
            Node(
                ast.Module(
                    body=[ast.Import(names=[ast.alias(name="a")])],
                    type_ignores=[],
                ),
                self.spec("b"),
                children={
                    "a": Node(
                        ast.Module(
                            [
                                ast.Assign(
                                    targets=[ast.Name(id="my_a", ctx=ast.Store())],
                                    value=ast.Constant(value=1),
                                )
                            ],
                            type_ignores=[],
                        ),
                        self.spec("a"),
                        children={"my_a": Node(ast.Constant(value=1), self.spec("a"))},
                    )
                },
            ),
        )

    def test_import_from(self):
        finder = DepsFinder([self._dir.name])
        self.write_file("a.py", ["my_a = 1"])
        self.write_file("b.py", ["from a import my_a"])
        self.assertNodeEqual(
            finder.build_module_from_filepath(self.file_path("b.py")),
            Node(
                ast.Module(
                    body=[
                        ast.ImportFrom(
                            module="a", names=[ast.alias(name="my_a")], level=0
                        ),
                    ],
                    type_ignores=[],
                ),
                self.spec("b"),
                children={"my_a": Node(ast.Constant(value=1), self.spec("a"))},
            ),
        )

    def test_import_as(self):
        finder = DepsFinder([self._dir.name])
        self.write_file("a.py", ["my_a = 1"])
        self.write_file("b.py", ["import a as a_dash"])
        self.assertNodeEqual(
            finder.build_module_from_filepath(self.file_path("b.py")),
            Node(
                ast.Module(
                    body=[ast.Import(names=[ast.alias(name="a", asname="a_dash")])],
                    type_ignores=[],
                ),
                self.spec("b"),
                children={
                    "a_dash": Node(
                        ast.Module(
                            [
                                ast.Assign(
                                    targets=[ast.Name(id="my_a", ctx=ast.Store())],
                                    value=ast.Constant(value=1),
                                )
                            ],
                            type_ignores=[],
                        ),
                        self.spec("a"),
                        children={"my_a": Node(ast.Constant(value=1), self.spec("a"))},
                    )
                },
            ),
        )

    def test_import_from_as(self):
        finder = DepsFinder([self._dir.name])
        self.write_file("a.py", ["my_a = 1"])
        self.write_file("b.py", ["from a import my_a as my_b"])
        self.assertNodeEqual(
            finder.build_module_from_filepath(self.file_path("b.py")),
            Node(
                ast.Module(
                    body=[
                        ast.ImportFrom(
                            module="a",
                            names=[ast.alias(name="my_a", asname="my_b")],
                            level=0,
                        ),
                    ],
                    type_ignores=[],
                ),
                self.spec("b"),
                children={"my_b": Node(ast.Constant(value=1), self.spec("a"))},
            ),
        )

    def test_func_def(self):
        self.write_file(
            "a.py",
            [
                "def my_func():",
                "  pass",
                "",
            ],
        )
        self.assertNodeEqual(
            DepsFinder([self._dir.name]).build_module_from_filepath(
                self.file_path("a.py")
            ),
            Node(
                ast.Module(
                    body=[
                        ast.FunctionDef(
                            name="my_func",
                            args=ast.arguments(
                                posonlyargs=[],
                                args=[],
                                kwonlyargs=[],
                                kw_defaults=[],
                                defaults=[],
                            ),
                            body=[ast.Pass()],
                            decorator_list=[],
                        ),
                    ],
                    type_ignores=[],
                ),
                self.spec("a"),
                children={
                    "my_func": Node(
                        ast.FunctionDef(
                            name="my_func",
                            args=ast.arguments(
                                posonlyargs=[],
                                args=[],
                                kwonlyargs=[],
                                kw_defaults=[],
                                defaults=[],
                            ),
                            body=[ast.Pass()],
                            decorator_list=[],
                        ),
                        self.spec("a"),
                    )
                },
            ),
        )

    def test_class_def(self):
        self.write_file(
            "a.py",
            [
                "class MyClass:",
                "  a = 'b'",
                "  c = a",
                "  d = my_b",
                "",
                "  def f(self):",
                "    pass",
                "",
                "  @classmethod",
                "  def g(cls):",
                "    pass",
                "",
                "  @staticmethod",
                "  def e():",
                "    pass",
                "",
            ],
        )
        self.assertNodeEqual(
            DepsFinder([self._dir.name]).build_module_from_filepath(
                self.file_path("a.py")
            ),
            Node(
                ast.Module(
                    body=[
                        ast.ClassDef(
                            name="MyClass",
                            bases=[],
                            keywords=[],
                            body=[
                                ast.Assign(
                                    targets=[ast.Name(id="a", ctx=ast.Store())],
                                    value=ast.Constant(value="b"),
                                ),
                                ast.Assign(
                                    targets=[ast.Name(id="c", ctx=ast.Store())],
                                    value=ast.Name(id="a", ctx=ast.Load()),
                                ),
                                ast.Assign(
                                    targets=[ast.Name(id="d", ctx=ast.Store())],
                                    value=ast.Name(id="my_b", ctx=ast.Load()),
                                ),
                                ast.FunctionDef(
                                    name="f",
                                    args=ast.arguments(
                                        posonlyargs=[],
                                        args=[ast.arg(arg="self")],
                                        kwonlyargs=[],
                                        kw_defaults=[],
                                        defaults=[],
                                    ),
                                    body=[ast.Pass()],
                                    decorator_list=[],
                                ),
                                ast.FunctionDef(
                                    name="g",
                                    args=ast.arguments(
                                        posonlyargs=[],
                                        args=[ast.arg(arg="cls")],
                                        kwonlyargs=[],
                                        kw_defaults=[],
                                        defaults=[],
                                    ),
                                    body=[ast.Pass()],
                                    decorator_list=[
                                        ast.Name(id="classmethod", ctx=ast.Load())
                                    ],
                                ),
                                ast.FunctionDef(
                                    name="e",
                                    args=ast.arguments(
                                        posonlyargs=[],
                                        args=[],
                                        kwonlyargs=[],
                                        kw_defaults=[],
                                        defaults=[],
                                    ),
                                    body=[ast.Pass()],
                                    decorator_list=[
                                        ast.Name(id="staticmethod", ctx=ast.Load())
                                    ],
                                ),
                            ],
                            decorator_list=[],
                        ),
                    ],
                    type_ignores=[],
                ),
                self.spec("a"),
                children={
                    "MyClass": Node(
                        ast.ClassDef(
                            name="MyClass",
                            bases=[],
                            keywords=[],
                            body=[
                                ast.Assign(
                                    targets=[ast.Name(id="a", ctx=ast.Store())],
                                    value=ast.Constant(value="b"),
                                ),
                                ast.Assign(
                                    targets=[ast.Name(id="c", ctx=ast.Store())],
                                    value=ast.Name(id="a", ctx=ast.Load()),
                                ),
                                ast.Assign(
                                    targets=[ast.Name(id="d", ctx=ast.Store())],
                                    value=ast.Name(id="my_b", ctx=ast.Load()),
                                ),
                                ast.FunctionDef(
                                    name="f",
                                    args=ast.arguments(
                                        posonlyargs=[],
                                        args=[ast.arg(arg="self")],
                                        kwonlyargs=[],
                                        kw_defaults=[],
                                        defaults=[],
                                    ),
                                    body=[ast.Pass()],
                                    decorator_list=[],
                                ),
                                ast.FunctionDef(
                                    name="g",
                                    args=ast.arguments(
                                        posonlyargs=[],
                                        args=[ast.arg(arg="cls")],
                                        kwonlyargs=[],
                                        kw_defaults=[],
                                        defaults=[],
                                    ),
                                    body=[ast.Pass()],
                                    decorator_list=[
                                        ast.Name(id="classmethod", ctx=ast.Load())
                                    ],
                                ),
                                ast.FunctionDef(
                                    name="e",
                                    args=ast.arguments(
                                        posonlyargs=[],
                                        args=[],
                                        kwonlyargs=[],
                                        kw_defaults=[],
                                        defaults=[],
                                    ),
                                    body=[ast.Pass()],
                                    decorator_list=[
                                        ast.Name(id="staticmethod", ctx=ast.Load())
                                    ],
                                ),
                            ],
                            decorator_list=[],
                        ),
                        self.spec("a"),
                        children={
                            "a": Node(ast.Constant(value="b"), self.spec("a")),
                            "c": Node(ast.Constant(value="b"), self.spec("a")),
                            "g": Node(
                                ast.FunctionDef(
                                    name="g",
                                    args=ast.arguments(
                                        posonlyargs=[],
                                        args=[ast.arg(arg="cls")],
                                        kwonlyargs=[],
                                        kw_defaults=[],
                                        defaults=[],
                                    ),
                                    body=[ast.Pass()],
                                    decorator_list=[
                                        ast.Name(id="classmethod", ctx=ast.Load())
                                    ],
                                ),
                                self.spec("a"),
                            ),
                            "e": Node(
                                ast.FunctionDef(
                                    name="e",
                                    args=ast.arguments(
                                        posonlyargs=[],
                                        args=[],
                                        kwonlyargs=[],
                                        kw_defaults=[],
                                        defaults=[],
                                    ),
                                    body=[ast.Pass()],
                                    decorator_list=[
                                        ast.Name(id="staticmethod", ctx=ast.Load())
                                    ],
                                ),
                                self.spec("a"),
                            ),
                        },
                    )
                },
            ),
        )

    def test_assignment(self):
        self.write_file(
            "a.py",
            [
                "class MyClass:",
                "  a = 'b'",
                "",
                "var1 = MyClass.a",
                "var2 = var1",
                "e, f = 123, 'def'",
            ],
        )
        self.assertNodeEqual(
            DepsFinder([self._dir.name]).build_module_from_filepath(
                self.file_path("a.py")
            ),
            Node(
                ast.Module(
                    body=[
                        ast.ClassDef(
                            name="MyClass",
                            bases=[],
                            keywords=[],
                            body=[
                                ast.Assign(
                                    targets=[ast.Name(id="a", ctx=ast.Store())],
                                    value=ast.Constant(value="b"),
                                )
                            ],
                            decorator_list=[],
                        ),
                        ast.Assign(
                            targets=[ast.Name(id="var1", ctx=ast.Store())],
                            value=ast.Attribute(
                                value=ast.Name(id="MyClass", ctx=ast.Load()),
                                attr="a",
                                ctx=ast.Load(),
                            ),
                        ),
                        ast.Assign(
                            targets=[ast.Name(id="var2", ctx=ast.Store())],
                            value=ast.Name(id="var1", ctx=ast.Load()),
                        ),
                        ast.Assign(
                            targets=[
                                ast.Tuple(
                                    elts=[
                                        ast.Name(id="e", ctx=ast.Store()),
                                        ast.Name(id="f", ctx=ast.Store()),
                                    ],
                                    ctx=ast.Store(),
                                )
                            ],
                            value=ast.Tuple(
                                elts=[
                                    ast.Constant(value=123),
                                    ast.Constant(value="def"),
                                ],
                                ctx=ast.Load(),
                            ),
                        ),
                    ],
                    type_ignores=[],
                ),
                self.spec("a"),
                children={
                    "MyClass": Node(
                        ast.ClassDef(
                            name="MyClass",
                            bases=[],
                            keywords=[],
                            body=[
                                ast.Assign(
                                    targets=[ast.Name(id="a", ctx=ast.Store())],
                                    value=ast.Constant(value="b"),
                                )
                            ],
                            decorator_list=[],
                        ),
                        self.spec("a"),
                        children={"a": Node(ast.Constant(value="b"), self.spec("a"))},
                    ),
                    "var1": Node(ast.Constant(value="b"), self.spec("a")),
                    "var2": Node(ast.Constant(value="b"), self.spec("a")),
                    "e": Node(ast.Constant(value=123), self.spec("a")),
                    "f": Node(ast.Constant(value="def"), self.spec("a")),
                },
            ),
        )

    def test_find_dependencies(self):
        finder = DepsFinder([self._dir.name])
        self.write_file(
            "b.py",
            [
                "class MyClass:",
                "  @classmethod",
                "  def save_file(cls, a):",
                "    a.to_csv('asd.csv')",
                "",
            ],
        )
        self.write_file(
            "a.py",
            [
                "import b",
                "",
                "b_name = 'file_b.csv'",
                "",
                "def my_func():",
                "  return read_csv('qwe.csv')",
                "",
                "if __name__ == '__main__':",
                "  a = read_csv('abc.csv')",
                "  b = read_csv(b_name)",
                "  d = my_func()",
                "",
                "  a.to_csv('def.csv')",
                "  c_name = 'file_c.csv'",
                "  b.to_csv(c_name)",
                "  b.MyClass.save_file(d)",
            ],
        )
        ins, outs = finder.find_dependencies(
            self.file_path("a.py"),
            [ExprPattern.from_str(r'read_csv(r"\w+\.csv")')],
            [ExprPattern.from_str(r'`*`.to_csv(r"\w+\.csv")')],
        )
        self.assertEqual(ins, ["abc.csv", "file_b.csv", "qwe.csv"])
        self.assertEqual(outs, ["def.csv", "file_c.csv", "asd.csv"])
