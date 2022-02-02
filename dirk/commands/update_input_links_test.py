import unittest
import argparse

from dirk.commands.update_input_links import add_subcommand
from dirk.config import Config, Stage
from dirk.files.file import File
from dirk.test_utils import TempDirMixin


class UpdateInputLinksCommandTestCase(TempDirMixin, unittest.TestCase):
    def test_run(self):
        parser = argparse.ArgumentParser("dirk")
        subparsers = parser.add_subparsers()
        add_subcommand(subparsers)
        conf = Config(
            stages=[Stage(name="clean")],
            inputs={
                "new_orleans_pd": [
                    File(url="https://link-to.com/cprr-2020.csv"),
                    File(
                        url="https://link-to.com/pprr-2020.csv",
                        name="pprr_2018_2020.csv",
                    ),
                    File(
                        url="https://link-to.com/no-uof-2020.csv", name="uof_2020.csv"
                    ),
                ],
                "baton_rouge_pd": [
                    File(
                        url="https://link-to.com/br-cprr-2020.csv", name="cprr_2020.csv"
                    ),
                ],
            },
        )
        conf.root_dir = self._dir.name

        args = parser.parse_args(["update-input-links"])
        args.exec(conf, args)

        self.assertFileContent(
            ".dirk/input_links/new_orleans_pd/cprr-2020.csv.link",
            ["https://link-to.com/cprr-2020.csv"],
        )
        self.assertFileContent(
            ".dirk/input_links/new_orleans_pd/pprr_2018_2020.csv.link",
            ["https://link-to.com/pprr-2020.csv"],
        )
        mod_time = self.assertFileContent(
            ".dirk/input_links/new_orleans_pd/uof_2020.csv.link",
            ["https://link-to.com/no-uof-2020.csv"],
        )
        self.assertFileContent(
            ".dirk/input_links/baton_rouge_pd/cprr_2020.csv.link",
            ["https://link-to.com/br-cprr-2020.csv"],
        )

        args.exec(
            Config(
                stages=[Stage(name="clean")],
                inputs={
                    "new_orleans_pd": [
                        # update link
                        File(url="https://link-to.com/2/cprr-2020.csv"),
                        # replace file
                        File(
                            url="https://link-to.com/pprr-2017-2020.csv",
                            name="pprr_2017_2020.csv",
                        ),
                        # stays the same
                        File(
                            url="https://link-to.com/no-uof-2020.csv",
                            name="uof_2020.csv",
                        ),
                    ],
                    # remove dir baton_rouge_pd
                    # add dir bursly_pd
                    "bursly_pd": [
                        File(
                            url="https://link-to.com/brus-cprr-2020.csv",
                            name="cprr_2020.csv",
                        ),
                    ],
                },
                root_dir=self._dir.name,
            ),
            args,
        )

        self.assertFileContent(
            ".dirk/input_links/new_orleans_pd/cprr-2020.csv.link",
            ["https://link-to.com/2/cprr-2020.csv"],
        )
        self.assertFileRemoved(
            ".dirk/input_links/new_orleans_pd/pprr_2018_2020.csv.link"
        )
        self.assertFileContent(
            ".dirk/input_links/new_orleans_pd/pprr_2017_2020.csv.link",
            ["https://link-to.com/pprr-2017-2020.csv"],
        )
        self.assertFileNotModifiedSince(
            ".dirk/input_links/new_orleans_pd/uof_2020.csv.link", mod_time
        )
        self.assertDirRemoved(".dirk/input_links/baton_rouge_pd")
        self.assertFileContent(
            ".dirk/input_links/bursly_pd/cprr_2020.csv.link",
            ["https://link-to.com/brus-cprr-2020.csv"],
        )
