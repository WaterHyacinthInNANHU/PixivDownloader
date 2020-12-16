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
            print_("\r{}progress:| {}{}{} | {} / {} |".format(percent, '#'*integer, decimal, '-'*(99-integer), n,
                                                              total), end='')
        else:
            print_("\r{}progress:| {} | {} / {} |".format(percent, '#' * 100, n, total))

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
