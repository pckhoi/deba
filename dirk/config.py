import typing
import pathlib

from attrs import define

from dirk.attrs_utils import field_transformer, doc
from dirk.serialize import yaml_load
from dirk.expr import Expressions
from dirk.files.file import File
from dirk.files.files_provider import FilesProvider


@define(field_transformer=field_transformer(globals()))
class Stage(object):
    """A stage is a group of scripts that have the same order of execution."""

    name: str = doc("name of the stage")
    ignore: typing.List[str] = doc(
        "list of scripts that will be ignored during dependency analysis"
    )
    common_dependencies: typing.List[str] = doc(
        "list of common dependencies of every scripts in this stage"
    )


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
    recipe: typing.List[str] = doc("the command to execute")


@define(field_transformer=field_transformer(globals()))
class Config(object):
    """Dirk configurations."""

    targets: typing.List[str] = doc(
        "explicit targets to generate when user run `make dirk`"
    )
    stages: typing.List[Stage] = doc(
        "list of execution stages. The order of this list is also the order of execution. What this mean concretely is that scripts from a stage can only take output from earlier stages or the same stage as input."
    )
    expressions: Expressions = doc("expression templates")
    overrides: typing.List[ExecutionRule] = doc(
        "list of make rule overrides. If a make rule with the same targets exists, replace it with the corresponding rule defined here."
    )
    files: typing.List[File] = doc(
        "list of files that can be pulled and kept up-to-date by dirk"
    )
    files_from: typing.List[FilesProvider] = doc(
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


_conf = None


def get_config() -> Config:
    global _conf
    if _conf is not None:
        return _conf
    for name in ["dirk.yaml", "dirk.yml"]:
        try:
            with open(name, "r") as f:
                _conf = yaml_load(f.read(), Config)
            return _conf
        except FileNotFoundError:
            continue
    raise FileNotFoundError(
        "dirk config file not found: %s" % (pathlib.Path().cwd() / "dirk.yaml")
    )
