import re
import typing
import unittest
import ast

from attrs import define
from dirk.expr import ExprTemplate, ExprTemplateParseError


class ExprTemplateTestCase(unittest.TestCase):
    def assertASTEqual(self, a: ast.Expr, b: ast.Expr):
        self.assertEqual(ast.dump(a, indent=4), ast.dump(b, indent=4))

    def test_from_str(self):
        with self.assertRaises(ExprTemplateParseError) as cm:
            ExprTemplate.from_str("`abc*")
        self.assertEqual(
            cm.exception.args, ("backtick pattern not closed at line 1, offset 1",)
        )

        with self.assertRaises(ExprTemplateParseError) as cm:
            ExprTemplate.from_str("abc\n123")
        self.assertEqual(cm.exception.args, ("expect exactly 1 expression, found 2",))

        with self.assertRaises(ExprTemplateParseError) as cm:
            ExprTemplate.from_str("abc('d', 'e')")
        self.assertEqual(
            cm.exception.args,
            ("expect exactly 1 string in expression template, found 2",),
        )

        with self.assertRaises(ExprTemplateParseError) as cm:
            ExprTemplate.from_str(r"r'*'")
        self.assertEqual(
            cm.exception.args,
            ("invalid regular expression r'*': nothing to repeat at position 0",),
        )

        with self.assertRaises(SyntaxError):
            ExprTemplate.from_str(r"@@")

        @define
        class Case:
            s: str
            expr: ast.AST
            file_pat: re.Pattern
            patterns: typing.List[str]

        for case in [
            Case(
                r"r'.+\.csv'",
                ast.Constant(r".+\.csv"),
                re.compile(r"^.+\.csv$"),
                [],
            ),
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
                            "dirk_backtick_pat_000",
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
            et = ExprTemplate.from_str(case.s)
            self.assertASTEqual(et.node, case.expr)
            self.assertEqual(et.file_pat, case.file_pat, repr(case))
            self.assertEqual(et.patterns, case.patterns, repr(case))

    def test_match_node(self):
        @define
        class Case:
            template: str
            source: str
            file: typing.Union[None, str]

        for case in [
            Case(r"r'.+\.csv'", "'abc.csv'", "abc.csv"),
            Case(r"r'.+\.csv'", "'abc.csvl'", None),
            Case(r"r'.+\.csv'", "'abc.det'", None),
            Case(r"`*`.to_csv(r'.+\.csv')", "df.to_csv('abc.csv')", "abc.csv"),
            Case(r"`*`.to_csv(r'.+\.csv')", "to_csv('abc.csv')", None),
            Case(r"`*`.to_csv(r'.+\.csv')", "df.load('abc.csv')", None),
            Case(r"`*`.to_csv(r'.+\.csv')", "df.to_csv('abc.cst')", None),
            Case(r"`save_*`(r'.+\.csv')", "save_user('abc.csv')", "abc.csv"),
            Case(r"`save_*`(r'.+\.csv')", "load_user('abc.csv')", None),
            Case(r"`save_*`(r'.+\.csv')", "save_user('abc.dsv')", None),
        ]:
            et = ExprTemplate.from_str(case.template)
            node = ast.parse(case.source).body[0].value
            self.assertEqual(et.match_expr(node), case.file, repr(case))
