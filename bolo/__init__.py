import pathlib

from bolo.config import get_config


def data(s: str) -> pathlib.Path:
    conf = get_config()
    return pathlib.Path.cwd() / conf.data_dir / s.lstrip("/")
