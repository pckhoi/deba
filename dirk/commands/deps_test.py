import unittest
import argparse

from dirk.commands.deps import add_subcommand
from dirk.config import Config, ExecutionRule, Stage
from dirk.deps.expr import Expressions
from dirk.test_utils import TempDirMixin


class DepsCommandTestCase(TempDirMixin, unittest.TestCase):
    def test_run(self):
        parser = argparse.ArgumentParser("dirk")
        subparsers = parser.add_subparsers()
        add_subcommand(subparsers)
        conf = Config(
            stages=[Stage(name="clean", ignore=["d.py"]), Stage(name="fuse")],
            targets=["fuse/data.csv"],
            expressions=Expressions(
                inputs=[r'read_csv(".+\\.csv")'],
                outputs=[r'`*`.to_csv(".+\\.csv")'],
            ),
            overrides=[
                ExecutionRule(
                    target="clean/b_output.csv",
                    dependencies=["raw/my_b_input.csv"],
                    recipe="my_command",
                ),
                ExecutionRule(
                    target="clean/c.csv",
                    dependencies=["raw/c.csv"],
                    recipe="my_other_command",
                ),
            ],
            root_dir = self._dir.name,
        )

        self.write_file(
            "clean/a.py",
            [
                'if __name__ == "__main__":',
                '  df = read_csv("raw/a_input.csv")',
                '  df.to_csv("clean/a_output.csv")',
            ],
        )
        self.write_file(
            "clean/b.py",
            [
                'if __name__ == "__main__":',
                '  df = read_csv("raw/b_input.csv")',
                '  df.to_csv("clean/b_output.csv")',
            ],
        )
        self.write_file(
            "clean/d.py",
            [
                'if __name__ == "__main__":',
                '  df = read_csv("raw/d_input.csv")',
                '  df.to_csv("clean/d_output.csv")',
            ],
        )

        args = parser.parse_args(["deps", "--stage", "clean"])
        args.exec(conf, args)

        self.assertFileContent(
            ".dirk/deps/clean.d",
            [
                "CLEAN_DATA_DIR := $(DATA_DIR)/clean",
                "",
                "$(CLEAN_DATA_DIR): | $(DATA_DIR) ; @-mkdir $@ 2>/dev/null",
                "",
                "$(DATA_DIR)/clean/a_output.csv &: $(MD5_DIR)/clean/a.py.md5 $(DATA_DIR)/raw/a_input.csv | $(CLEAN_DATA_DIR)",
                "\t$(PYTHON) clean/a.py",
                "",
                "",
            ],
        )

        args = parser.parse_args(["deps"])
        args.exec(conf, args)

        self.assertFileContent(
            ".dirk/main.d",
            [
                "all: $(DATA_DIR)/fuse/data.csv",
                "",
                "clean/b_output.csv &: raw/my_b_input.csv",
                "\tmy_command",
                "",
                "clean/c.csv &: raw/c.csv",
                "\tmy_other_command",
                "",
                "",
            ],
        )
