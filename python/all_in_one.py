# -*- coding: utf-8 -*-
import argparse
import random

from prettytable import PrettyTable
from rich.console import Console


class Logger(object):
    def __init__(self, console, verbosity=0, quiet=False, raw=False):
        self.console = console
        self.verbosity = verbosity
        self.quiet = quiet
        self.raw = raw

    def debug(self, message):
        if self.verbosity >= 2:
            if self.raw:
                self.console.print(message)
            else:
                self.console.print("{}[DEBUG]{} {}".format("[yellow3]", "[/yellow3]", message), highlight=False)

    def verbose(self, message):
        if self.verbosity >= 1:
            if self.raw:
                self.console.print(message)
            else:
                self.console.print("{}[VERBOSE]{} {}".format("[blue]", "[/blue]", message), highlight=False)

    def info(self, message):
        if not self.quiet:
            if self.raw:
                self.console.print(message)
            else:
                self.console.print("{}[*]{} {}".format("[bold blue]", "[/bold blue]", message), highlight=False)

    def success(self, message):
        if not self.quiet:
            if self.raw:
                self.console.print(message)
            else:
                self.console.print("{}[+]{} {}".format("[bold green]", "[/bold green]", message), highlight=False)

    def warning(self, message):
        if not self.quiet:
            if self.raw:
                self.console.print(message)
            else:
                self.console.print("{}[-]{} {}".format("[bold orange3]", "[/bold orange3]", message), highlight=False)

    def error(self, message):
        if not self.quiet:
            if self.raw:
                self.console.print(message)
            else:
                self.console.print("{}[!]{} {}".format("[bold red]", "[/bold red]", message), highlight=False)


class App:
    def __init__(self, app_name='Awesome app', app_description='Awesome script', app_author='Mad Hakker', app_version='1.0.0') -> None:
        self.name = app_name
        self.version = app_version
        self.author = app_author
        # Banner
        self.banner = f'~ {self.name} v{self.version} by {self.author}\n'
        # Registered properties for this app
        self.props = dict()
        # Option parser
        self.parser = argparse.ArgumentParser(
            description=app_description,
            formatter_class=argparse.RawTextHelpFormatter,
        )
        self.parser.add_argument(
            '-v',
            '--verbose',
            dest='verbosity',
            action='count',
            default=0,
            help='verbosity level (-v for verbose, -vv for debug)',
        )
        self.parser.add_argument(
            '-q',
            '--quiet',
            dest='quiet',
            action='store_true',
            default=False,
            help='Show no information at all',
        )
        self.parser.add_argument(
            '--raw',
            action='store_true',
            default=False,
            help='Print without formatting the output'
        )

    def register_property(self, prop: str, desc: str):
        """Registers a property. This is used to display a useful help message to the user.

        All properties must be registered before calling the parse_options() method.
        """
        self.props[prop] = {
            'desc': desc,
        }

    def get_quote(self):
        quotes = [
            'It\'s no use going back to yesterday, because I was a different person then.',
            'We\'re all mad here.',
            'Curiouser and curiouser!',
            'I don\'t think -- " "Then you shouldn\'t talk.',
            'Not all who wander are lost.',
            'I am not crazy; my reality is just different from yours.',
        ]
        return random.choice(quotes)

    def get_parser(self):
        return self.parser

    def parse_options(self):
        if self.props:
            pt = PrettyTable()
            pt.align = 'l'
            pt.header = False
            pt.border = False
            pt.add_rows([(f'  {prop}', self.props[prop]['desc']) for prop in self.props])
            self.parser.epilog = f'available properties:\n{pt}'
        return self.parser.parse_args()

    def main(self):
        """Main function. Override it."""
        self.logger.info('Override main function')

    def start(self):
        """Starts the app.
        """
        print(self.banner)
        # Command line arguments
        self.options = self.parse_options()

        self.console = Console()
        self.logger = Logger(self.console, self.options.verbosity, self.options.quiet, self.options.raw)

        if not self.options.raw:
            self.logger.info(self.get_quote())
        try:
            self.main()
        except KeyboardInterrupt:
            self.logger.info('Terminating script...')
            raise SystemExit


if __name__ == "__main__":
    app = App()
    app.start()
