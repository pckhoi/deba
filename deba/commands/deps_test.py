import unittest
import argparse

from deba.commands.deps import add_subcommand
from deba.config import Config, ExecutionRule, Stage
from deba.deps.expr import ExprPatterns
from deba.test_utils import TempDirMixin


class DepsCommandTestCase(TempDirMixin, unittest.TestCase):
    def test_run(self):
        parser = argparse.ArgumentParser("deba")
        subparsers = parser.add_subparsers()
        add_subcommand(subparsers)
        conf = Config(
            stages=[
                Stage(name="clean", ignored_scripts=["d.py"]),
                Stage(name="fuse", ignored_targets=["duplicates.csv"]),
            ],
            targets=["fuse/data.csv"],
            patterns=ExprPatterns(
                prerequisites=[r'read_csv(".+\\.csv")'],
                targets=[r'`*`.to_csv(".+\\.csv")'],
            ),
            overrides=[
                ExecutionRule(
                    target="clean/b_output.csv",
                    prerequisites=["raw/my_b_input.csv"],
                    recipe="my_command",
                ),
                ExecutionRule(
                    target="clean/c.csv",
                    prerequisites=["raw/c.csv"],
                    recipe="my_other_command",
                ),
            ],
            root_dir=self._dir.name,
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
        self.write_file(
            "fuse/a.py",
            [
                'if __name__ == "__main__":',
                '  df = read_csv("clean/b_output.csv")',
                '  df.to_csv("duplicates.csv")',
                '  df.to_csv("fuse/data.csv")',
            ],
        )
        self.write_file("fuse/b.pyc", [""])

        args = parser.parse_args(["deps", "--stage", "clean"])
        args.exec(conf, args)

        self.assertFileContent(
            ".deba/deps/clean.d",
            [
                "$(DEBA_DATA_DIR)/clean: ; @-mkdir -p $@ 2>/dev/null",
                "",
                "$(DEBA_DATA_DIR)/clean/a_output.csv &: $(DEBA_MD5_DIR)/clean/a.py.md5 $(DEBA_DATA_DIR)/raw/a_input.csv | $(DEBA_DATA_DIR)/clean",
                "\t$(call deba_execute,clean/a.py)",
                "",
                "",
            ],
        )

        args = parser.parse_args(["deps", "--stage", "fuse"])
        args.exec(conf, args)

        self.assertFileContent(
            ".deba/deps/fuse.d",
            [
                "$(DEBA_DATA_DIR)/fuse: ; @-mkdir -p $@ 2>/dev/null",
                "",
                "$(DEBA_DATA_DIR)/fuse/data.csv &: $(DEBA_MD5_DIR)/fuse/a.py.md5 $(DEBA_DATA_DIR)/clean/b_output.csv | $(DEBA_DATA_DIR)/fuse",
                "\t$(call deba_execute,fuse/a.py)",
                "",
                "",
            ],
        )

        args = parser.parse_args(["deps"])
        args.exec(conf, args)

        self.assertFileContent(
            ".deba/main.d",
            [
                "$(DEBA_DATA_DIR)/clean/b_output.csv &: $(DEBA_DATA_DIR)/raw/my_b_input.csv",
                "\tmy_command",
                "",
                "$(DEBA_DATA_DIR)/clean/c.csv &: $(DEBA_DATA_DIR)/raw/c.csv",
                "\tmy_other_command",
                "",
                "",
            ],
        )
