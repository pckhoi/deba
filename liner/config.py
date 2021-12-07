import typing

import attr

from liner.stage import Stage
from liner.repositories.base import Repository


@attr.s(auto_attribs=True)
class Config(object):
    stages = attr.ib(factory=list, type=typing.List[Stage])
    repositories = attr.ib(
        factory=list,
        type=typing.List[Repository],
        validator=attr.validators.deep_iterable(
            member_validator=attr.validators.provides(Repository),
        )
    )
