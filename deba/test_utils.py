import typing
import tempfile
import ast
import io
import os
import sys
import shutil

from attrs import define, field


def ast_dump(obj):
    if sys.version_info[1] < 9:
        ast.dump(obj)
    else:
        ast.dump(obj, indent=4)


class ASTMixin(object):
    def assertASTEqual(
        self, a: ast.AST, b: ast.AST, msg: typing.Union[str, None] = None
    ):
        if a is None or b is None:
            self.assertEqual(a, b, msg)
        else:
            self.assertEqual(ast_dump(a), ast_dump(b), msg)


class TempDirMixin(object):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._dir = tempfile.TemporaryDirectory()

    def setUp(self):
        super().setUp()
        self.maxDiff = None
        for filename in os.listdir(self._dir.name):
            file_path = os.path.join(self._dir.name, filename)
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)

    @classmethod
    def tearDownClass(cls) -> None:
        cls._dir.cleanup()
        return super().tearDownClass()

    def file_path(self, filename: str) -> str:
        return os.path.join(self._dir.name, filename)

    def write_file(self, filename: str, lines: typing.List[str]):
        os.makedirs(os.path.dirname(self.file_path(filename)), exist_ok=True)
        with open(self.file_path(filename), "w") as f:
            f.write("\n".join(lines))

    def mod_time(self, filename: str) -> float:
        return os.path.getmtime(self.file_path(filename))

    def assertFileContent(self, filename: str, lines: typing.List[str]) -> float:
        """Asserts file content and returns modified time as seconds since the epoch"""
        with open(self.file_path(filename), "r") as f:
            self.assertEqual(
                f.read(),
                "\n".join(lines),
            )
        return self.mod_time(filename)

    def assertFileModifiedSince(self, filename: str, time: float):
        self.assertGreater(self.mod_time(filename), time)

    def assertFileNotModifiedSince(self, filename: str, time: float):
        self.assertEqual(self.mod_time(filename), time)

    def assertFileRemoved(self, filename: str):
        self.assertFalse(os.path.isfile(self.file_path(filename)))

    def assertDirRemoved(self, dirname: str):
        self.assertFalse(os.path.isdir(self.file_path(dirname)))
