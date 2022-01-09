import re
import itertools
import typing
import ast
from fnmatch import fnmatchcase

from attrs import define, field, Factory, setters
from dirk.attrs_utils import field_transformer


class ExprTemplateParseError(ValueError):
    pass


@define(field_transformer=field_transformer(globals()))
class ExprTemplate(object):
    node: ast.AST = field()
    file_pat: re.Pattern = field()
    patterns: typing.List[str] = field(factory=list)
    backtick_name_pat: typing.ClassVar[re.Pattern] = re.compile(
        r"^dirk_backtick_pat_(\d{3})$"
    )

    @node.validator
    def is_expr_valid(self, attr, value: ast.AST):
        str_count = 0
        for node in ast.walk(value):
            if isinstance(node, ast.Constant) and type(node.value) is str:
                str_count += 1
                try:
                    re.compile(node.value)
                except re.error as e:
                    raise ExprTemplateParseError(
                        "invalid regular expression r'%s': %s" % (node.value, e.args[0])
                    )
                s = node.value if node.value[0] == "^" else "^" + node.value
                s = s if s[-1] == "$" else s + "$"
                self.file_pat = re.compile(s)
        if str_count != 1:
            raise ExprTemplateParseError(
                "expect exactly 1 string in expression template, found %d" % str_count
            )

    @classmethod
    def from_str(cls, text: str) -> "ExprTemplate":
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
                    next_backtick += e.offset
                    pattern = line[e.offset : next_backtick]
                    lines[e.lineno - 1] = "%sdirk_backtick_pat_%03d%s" % (
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
                    raise ExprTemplateParseError(
                        "expect exactly 1 expression, found %d" % len(mod.body)
                    )
                t.node = mod.body[0].value
                return t

    def compare_ast(self, node1: ast.AST, node2: ast.AST) -> typing.Tuple[str, bool]:
        if type(node1) is not type(node2):
            return "", False
        if isinstance(node1, ast.AST):
            if isinstance(node1, ast.Name):
                if type(node1.ctx) is not type(node2.ctx):
                    return "", False
                if node1.id == node2.id:
                    return "", True
                m = ExprTemplate.backtick_name_pat.match(node1.id)
                if m is None:
                    return "", False
                pat = self.patterns[int(m.group(1))]
                return "", fnmatchcase(node2.id, pat)
            elif isinstance(node1, ast.Constant):
                if type(node1.value) is str and type(node2.value) is str:
                    m = self.file_pat.match(node2.value)
                    if m is None:
                        return "", False
                    return node2.value, True
                return "", node1.value == node2.value
            s = ""
            for k, v in vars(node1).items():
                if k in ("lineno", "col_offset", "end_lineno", "end_col_offset"):
                    continue
                v, ok = self.compare_ast(v, getattr(node2, k))
                if not ok:
                    return "", False
                elif v != "":
                    s = v
            return s, True
        elif isinstance(node1, list):
            s = ""
            for v, ok in itertools.starmap(
                self.compare_ast, itertools.zip_longest(node1, node2)
            ):
                if not ok:
                    return "", False
                elif v != "":
                    s = v
            return s, True
        else:
            return "", node1 == node2

    def match_node(self, node: ast.AST) -> typing.Union[None, str]:
        s, ok = self.compare_ast(self.node, node)
        if ok:
            return s
