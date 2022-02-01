import unittest
import argparse

from dirk.commands.deps import add_subcommand
from dirk.config import Config, Stage
from dirk.deps.expr import Expressions
from dirk.test_utils import TempDirMixin


class DepsCommandTestCase(TempDirMixin, unittest.TestCase):
    def test_stage(self):
        parser = argparse.ArgumentParser("dirk")
        subparsers = parser.add_subparsers()
        add_subcommand(subparsers)
        conf = Config(
            stages=[Stage(name="clean"), Stage(name="fuse")],
            targets=["fuse/data.csv"],
            expressions=Expressions(
                inputs=[r'read_csv(".+\\.csv")'],
                outputs=[r'`*`.to_csv(".+\\.csv")'],
            ),
        )
        conf._root_dir = self._dir.name

        self.write_file(
            "clean/a.py",
            [
                'if __name__ == "__main__":',
                '  df = read_csv("raw/a_input.csv")',
                '  df.to_csv("clean/a_output.csv")',
            ],
        )

        args = parser.parse_args(["deps", "--stage", "clean"])
        args.exec(conf, args)

        with open(self.file_path(".dirk/deps/clean.d"), "r") as f:
            self.assertEqual(
                f.read(),
                "\n".join(
                    [
                        "CLEAN_DATA_DIR := $(DATA_DIR)/clean",
                        "",
                        "$(CLEAN_DATA_DIR): | $(DATA_DIR) ; @-mkdir $@ 2>/dev/null",
                        "",
                        "$(DATA_DIR)/clean/a_output.csv: $(MD5_DIR)/clean/a.py.md5 data/raw/a_input.csv | $(CLEAN_DATA_DIR)",
                        "\t$(PYTHON) clean/a.py",
                        "",
                        "",
                    ]
                ),
            )
