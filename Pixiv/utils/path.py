import os.path as osp
import os
from pathlib import Path
import re

SYSTEM_CHARACTERS = r'\/:*?"<>'


def mkdir_(path):
    if not osp.isdir(path):
        os.mkdir(path)


def parent_path_(path):
    return Path(path).parent


def root_path_():
    """
    return root path of utils package
    :return: path
    """
    current_path = osp.abspath(__file__)
    utils_path = parent_path_(current_path)
    return parent_path_(utils_path)


def join_(a, *paths):
    return osp.join(a, *paths)


def set_path_(*path):
    for p in path:
        os.environ['PATH'] += ';{}'.format(p)


def get_path_of_environment_variable_(variable):
    return os.environ[variable]


def replace_system_character(string: str, char: str = '&'):
    rx = '[' + re.escape(SYSTEM_CHARACTERS) + ']'
    res = re.sub(rx, char, string)
    spaces = [1 for c in res if c == ' ']
    res = res[len(spaces):]
    return res
