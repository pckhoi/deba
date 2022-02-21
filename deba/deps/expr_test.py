from importlib.machinery import ModuleSpec, SourceFileLoader
from unittest import TestCase
import re
import typing
import ast

from attrs import define
from deba.deps.expr import ExprPattern, ExprTemplateParseError
from deba.deps.module import Node, Stack
from deba.test_utils import ASTMixin


class ExprTemplateTestCase(ASTMixin, TestCase):
    def test_from_str(self):
        with self.assertRaises(ExprTemplateParseError) as cm:
            ExprPattern.from_str("`abc*")
        self.assertEqual(
            cm.exception.args, ("backtick pattern not closed at line 1, offset 1",)
        )

        with self.assertRaises(ExprTemplateParseError) as cm:
            ExprPattern.from_str("abc\n123")
        self.assertEqual(cm.exception.args, ("expect exactly 1 expression, found 2",))

        for s in ["abc('d', 'e')", "abc()", "abc(de=123, qw='asd')"]:
            with self.assertRaises(ExprTemplateParseError) as cm:
                ExprPattern.from_str(s)
            self.assertEqual(
                cm.exception.args,
                (
                    "function call must have exactly one argument or one keyword argument",
                ),
            )

        with self.assertRaises(ExprTemplateParseError) as cm:
            ExprPattern.from_str(r"r'*'")
        self.assertTrue("expression must be a function call" in cm.exception.args[0])

        with self.assertRaises(ExprTemplateParseError) as cm:
            ExprPattern.from_str(r"to_csv(r'*')")
        self.assertEqual(
            cm.exception.args,
            ("invalid regular expression r'*': nothing to repeat at position 0",),
        )

        with self.assertRaises(SyntaxError):
            ExprPattern.from_str(r"@@")

        @define
        class Case:
            s: str
            expr: ast.AST
            file_pat: object
            patterns: typing.List[str]

        for case in [
            Case(
                r"load_csv('.+\\.csv')",
                ast.Call(
                    ast.Name("load_csv", ctx=ast.Load()),
                    args=[ast.Constant(r".+\.csv")],
                    keywords=[],
                ),
                re.compile(r"^.+\.csv$"),
                [],
            ),
            Case(
                r'`*`.to_csv("\\w+\\.csv")',
                ast.Call(
                    ast.Attribute(
                        ast.Name(
                            "deba_backtick_pat_000",
                            ctx=ast.Load(),
                        ),
                        attr="to_csv",
                        ctx=ast.Load(),
                    ),
                    args=[ast.Constant(r"\w+\.csv")],
                    keywords=[],
                ),
                re.compile(r"^\w+\.csv$"),
                ["*"],
            ),
        ]:
            et = ExprPattern.from_str(case.s)
            self.assertASTEqual(et.node, case.expr)
            self.assertEqual(et.file_pat, case.file_pat, repr(case))
            self.assertEqual(et.patterns, case.patterns, repr(case))

    def test_match_node(self):
        @define
        class Case:
            template: str
            source: str
            file: typing.Union[None, str]

        for idx, case in enumerate(
            [
                Case(r"read_csv(r'.+\.csv')", "read_csv('abc.csv')", "abc.csv"),
                Case(r"read_csv(r'.+\.csv')", "read_csv('abc.csvl')", None),
                Case(r"read_csv(r'.+\.csv')", "read_csv('abc.det')", None),
                Case(r"`*`.to_csv(r'.+\.csv')", "df.to_csv('abc.csv')", "abc.csv"),
                Case(
                    r"`*`.to_csv(r'.+\.csv')",
                    "df.to_csv('abc.csv', index=False)",
                    "abc.csv",
                ),
                Case(r"`*`.to_csv(r'.+\.csv')", "to_csv('abc.csv')", None),
                Case(r"`*`.to_csv(r'.+\.csv')", "df.load('abc.csv')", None),
                Case(r"`*`.to_csv(r'.+\.csv')", "df.to_csv('abc.cst')", None),
                Case(r"`save_*`(r'.+\.csv')", "save_user('abc.csv')", "abc.csv"),
                Case(r"`save_*`(r'.+\.csv')", "load_user('abc.csv')", None),
                Case(r"`save_*`(r'.+\.csv')", "save_user('abc.dsv')", None),
                Case(
                    r"`do_*`(`does_*`(kw=r'.+\.pdf'))",
                    "do_abc(123, does_xyz('abc', kw='qwe.pdf'))",
                    "qwe.pdf",
                ),
            ]
        ):
            et = ExprPattern.from_str(case.template)
            node = ast.parse(case.source).body[0].value
            self.assertEqual(
                et.match_node(Stack(), node),
                case.file,
                "(case %d) %s" % (idx, repr(case)),
            )

    def test_match_node_with_scopes(self):
        spec = ModuleSpec("a", loader=SourceFileLoader("a", "a"))
        scopes = Stack(
            [
                {
                    "a": Node(ast.Constant(value="file_a.csv"), spec),
                    "MyClass": Node(
                        ast.ClassDef(
                            name="MyClass",
                            bases=[],
                            keywords=[],
                            body=[
                                ast.Assign(
                                    targets=[ast.Name(id="b", ctx=ast.Store())],
                                    value=ast.Constant(value="file_b.csv"),
                                ),
                                ast.Assign(
                                    targets=[ast.Name(id="c", ctx=ast.Store())],
                                    value=ast.Constant(value="file_c.pdf"),
                                ),
                            ],
                        ),
                        spec,
                        children={
                            "b": Node(
                                ast.Constant(value="file_b.csv"),
                                spec,
                            ),
                            "c": Node(
                                ast.Constant(value="file_c.pdf"),
                                spec,
                            ),
                        },
                    ),
                }
            ]
        )

        @define
        class Case:
            template: str
            source: str
            file: typing.Union[None, str]

        for idx, case in enumerate(
            [
                Case(r"read_csv(r'.+\.csv')", "read_csv(a)", "file_a.csv"),
                Case(r"read_csv(r'.+\.csv')", "read_csv(d)", None),
                Case(r"read_csv(r'.+\.csv')", "read_csv(MyClass.b)", "file_b.csv"),
                Case(r"read_csv(r'.+\.csv')", "read_csv(MyClass.c)", None),
            ]
        ):
            et = ExprPattern.from_str(case.template)
            node = ast.parse(case.source).body[0].value
            self.assertEqual(
                et.match_node(scopes, node),
                case.file,
                "(case %d) %s" % (idx, repr(case)),
            )
