import os.path as osp
import os
from pathlib import Path


def mkdir(path):
    if not osp.isdir(path):
        os.mkdir(path)


def path_parent(path):
    return Path(path).parent

