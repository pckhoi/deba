import os
import typing
import pathlib

from attrs import define, validators

from deba.attrs_utils import field_transformer, doc
from deba.serialize import yaml_dump, yaml_load
from deba.deps.expr import ExprPatterns


@define(field_transformer=field_transformer(globals()), slots=False)
class Stage(object):
    """A stage is a group of scripts that have the same order of execution."""

    name: str = doc(
        "name of the stage",
        required=True,
        validator=validators.matches_re(r"^[a-zA-Z][a-zA-Z0-9-_]+$"),
    )
    ignored_scripts: typing.List[str] = doc(
        "list of scripts that will be ignored during dependency analysis"
    )
    common_prerequisites: typing.List[str] = doc(
        "list of common prerequisites of every scripts in this stage"
    )
    ignored_targets: typing.List[str] = doc(
        "list of targets that will be ignored (not written to Makefile)"
    )

    @property
    def deps_filepath(self) -> str:
        return os.path.join(self._conf.deps_dir, "%s.d" % self.name)

    @property
    def script_dir(self) -> str:
        return os.path.join(self._conf._root_dir, self.name)

    def scripts(self) -> typing.Iterator[str]:
        for filename in os.listdir(self.script_dir):
            if self.ignored_scripts is not None and filename in self.ignored_scripts:
                continue
            if filename.endswith(".py"):
                yield filename, os.path.join(self.script_dir, filename)


@define(field_transformer=field_transformer(globals()))
class ExecutionRule(object):
    """An execution rule defines how a target or a list of targets should be generated.

    An execution rule is roughly equivalent to a make rule like this:

        [target]: [prerequisites]
            [recipe]
    """

    target: typing.Union[str, typing.List[str]] = doc(
        "single target or list of targets that can be generated"
    )
    prerequisites: typing.List[str] = doc(
        "list of prerequisites that when newer than the targets, trigger the execution"
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
            return "$(DEBA_DATA_DIR)/%s" % self.target
        return " ".join("$(DEBA_DATA_DIR)/%s" % s for s in self.target)


@define(field_transformer=field_transformer(globals()))
class Config(object):
    """Dirk configurations."""

    stages: typing.List[Stage] = doc(
        "list of execution stages. The order of this list is also the order of execution. What this mean concretely is that scripts from a stage can only take target from earlier stages or the same stage as prerequisite.",
        required=True,
    )

    root_dir: str = doc(
        "root directory from which to locate data and stage directories"
    )

    targets: typing.List[str] = doc(
        "explicit targets to generate when user run `make deba`"
    )

    patterns: ExprPatterns = doc("expression templates")

    overrides: typing.List[ExecutionRule] = doc(
        "list of make rule overrides. If a make rule with the same targets exists, replace it with the corresponding rule defined here."
    )

    python_path: typing.List[str] = doc(
        "additional search paths for module files. The directory that contains deba.yaml file will be prepended to this list. This list is then concatenated as PYTHONPATH env var during script execution."
    )

    enforce_stage_order: bool = doc(
        "make sure that scripts cannot read outputs of later stages.", default=False
    )

    data_dir: str = doc(
        "keep all generated data in this folder",
        default="data",
        converter=lambda s: s if type(s) is not str else s.rstrip("/"),
        required=True,
    )

    md5_dir: str = doc(
        "directory containing md5 checksums of all Python scripts",
        default=".deba/md5",
        converter=lambda s: s if type(s) is not str else s.rstrip("/"),
        required=True,
    )

    @property
    def script_search_paths(self) -> typing.List[str]:
        if self.python_path is None:
            return [self._root_dir]
        return [self._root_dir] + self.python_path

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

    def save(self):
        with open(os.path.join(self._root_dir, "deba.yaml"), "w") as f:
            f.write(yaml_dump(self))

    @property
    def _root_dir(self) -> str:
        if self.root_dir is not None:
            return self.root_dir
        return os.getcwd()

    @property
    def deba_dir(self) -> str:
        return os.path.join(self._root_dir, ".deba")

    @property
    def deps_dir(self) -> str:
        return os.path.join(self.deba_dir, "deps")

    @property
    def main_deps_filepath(self) -> str:
        return os.path.join(self.deba_dir, "main.d")


_conf = None


def get_config(root: typing.Union[str, None] = None) -> Config:
    global _conf
    if _conf is not None:
        return _conf
    try:
        deba_path = "deba.yaml"
        if root is not None:
            deba_path = os.path.join(root, deba_path)
        with open(deba_path, "r") as f:
            _conf = yaml_load(f.read(), Config)
        if root is not None:
            _conf.root_dir = root
        return _conf
    except FileNotFoundError:
        raise FileNotFoundError(
            "deba config file not found: %s" % (pathlib.Path().cwd() / "deba.yaml")
        )
