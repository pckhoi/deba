import re
import typing
import ast

from attrs import define
from dirk.expr import ExprTemplate, ExprTemplateParseError
from dirk.test_utils import ASTTestCase


class ExprTemplateTestCase(ASTTestCase):
    def test_from_str(self):
        with self.assertRaises(ExprTemplateParseError) as cm:
            ExprTemplate.from_str("`abc*")
        self.assertEqual(
            cm.exception.args, ("backtick pattern not closed at line 1, offset 1",)
        )

        with self.assertRaises(ExprTemplateParseError) as cm:
            ExprTemplate.from_str("abc\n123")
        self.assertEqual(cm.exception.args, ("expect exactly 1 expression, found 2",))

        for s in ["abc('d', 'e')", "abc()", "abc(de=123, qw='asd')"]:
            with self.assertRaises(ExprTemplateParseError) as cm:
                ExprTemplate.from_str(s)
            self.assertEqual(
                cm.exception.args,
                (
                    "function call must have exactly one argument or one keyword argument",
                ),
            )

        with self.assertRaises(ExprTemplateParseError) as cm:
            ExprTemplate.from_str(r"r'*'")
        self.assertEqual(
            cm.exception.args,
            ("expression must be a function call, found <class 'ast.Constant'>",),
        )

        with self.assertRaises(ExprTemplateParseError) as cm:
            ExprTemplate.from_str(r"to_csv(r'*')")
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
            et = ExprTemplate.from_str(case.template)
            node = ast.parse(case.source).body[0].value
            self.assertEqual(
                et.match_node(node), case.file, "(case %d) %s" % (idx, repr(case))
            )
