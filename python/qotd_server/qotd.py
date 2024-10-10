#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @created: 23 Nov 2022
import madhac.app as mapp
import typing
import socketserver as ss
import random


class Server(ss.TCPServer):
    """TCP server subclass to give access to the app.
    """
    def __init__(self, server_address, rhc, app: 'QotdApp') -> None:
        super().__init__(server_address, rhc)
        self.app = app


class Handler(ss.BaseRequestHandler):
    def handle(self) -> None:
        serv = typing.cast(Server, self.server)
        app = serv.app
        logger = serv.app.logger
        logger.info(f'Received request from {self.client_address}')
        self.request.sendall(app.get_quote().encode('utf-8'))


class QotdApp(mapp.App):
    def main(self):
        serv = Server((self.options.address, self.options.port), Handler, self)
        with serv as server:
            server.serve_forever()

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


if __name__ == "__main__":
    app = QotdApp(
        app_name='QotD server',
        app_description='This script spaws a QOTD (Quote of the Day) server',
        app_version='1.0.0',
    )
    parser = app.get_parser()
    parser.add_argument(
        '--address',
        default='0.0.0.0',
        type=str,
        help='Address to listen to',
    )
    parser.add_argument(
        '-p',
        '--port',
        default=17,
        type=int,
        help='Port to listen to',
    )
    app.start()
