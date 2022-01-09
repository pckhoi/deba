import typing
import ast
from fnmatch import fnmatchcase

from attrs import define, field, Factory
from attrs_utils import field_transformer


class ExprTemplateParseError(ValueError):
    pass


@define(field_transformer=field_transformer(globals()))
class ExprTemplate(object):
    expr: ast.Expr
    patterns: typing.List[str] = Factory(list)

    @classmethod
    def parse(cls, text: str) -> "ExprTemplate":
        t = cls()
        while True:
            try:
                mod = ast.parse(text)
            except SyntaxError as e:
                lines = text.split("\n")
                line = lines[e.lineno - 1]
                c = line[e.offset - 1]
                if c == "`":
                    next_backtick = line[e.offset :].find("`")
                    if next_backtick == -1:
                        raise ExprTemplateParseError(
                            "backtick pattern not closed at line %d, offset %d"
                            % (e.lineno, e.offset)
                        )
                    next_backtick += e.offset - 1
                    pattern = line[e.offset : next_backtick]
                    lines[e.lineno - 1] = "%sdirk_backtick_pat_%30d%s" % (
                        line[: e.offset - 1],
                        len(t.patterns),
                        line[next_backtick + 1 :],
                    )
                    t.patterns.append(pattern)
                    text = "\n".join(lines)
                else:
                    raise
            else:
                if len(mod.body) > 1:
                    raise ExprTemplateParseError("more than one expression found")
                t.expr = mod.body[0]
                return t
