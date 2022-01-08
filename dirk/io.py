import pathlib

from dirk.config import Config
from dirk.serialize import yaml_load


def load_config() -> Config:
    with open(pathlib.Path.cwd() / "dirk.yaml", "r") as f:
        return yaml_load(f.read(), Config)
