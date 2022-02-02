import json
import os
import typing
import pathlib

from attrs import define

from dirk.attrs_utils import field_transformer, doc
from dirk.serialize import yaml_load
from dirk.deps.expr import Expressions
from dirk.files.file import File
from dirk.files.files_provider import FilesProvider


@define(field_transformer=field_transformer(globals()), slots=False)
class Stage(object):
    """A stage is a group of scripts that have the same order of execution."""

    name: str = doc("name of the stage")
    ignore: typing.List[str] = doc(
        "list of scripts that will be ignored during dependency analysis"
    )
    common_dependencies: typing.List[str] = doc(
        "list of common dependencies of every scripts in this stage"
    )

    @property
    def deps_filepath(self) -> str:
        return os.path.join(self._conf.deps_dir, "%s.d" % self.name)

    @property
    def script_dir(self) -> str:
        return os.path.join(self._conf.root_dir, self.name)

    def scripts(self) -> typing.Iterator[str]:
        for filename in os.listdir(self.script_dir):
            if self.ignore is not None and filename in self.ignore:
                continue
            if filename.endswith(".py"):
                yield filename, os.path.join(self.script_dir, filename)


@define(field_transformer=field_transformer(globals()))
class ExecutionRule(object):
    """An execution rule defines how a target or a list of targets should be generated.

    An execution rule is roughly equivalent to a make rule like this:

        [target]: [dependencies]
            [recipe]
    """

    target: typing.Union[str, typing.List[str]] = doc(
        "single target or list of targets that can be generated"
    )
    dependencies: typing.List[str] = doc(
        "list of dependencies that when newer than the targets, trigger the execution"
    )
    recipe: str = doc("the command to execute")

    @property
    def target_set(self) -> typing.Set[str]:
        if type(self.target) is str:
            return set([self.target])
        return set(self.target)

    @property
    def target_str(self) -> str:
        if type(self.target) is str:
            return self.target
        return " ".join(self.target)


@define(field_transformer=field_transformer(globals()))
class Config(object):
    """Dirk configurations."""

    stages: typing.List[Stage] = doc(
        "list of execution stages. The order of this list is also the order of execution. What this mean concretely is that scripts from a stage can only take output from earlier stages or the same stage as input.",
        required=True,
    )

    root_dir: str = doc(
        "root directory from which to locate data and stage directories"
    )

    targets: typing.List[str] = doc(
        "explicit targets to generate when user run `make dirk`"
    )
    expressions: Expressions = doc("expression templates")
    overrides: typing.List[ExecutionRule] = doc(
        "list of make rule overrides. If a make rule with the same targets exists, replace it with the corresponding rule defined here."
    )
    inputs: typing.Dict[str, typing.List[File]] = doc(
        "list of files that can be pulled and kept up-to-date by dirk"
    )
    inputs_from: typing.List[FilesProvider] = doc(
        "list of external files providers that dirk can consult and discover more files"
    )
    python_path: typing.List[str] = doc(
        "additional search paths for module files. The directory that contains dirk.yaml file will be prepended to this list. This list is then concatenated as PYTHONPATH env var during script execution."
    )
    data_dir: str = doc(
        "keep all generated data in this folder",
        default="data",
        converter=lambda s: s if type(s) is not str else s.strip("/"),
        required=True,
    )

    def script_search_paths(self) -> typing.List[str]:
        if self.python_path is None:
            return [self.root_dir]
        return [self.root_dir] + self.python_path

    def __attrs_post_init__(self):
        for stage in self.stages:
            stage._conf = self

    def get_stage(self, name: str) -> typing.Union[Stage, None]:
        for stage in self.stages:
            if stage.name == name:
                return stage

    def is_data_from_latter_stages(self, stage_name: str, file_name: str) -> bool:
        check = False
        file_stage = file_name.split("/")[0]
        for stage in self.stages:
            if stage.name == stage_name:
                check = True
            elif check and stage.name == file_stage:
                return True
        return False

    @property
    def dirk_dir(self) -> str:
        return os.path.join(self.root_dir, ".dirk")

    @property
    def deps_dir(self) -> str:
        return os.path.join(self.dirk_dir, "deps")

    @property
    def main_deps_filepath(self) -> str:
        return os.path.join(self.dirk_dir, "main.d")

    @property
    def input_links_dir(self) -> str:
        return os.path.join(self.dirk_dir, "input_links")


_conf = None


def get_config() -> Config:
    global _conf
    if _conf is not None:
        return _conf
    for name in ["dirk.yaml", "dirk.yml"]:
        try:
            with open(name, "r") as f:
                _conf = yaml_load(f.read(), Config)
            if _conf.root_dir is None:
                _conf.root_dir = os.getcwd()
            return _conf
        except FileNotFoundError:
            continue
    raise FileNotFoundError(
        "dirk config file not found: %s" % (pathlib.Path().cwd() / "dirk.yaml")
    )
