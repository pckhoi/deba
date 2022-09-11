import unittest
import argparse

from deba.commands.deps import add_subcommand
from deba.config import Config, ExecutionRule, Stage
from deba.deps.expr import ExprPatterns
from deba.test_utils import TempDirMixin
from deba.test_utils import subcommand_testcase, CommandTestCaseMixin


@subcommand_testcase(add_subcommand)
class DepsCommandTestCase(CommandTestCaseMixin, TempDirMixin, unittest.TestCase):
    def test_run(self):
        conf = Config(
            stages=[
                Stage(name="clean", ignored_scripts=["d.py", "*.spot-check.py"]),
                Stage(name="fuse", ignored_targets=["duplicates.csv"]),
            ],
            targets=["fuse/data.csv", "fuse/data_b.csv"],
            patterns=ExprPatterns(
                prerequisites=[r'read_csv(".+\\.csv")'],
                targets=[r'`*`.to_csv(".+\\.csv")'],
                references=[r'json.loads(".+\\.json")'],
            ),
            overrides=[
                ExecutionRule(
                    target="clean/b_output.csv",
                    prerequisites=["$(DEBA_DATA_DIR)/raw/my_b_input.csv"],
                    recipe="$(call deba_execute,my_command.py)",
                ),
                ExecutionRule(
                    target="clean/c.csv",
                    prerequisites=["abc.dvc"],
                    recipe="$(call deba_execute,my_other_command.py)",
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
            "clean/d.spot-check.py",
            [
                'if __name__ == "__main__":',
                '  df = read_csv("raw/d_spot_check_input.csv")',
                '  df.to_csv("clean/d_spot_check_output.csv")',
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
        self.write_file(
            "fuse/b.py",
            [
                'if __name__ == "__main__":',
                '  conf = json.loads("my_config.json")',
                '  df.to_csv("fuse/data_b.csv")',
            ],
        )
        self.write_file("fuse/b.pyc", [""])

        self.exec(conf, "deps", "--stage", "clean")

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

        self.exec(conf, "deps", "--stage", "fuse")

        self.assertFileContent(
            ".deba/deps/fuse.d",
            [
                "$(DEBA_DATA_DIR)/fuse: ; @-mkdir -p $@ 2>/dev/null",
                "",
                "$(DEBA_DATA_DIR)/fuse/data.csv &: $(DEBA_MD5_DIR)/fuse/a.py.md5 $(DEBA_DATA_DIR)/clean/b_output.csv | $(DEBA_DATA_DIR)/fuse",
                "\t$(call deba_execute,fuse/a.py)",
                "",
                "$(DEBA_DATA_DIR)/fuse/data_b.csv &: $(DEBA_MD5_DIR)/fuse/b.py.md5 $(DEBA_MD5_DIR)/my_config.json.md5 | $(DEBA_DATA_DIR)/fuse",
                "\t$(call deba_execute,fuse/b.py)",
                "",
                "",
            ],
        )

        self.exec(conf, "deps")

        self.assertFileContent(
            ".deba/main.d",
            [
                "$(DEBA_DATA_DIR)/clean/b_output.csv &: $(DEBA_DATA_DIR)/raw/my_b_input.csv",
                "\t$(call deba_execute,my_command.py)",
                "",
                "$(DEBA_DATA_DIR)/clean/c.csv &: abc.dvc",
                "\t$(call deba_execute,my_other_command.py)",
                "",
                "",
            ],
        )

    def test_skip_scripts_with_no_target(self):
        conf = Config(
            stages=[
                Stage(name="fuse"),
            ],
            targets=["fuse/data.csv"],
            patterns=ExprPatterns(
                prerequisites=[r'read_csv(".+\\.csv")'],
                targets=[r'`*`.to_csv(".+\\.csv")'],
            ),
            root_dir=self._dir.name,
        )

        self.write_file(
            "fuse/a.py",
            [
                'if __name__ == "__main__":',
                '  df = read_csv("raw/a_input.csv")',
            ],
        )
        self.write_file(
            "fuse/b.py",
            [
                'if __name__ == "__main__":',
                '  pd.DataFrame([[0,1]]).to_csv("clean/b_output.csv")',
            ],
        )
        self.write_file(
            "fuse/c.py",
            [
                'if __name__ == "__main__":',
                '  df = read_csv("raw/d_input.csv")',
                '  df.to_csv("fuse/d_output.csv")',
            ],
        )

        self.exec(conf, "deps", "--stage", "fuse")

        self.assertFileContent(
            ".deba/deps/fuse.d",
            [
                "$(DEBA_DATA_DIR)/fuse: ; @-mkdir -p $@ 2>/dev/null",
                "",
                "$(DEBA_DATA_DIR)/fuse/d_output.csv &: $(DEBA_MD5_DIR)/fuse/c.py.md5 $(DEBA_DATA_DIR)/raw/d_input.csv | $(DEBA_DATA_DIR)/fuse",
                "	$(call deba_execute,fuse/c.py)",
                "",
                "",
            ],
        )
