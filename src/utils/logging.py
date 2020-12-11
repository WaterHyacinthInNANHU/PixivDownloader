# Copyright 2004-present Facebook. All Rights Reserved.

# Put some color in you day!
import logging
import sys
from termcolor import colored
from threading import Lock

STD_INFO = colored('[INFO] ', 'green')
STD_ERROR = colored('[ERROR] ', 'red')
STD_WARNING = colored('[WARNING] ', 'yellow')
STD_INPUT = colored('[INPUT] ', 'blue')

try:
    import coloredlogs

    coloredlogs.install()
except BaseException:
    pass

logging.basicConfig(
    stream=sys.stdout,
    format="[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s",
    level=logging.INFO,
)

print_lock = Lock()


def print_(info, **kwargs):
    """
    thread printing
    :param info: message to be printed
    :return: None
    """
    print_lock.acquire()
    print(info, **kwargs)
    print_lock.release()
