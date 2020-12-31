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

# try:
#     import coloredlogs
#
#     coloredlogs.install()
# except BaseException:
#     pass

logging.basicConfig(
    stream=sys.stdout,
    format="[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s",
    level=logging.INFO,
)

print_lock = Lock()
last_print_mode = True  # record latest mode of print_()


def print_(string, print_in_same_line=False, **kwargs):
    """
    thread printing
    :param string: string to be printed
    :param print_in_same_line: set True to print in the same line
    :return: None
    """
    global last_print_mode, print_lock
    print_lock.acquire()
    if print_in_same_line:
        print('\r', end='')
        print('\r{}'.format(string), end='', flush=True)
    else:
        if last_print_mode:  # print \r to avoid redundant new line
            print('\r')
        print(string, **kwargs)
    last_print_mode = print_in_same_line
    print_lock.release()


def print_exceptions(ex: Exception) -> None:
    print_('{0}: {1}'.format(ex.__class__.__name__, ex))


def print_exceptions_to_file(ex: Exception, file) -> None:
    print_('{0}: {1}'.format(ex.__class__.__name__, ex), file=file)


class ProgressBar(object):
    def __init__(self, total: int = 100, initial: int = 0):
        self.total = total
        self.initial = initial
        self.n = 0
        self.colour = 'green'
        self.lock = Lock()

    def set_colour(self, colour: str):
        self.lock.acquire()
        self.colour = colour
        self.lock.release()

    def display(self):
        self.lock.acquire()
        n = self.n
        total = self.total
        colour = self.colour
        self.lock.release()
        points = int(n / total * 1000)
        percent = colored('[%3d%%] ' % int(points / 10), colour)
        integer = int(points / 10)
        decimal = points % 10
        if points != 1000:
            print_("{}progress:| {}{}{} | {} / {} |".format(percent, '#' * integer, decimal, '-' * (99 - integer), n,
                                                            total), print_in_same_line=True)
        else:
            print_("{}progress:| {} | {} / {} |".format(percent, '#' * 100, n, total), print_in_same_line=True)

    def reset(self, total: int = None):
        self.lock.acquire()
        self.n = 0
        if total is not None:
            self.total = total
        self.lock.release()

    def update(self, n: int = 1):
        self.lock.acquire()
        if self.n < self.total:
            self.n += n
        self.lock.release()
        self.display()
