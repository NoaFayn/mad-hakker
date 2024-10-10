"""Simple console logging class.
Inspired by https://github.com/p0dalirius
"""
from __future__ import annotations

import typing
from rich.markup import escape

if typing.TYPE_CHECKING:
    import argparse
    from rich.console import Console


class Logger(object):
    def __init__(self, console: Console, verbosity=0, quiet=False, raw=False, escape_rich_markup=False, highlight_markup=False):
        self.console: Console = console
        self.verbosity = verbosity
        self.quiet = quiet
        self.raw = raw
        self.escape_rich_markup = escape_rich_markup
        self.highlight_markup = highlight_markup

    def escape(self, message: str, escape_rich_markup: bool):
        return escape(message) if escape_rich_markup or self.escape_rich_markup else message

    def console_print(self, message: any, color: str, verbosity_threshold: int, level: str, escape_rich_markup=True):
        if self.verbosity >= verbosity_threshold and not self.quiet:
            if self.raw:
                self.console.print(self.escape(str(message), escape_rich_markup), highlight=self.highlight_markup)
            else:
                self.console.print(f"[{color}]\\[{level}][/{color}] {self.escape(str(message), escape_rich_markup)}", highlight=self.highlight_markup)

    def debug(self, message: any, escape_rich_markup=True):
        self.console_print(message, 'yellow3', 2, 'DEBUG', escape_rich_markup)

    def verbose(self, message: any, escape_rich_markup=True):
        self.console_print(message, 'blue', 1, 'VERBOSE', escape_rich_markup)

    def info(self, message: any, escape_rich_markup=True):
        self.console_print(message, 'bold blue', 0, '*', escape_rich_markup)

    def success(self, message: any, escape_rich_markup=True):
        self.console_print(message, 'bold green', 0, '+', escape_rich_markup)

    def warning(self, message: any, escape_rich_markup=True):
        self.console_print(message, 'bold orange3', 0, '-', escape_rich_markup)

    def error(self, message: any, escape_rich_markup=True):
        self.console_print(message, 'bold red', 0, '!', escape_rich_markup)


def add_logger_arguments(parser: argparse.ArgumentParser) -> None:
    """Adds arguments to configure the logger from the command line.
    """
    parser.add_argument(
        '-v',
        '--verbose',
        dest='verbosity',
        action='count',
        default=0,
        help='verbosity level (-v for verbose, -vv for debug)',
    )
    parser.add_argument(
        '-q',
        '--quiet',
        dest='quiet',
        action='store_true',
        default=False,
        help='Show no information at all',
    )
    parser.add_argument(
        '--raw',
        action='store_true',
        default=False,
        help='Print without formatting the output'
    )
