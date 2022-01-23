import typing
import os
import tempfile
import ast

from dirk.modules import Node, NodeFactory
from dirk.test_utils import ASTTestCase


class NodeTestCase(ASTTestCase):
    def test_get_descendant(self):
        const_ast = ast.Constant(value=3)
        classdef_ast = ast.ClassDef(
            "ABC",
            body=[
                ast.Assign(
                    targets=[ast.Name("a", ctx=ast.Store())],
                    value=const_ast,
                )
            ],
        )
        module_ast = ast.Module([classdef_ast])
        node = Node(
            module_ast,
            children={"ABC": Node(classdef_ast, children={"a": Node(const_ast)})},
        )
        self.assertEqual(
            node.get_descendant("ABC"),
            Node(classdef_ast, children={"a": Node(const_ast)}),
        )
        self.assertEqual(node.get_descendant("ABC.a"), Node(const_ast))
        self.assertIsNone(node.get_descendant("non_existent"))
        self.assertIsNone(node.get_descendant("ABC.non_existent"))


class NodeFactoryTestCase(ASTTestCase):
    def setUp(self):
        super().setUp()
        self.maxDiff = None
        self._dir = tempfile.TemporaryDirectory()

    def tearDown(self) -> None:
        self._dir.cleanup()
        return super().tearDown()

    def file_path(self, filename: str) -> str:
        return os.path.join(self._dir.name, filename)

    def write_file(self, filename: str, lines: typing.List[str]):
        os.makedirs(os.path.dirname(self.file_path(filename)), exist_ok=True)
        with open(self.file_path(filename), "w") as f:
            f.write("\n".join(lines))

    def assertNodeEqual(self, a: typing.Union[Node, None], b: typing.Union[Node, None]):
        if a is None or b is None:
            self.assertEqual(a, b)
        else:
            self.assertASTEqual(a.t, b.t)
            if b.children is None:
                self.assertIsNone(a.children)
            else:
                for k in b.children:
                    if k not in a.children:
                        raise AssertionError("%s not found in %s" % (k, a.children))
                for k, v in a.children.items():
                    if k not in b.children:
                        raise AssertionError("%s not found in %s" % (k, b.children))
                    self.assertNodeEqual(v, b.children[k])

    def test_find_module(self):
        factory = NodeFactory([self._dir.name])
        self.write_file("a.py", ["a = 1"])
        self.write_file("b/__init__.py", [""])
        self.write_file("b/c.py", ["b = r'abc'"])

        spec = factory.find_module("a")
        self.assertIsNotNone(spec)
        self.assertEqual(spec.origin, self.file_path("a.py"))

        spec = factory.find_module("b")
        self.assertIsNotNone(spec)
        self.assertEqual(spec.origin, self.file_path("b/__init__.py"))

        self.assertIsNone(factory.find_module("c"))

        spec = factory.find_module("c", spec.submodule_search_locations)
        self.assertIsNotNone(spec)
        self.assertEqual(spec.origin, self.file_path("b/c.py"))

        spec = factory.find_module("b.c")
        self.assertIsNotNone(spec)
        self.assertEqual(spec.origin, self.file_path("b/c.py"))

        self.assertIsNone(factory.find_module("b.d"))

    def test_parse_module_spec(self):
        factory = NodeFactory([self._dir.name])
        self.write_file("a.py", ["a = 1"])
        mod = factory.parse_module(self.file_path("a.py"))
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
        self.assertASTEqual(factory.parse_module(self.file_path("a.py")), mod)

    def test_build_module(self):
        factory = NodeFactory([self._dir.name])
        self.write_file("a.py", ["a = 1"])
        self.write_file("b/__init__.py", ["b = r'b'"])
        self.write_file("b/c.py", ["b = r'abc'"])
        self.write_file("b/d/__init__.py", ["d = r'd'"])
        self.write_file("b/d/e.py", ["e = 2"])

        node_a = factory.build_module("a")
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
                {"a": Node(ast.Constant(value=1))},
            ),
        )

        node_b = factory.build_module("b")
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
                {
                    "b": Node(ast.Constant(value="b")),
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
                        {"b": Node(ast.Constant(value="abc"))},
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
                        {
                            "d": Node(ast.Constant(value="d")),
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
                                {"e": Node(ast.Constant(value=2))},
                            ),
                        },
                    ),
                },
            ),
        )

    def test_build_from_ast(self):
        factory = NodeFactory([self._dir.name])
        self.write_file("a.py", ["my_a = 1"])
        self.write_file("b.py", ["my_b = 2"])
        self.write_file("c.py", ["import d as d_dash"])
        self.write_file("d.py", ["my_d = r'abc'"])
        self.write_file(
            "z.py",
            [
                "import a",
                "from b import my_b",
                "from c import d_dash as d_dash_dash",
                "",
                "def my_func():",
                "  pass",
                "",
                "class MyClass:",
                "  a = 'b'",
                "  c = a",
                "  d = my_b",
                "",
                "  def c(self):",
                "    pass",
                "",
                "  @classmethod",
                "  def d(cls):",
                "    pass",
                "",
                "  @staticmethod",
                "  def e():",
                "    pass",
                "",
                "var1 = MyClass.a",
                "var2 = var1",
                "e, f = 123, 'def'",
            ],
        )

        self.assertNodeEqual(
            factory.build_module_from_filepath(self.file_path("z.py")),
            Node(
                ast.Module(
                    body=[
                        ast.Import(names=[ast.alias(name="a")]),
                        ast.ImportFrom(
                            module="b", names=[ast.alias(name="my_b")], level=0
                        ),
                        ast.ImportFrom(
                            module="c",
                            names=[ast.alias(name="d_dash", asname="d_dash_dash")],
                            level=0,
                        ),
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
                                    name="c",
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
                                    name="d",
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
                {
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
                        {"my_a": Node(ast.Constant(value=1))},
                    ),
                    "my_b": Node(ast.Constant(value=2)),
                    "d_dash_dash": Node(
                        ast.Module(
                            [
                                ast.Assign(
                                    targets=[ast.Name(id="my_d", ctx=ast.Store())],
                                    value=ast.Constant(value="abc"),
                                )
                            ],
                            type_ignores=[],
                        ),
                        {"my_d": Node(ast.Constant(value="abc"))},
                    ),
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
                    ),
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
                                    name="c",
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
                                    name="d",
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
                        {
                            "a": Node(ast.Constant(value="b")),
                            "c": Node(ast.Constant(value="b")),
                            "d": Node(ast.Constant(value=2)),
                            "d": Node(
                                ast.FunctionDef(
                                    name="d",
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
                                )
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
                                )
                            ),
                        },
                    ),
                    "var1": Node(ast.Constant(value="b")),
                    "var2": Node(ast.Constant(value="b")),
                    "e": Node(ast.Constant(value=123)),
                    "f": Node(ast.Constant(value="def")),
                },
            ),
        )
        # TODO: add tests for func, async func, class def, assignment
