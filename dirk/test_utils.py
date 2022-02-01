import typing
import tempfile
import ast
import os


class ASTMixin(object):
    def assertASTEqual(
        self, a: ast.AST, b: ast.AST, msg: typing.Union[str, None] = None
    ):
        if a is None or b is None:
            self.assertEqual(a, b, msg)
        else:
            self.assertEqual(ast.dump(a, indent=4), ast.dump(b, indent=4), msg)


class TempDirMixin(object):
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

    def assertFileContent(self, filename: str, lines: typing.List[str]):
        with open(self.file_path(filename), "r") as f:
            self.assertEqual(
                f.read(),
                "\n".join(lines),
            )
