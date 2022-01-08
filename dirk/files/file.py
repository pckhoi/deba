import typing

from attrs import define

from dirk.attrs_utils import field_transformer, doc


@define(field_transformer=field_transformer(globals()))
class File(object):
    """A file defines how a file can be downloaded (and thus kept up-to-date) by dirk"""

    name: str = doc(
        "name of the file. If not defined then the name will be generated from the url"
    )
    url: str = doc(
        "the download link of this file. The file is considered changed only when this link change."
    )
