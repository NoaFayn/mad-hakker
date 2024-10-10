# -*- coding: utf-8 -*-
import argparse
import random
import socket

from prettytable import PrettyTable
from rich.console import Console

from madhac.Logger import Logger, add_logger_arguments
from madhac.Properties import Properties, add_property_argument

# Property
properties = Properties.instance()

PROP_QOTD_SERVER = 'qotd.server'
PROP_QOTD_TIMEOUT = 'qotd.timeout'
DEFAULT_QOTD_TIMEOUT = 1


# Decorator to mark an App function as action for the user
def UserAction(func):
    func.madhac_action = 'user'
    return func


class App:
    def __init__(self, app_name='Awesome app', app_description='Awesome script', app_author='Mad Hakker', app_version='1.0.0') -> None:
        self.name = app_name
        self.version = app_version
        self.author = app_author
        # Banner
        self.banner = f'~ {self.name} v{self.version} by {self.author}'
        # Registered properties for this app
        self.props = dict()
        # Description
        description = app_description
        user_actions = [func for func in self.__class__.__dict__.values() if hasattr(func, 'madhac_action')]
        self.has_user_actions = bool(user_actions)
        if self.has_user_actions:
            description += '\n\navailable actions:\n'
            actions_table = PrettyTable()
            actions_table.align = 'l'
            actions_table.header = False
            actions_table.border = False
            actions_table.add_rows([(f'  {func.__name__}', str(func.__doc__.strip()) if func.__doc__ else '') for func in user_actions])
            description += str(actions_table)
        # Option parser
        self.parser = argparse.ArgumentParser(
            description=description,
            formatter_class=argparse.RawTextHelpFormatter,
        )
        add_property_argument(self.parser)
        add_logger_arguments(self.parser)
        if self.has_user_actions:
            self.parser.add_argument(
                'action',
                help='Action to perform',
            )

    def register_property(self, prop: str, desc: str):
        """Registers a property. This is used to display a useful help message to the user.

        All properties must be registered before calling the parse_options() method.
        """
        self.props[prop] = {
            'desc': desc,
        }

    def get_quote(self):
        # Try to connect to QOTD server if provided
        qotd_url = properties.get(PROP_QOTD_SERVER)
        qotd_timeout = properties.get(PROP_QOTD_TIMEOUT, DEFAULT_QOTD_TIMEOUT)
        if qotd_url:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(qotd_timeout)
                    s.connect((qotd_url, 17))
                    return s.recv(1024).decode('utf-8')
            except Exception:
                pass

        # Default local quote
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
        pass

    def init(self):
        """Init function executed before the user action and the main function.
        """
        pass

    def start(self):
        """Starts the app.
        """
        print(self.banner)
        # Command line arguments
        self.options = self.parse_options()
        properties.parse_arguments(self.options)

        self.console = Console()
        self.logger = Logger(self.console, self.options.verbosity, self.options.quiet, self.options.raw)

        if not self.options.raw:
            print(f'  ~{self.get_quote()}', end='\n\n')
        try:
            self.init()
            # Run user action if set
            if self.has_user_actions:
                action = getattr(self, self.options.action)
                action()
            self.main()
        except KeyboardInterrupt:
            self.logger.info('Terminating script...')
            raise SystemExit
