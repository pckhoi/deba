import typing

from attrs import define

from dirk.attrs_utils import field_transformer, doc
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
    overrides: typing.List[ExecutionRule] = doc(
        "list of make rule overrides. If a make rule with the same targets exists, replace it with the corresponding rule defined here."
    )
    files: typing.List[File] = doc(
        "list of files that can be pulled and kept up-to-date by dirk"
    )
    files_from: typing.List[FilesProvider] = doc(
        "list of external files providers that dirk can consult and discover more files"
    )
    data_dir: str = doc("keep all generated data in this folder", default="data")
