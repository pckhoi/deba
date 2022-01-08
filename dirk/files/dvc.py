import typing

from attrs import define


from dirk.attrs_utils import field_transformer


@define(field_transformer=field_transformer(globals()))
class DVCFilesProvider(object):
    pass
