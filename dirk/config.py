import typing

from attrs import define

from dirk.attrs_utils import field_transformer


@define(field_transformer=field_transformer(globals()))
class Stage(object):
    name: str


@define(field_transformer=field_transformer(globals()))
class Rule(object):
    target: str
    dependencies: typing.List[str]
    recipe: typing.List[str]


@define(field_transformer=field_transformer(globals()))
class Config(object):
    targets: typing.List[str]
    stages: typing.List[Stage]
    overrides: typing.List[Rule]
