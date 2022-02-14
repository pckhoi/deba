import pathlib
import subprocess
import unittest
import os

from dirk.commands import get_parser
from dirk.config import get_config
from dirk.test_utils import TempDirMixin


class IntegrationTestCase(TempDirMixin, unittest.TestCase):
    def test_everything(self):
        os.chdir(self._dir.name)
        parser = get_parser()
        args = parser.parse_args(
            [
                "init",
                "--stages",
                "clean",
                "fuse",
                "--targets",
                "fuse/personnel.csv",
                "--input-patterns",
                r"csv.load_csv(r'.+\.csv')",
                "--output-patterns",
                r"csv.to_csv(r'.+\.csv')",
            ]
        )
        args.exec(None, args)
        self.assertTrue(os.path.isfile(self.file_path("dirk.yaml")))
        self.assertTrue(os.path.isfile(self.file_path("dirk.mk")))
        self.assertTrue(os.path.isfile(self.file_path(".gitignore")))
        self.assertTrue(os.path.isfile(self.file_path("Makefile")))

        self.write_file(
            "data/inputs/baton_rouge_pd/personnel1.csv",
            ["id,name,age", "1,john,28", "2,dave,30"],
        )
        self.write_file(
            "data/inputs/baton_rouge_pd/personnel2.csv",
            ["id,name,age", "1,alice,27", "2,jane,31"],
        )
        conf = get_config()
        conf.python_path = [str(pathlib.Path(__file__).parent.parent)]
        conf.save()

        self.write_file(
            "lib/csv.py",
            [
                "import csv",
                "",
                "",
                "def load_csv(name):",
                "  rows = []",
                "  with open(name, newline='') as f:",
                "    reader = csv.reader(f)",
                "    for row in reader:",
                "      rows.append(row)",
                "  return rows",
                "",
                "",
                "def to_csv(name, rows):",
                "  with open(name, 'w', newline='') as f:",
                "    writer = csv.writer(f)",
                "    writer.writerows(rows)",
                "",
            ],
        )

        self.write_file(
            "clean/baton_rouge_pd.py",
            [
                "from lib import csv",
                "import dirk",
                "",
                "",
                "if __name__ == '__main__':",
                "  per = csv.load_csv(dirk.data('inputs/baton_rouge_pd/personnel1.csv'))",
                "  per[0].append('agency')",
                "  per[1:] = [row+'Baton Rouge PD' for row in per[1:]]",
                "  csv.to_csv(dirk.data('clean/baton_rouge_pd/personnel.csv'))",
                "",
            ],
        )

        print(
            subprocess.run(
                ["make", ".dirk/main.d"],
                stdout=subprocess.PIPE,
                universal_newlines=True,
            ).stdout
        )

        print(
            subprocess.run(
                ["make", "data/clean/baton_rouge_pd/personnel.csv"],
                stdout=subprocess.PIPE,
                universal_newlines=True,
            )
        )
        self.assertFileContent("data/clean/baton_rouge_pd/personnel.csv", [""])
