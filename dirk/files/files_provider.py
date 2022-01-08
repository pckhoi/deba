import typing

from attrs import define

from dirk.attrs_utils import field_transformer, doc
from dirk.files.dvc import DVCFilesProvider
from dirk.files.wrgl import WrglFilesProvider


@define(field_transformer=field_transformer(globals()))
class FilesProvider(object):
    """A files provider defines how a group of files can be kept up-to-date by external tools.

    The following attributes are exclusive:
    - wrgl
    - dvc
    """

    wrgl: WrglFilesProvider = doc(
        "if defined, files are discovered from wrgl configuration"
    )
    dvc: DVCFilesProvider = doc(
        "if defined, files are discovered from dvc configuration"
    )
