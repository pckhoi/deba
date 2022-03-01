import pathlib

from deba.config import get_config

_root = None


def set_root(root: str):
    """Set Deba root folder

    Root folder is the folder that contains deba.yaml file. If not set
    then the current working directory is assumed to be the root folder.

    :param str root: the root folder

    :rtype: None
    """
    global _root
    _root = root


def data(filepath: str) -> pathlib.Path:
    """Joins Deba's dataDir with filepath

    This function will read deba.yaml to determine dataDir. By defaults,
    it read from current working directory. If that's not where deba.yaml
    is, set the location with set_root.

    :param str filepath: file path relative to data directory

    :rtype: str
    """
    conf = get_config(_root)
    return pathlib.Path(conf._root_dir) / conf.data_dir / filepath.lstrip("/")
