# -*- coding: utf-8 -*-
import madhac.app as mapp
import json
import traceback
import ipaddress
import requests

from typing import Union


class UnsupportedFormat(Exception):
    """Raised when the format is not supported.
    """
    def __init__(self, format='', *args: object) -> None:
        super().__init__(*args)
        self.message = f'Unsupported format: {format}'


class Whitelist:
    def __init__(self) -> None:
        self.whitelist = []

    @staticmethod
    def load_from_properties():
        whitelist = Whitelist()
        whitelist.whitelist = mapp.properties.get('ipfilter.whitelisted', [])
        # Convert all string cidr to ip_network objects
        for elt in whitelist.whitelist:  # type: ignore
            elt['net'] = list(map(lambda ipnet: ipaddress.ip_network(ipnet), elt['net']))
        return whitelist

    @staticmethod
    def load_from_file(filename: str):
        whitelist = Whitelist()
        with open(filename, 'r') as fin:
            whitelist.whitelist = json.load(fin)
        # Convert all string cidr to ip_network objects
        for elt in whitelist.whitelist:
            elt['net'] = list(map(lambda ipnet: ipaddress.ip_network(ipnet), elt['net']))
        return whitelist

    def is_whitelisted(self, address: Union[ipaddress.IPv4Address, ipaddress.IPv6Address]):
        """Checks if the address is whitelisted.

        Returns TRUE if the address is whitelisted, FALSE otherwise.
        """
        for elt in self.whitelist:
            for net in elt['net']:
                if address in net:
                    return True
        return False

    def filter(self, ip_addresses: list[ipaddress.IPv4Address]):
        """Given a list of IP addresses, returns only the ones that are not whitelisted by this Whitelist.
        """
        return [ip for ip in ip_addresses if not self.is_whitelisted(ip)]


class WhoisLookupItem:
    """Whois lookup item result.
    """
    def __init__(self, ip: ipaddress.IPv4Address, response) -> None:
        self.ip = ip
        self.response = response

    def to_json(self):
        return {
            'ip': str(self.ip),
            'response': self.response,
        }


class State:
    def __init__(self, options: mapp.argparse.Namespace, logger: mapp.Logger) -> None:
        # List of IPs to work with
        self.ips = []  # type: list[ipaddress.IPv4Address]
        # List of IPs filtered
        self.ips_whitelisted = []  # type: list[ipaddress.IPv4Address]
        # Whois lookup results
        self.lookup = []  # type: list[WhoisLookupItem]
        # Script options
        self.options = options
        # Logger
        self.logger = logger
        # Whitelist
        self.whitelist = None

    def parse_input(self):
        """Parses the input file.

        Updates the current state.
        If no input file is provided, then this method does nothing.

        Raises:
            UnsupportedFormat
        """
        # Ignore if no input
        if not self.options.input:
            return

        with open(self.options.input, 'r') as fin:
            if self.options.inform == 'json-aws':
                try:
                    data = json.load(fin)
                    self.ips = [ipaddress.IPv4Address(elt['dstAddr']) for elt in data]
                except Exception:
                    traceback.print_exc()
                    raise UnsupportedFormat()
            elif self.options.inform == 'json-whois':
                try:
                    data = json.load(fin)
                    self.ips = [ipaddress.IPv4Address(elt['ip']) for elt in data]
                except Exception:
                    traceback.print_exc()
                    raise UnsupportedFormat()
            else:
                raise UnsupportedFormat(self.options.inform)

    def parse_filter(self):
        """Parses the provided IP whitelist.

        Filters all IPs that are whitelisted.

        Updates the current state.
        """
        # Ignore if no whitelist provided
        if not self.options.whitelist:
            return

        self.whitelist = Whitelist.load_from_file(self.options.whitelist)

        # Remove all IPs that are whitelisted
        self.ips_whitelisted = [ip for ip in self.ips if self.whitelist.is_whitelisted(ip)]
        self.ips = [ip for ip in self.ips if ip not in self.ips_whitelisted]

    def has_lookup(self):
        """Returns TRUE if there is at least one whois lookup result.
        """
        return bool(self.lookup)

    def has_ip(self):
        """Returns TRUE if there is at least one IP address.
        """
        return bool(self.ips)

    def whois_lookup(self):
        """Performs a whois lookup for each IP loaded and appends the result to the lookup results.

        Updates the current state.
        """
        for ip in self.ips:
            res = requests.api.get(f'http://whois.arin.net/rest/ip/{str(ip)}', headers={
                'Accept': 'application/json'
            })
            res.raise_for_status()
            content = res.json()
            self.lookup.append(WhoisLookupItem(ip, content))

    def print_lookup(self):
        """Prints the whois lookup results in the logger.
        """
        for elt in self.lookup:
            if 'net' not in elt.response:
                self.logger.error(f'{str(elt.ip)}: Missing "net" object: {str(elt.response)}')
                continue
            if 'orgRef' not in elt.response['net']:
                self.logger.error(f'{str(elt.ip)}: Missing "orgRef" object: {str(elt.response["net"])}')
                continue
            if '@name' not in elt.response['net']['orgRef']:
                self.logger.error(f'{str(elt.ip)}: Missing "@name" object: {str(elt.response["net"]["orgRef"])}')
                continue
            self.logger.info(f'{str(elt.ip)}\t{elt.response["net"]["orgRef"]["@name"]}')

    def save_lookup(self):
        """Saves the whois lookup results at the designated output.
        """
        # Ignore if no output
        if not self.options.output:
            return

        with open(self.options.output, 'w') as fout:
            if self.options.outform == 'json':
                data = [item.to_json() for item in self.lookup]
                json.dump(data, fout)
            else:
                raise UnsupportedFormat(self.options.outform)

    def print_ips(self):
        """Prints the IPs in the logger.
        """
        for ip in self.ips:
            self.logger.info(str(ip))

    def save_ips(self):
        """Saves the IPs at the designated output.
        """
        # Ignore if no output file
        if not self.options.output:
            return

        data = [str(ip) for ip in self.ips]
        with open(self.options.output, 'w') as fout:
            if self.options.outform == 'json':
                json.dump(data, fout)
            elif self.options.outform == 'txt':
                fout.write('\n'.join(data))
            else:
                raise UnsupportedFormat(self.options.outform)

    def print_stats(self):
        """Prints the stats about current state.
        """
        nb_ips_loaded = len(self.ips) + len(self.ips_whitelisted)
        self.logger.info(f'#IP loaded: [{nb_ips_loaded}]')
        self.logger.info(f'#IP: [{len(self.ips)}]')
        self.logger.info(f'#IP whitelisted: [{len(self.ips_whitelisted)}]')
        percent_whitelisted = round(len(self.ips_whitelisted) / nb_ips_loaded * 100)
        self.logger.info(f'%IP whitelisted: [{percent_whitelisted}]')
        percent_remaining = round(len(self.ips) / nb_ips_loaded * 100)
        self.logger.info(f'%IP: [{percent_remaining}]')


INPUT_FORMATS = {
    'json-aws': {
        'name': 'JSON',
        'description': 'JSON format of IPs generated by CloudWatch',
    },
    'json-whois': {
        'name': 'JSON Whois lookup',
        'description': 'JSON format containing whois lookup',
    }
}
OUTPUT_FORMATS = {
    'json': {
        'name': 'JSON',
        'description': 'JSON format',
    },
    'txt': {
        'name': 'txt',
        'description': 'Text output',
    }
}


def print_list_input_formats(logger: mapp.Logger):
    """Prints the list of available input formats.
    """
    for format in INPUT_FORMATS:
        logger.info(f'{format: INPUT_FORMATS[format]["description"]}')


def print_list_output_formats(logger: mapp.Logger):
    """Prints the list of available output formats.
    """
    for format in OUTPUT_FORMATS:
        logger.info(f'{format: OUTPUT_FORMATS[format]["description"]}')


def main(options, logger, console):
    state = State(options, logger)
    # List input formats
    if options.list_inform:
        print_list_input_formats(logger)
        return  # do not do anything else
    if options.list_outform:
        print_list_output_formats(logger)
        return  # do not do anything else

    # Load input
    state.parse_input()
    state.parse_filter()

    # Whois lookup
    if options.whois:
        # Check if lookup already performed
        if state.has_lookup():
            # No need to perform the whois lookup, just use the provided results
            pass
        else:
            # Perform whois lookup
            state.whois_lookup()

        # Output result
        if not options.notext:
            state.print_lookup()
        state.save_lookup()

    # Print IPs
    if options.list:
        # Output result
        if not options.notext:
            state.print_ips()
        state.save_ips()

    # Stats
    if options.stats:
        if not options.notext:
            state.print_stats()


if __name__ == "__main__":
    app = mapp.App(app_description='This script flag suspicious IP addresses from a list. It is based on AbuseIPDB website.')
    parser = app.get_parser()
    parser.add_argument(
        '-i',
        '--input',
        '--in',
        help='Input file containing the IP addresses to analyse'
    )
    parser.add_argument(
        '-o',
        '--output',
        '--out',
        help='Output file'
    )
    parser.add_argument(
        '--inform',
        default='json-aws',
        help='Specify the format of the input file. Use --list-inform to list the accepted formats',
    )
    parser.add_argument(
        '--list-inform',
        action='store_true',
        help='Lists the accepted input formats',
    )
    parser.add_argument(
        '--outform',
        default='stdout',
        help='Specify the format for the output. Use --list-outform to list the accepted formats',
    )
    parser.add_argument(
        '--list-outform',
        action='store_true',
        help='Lists the accepted output formats',
    )
    parser.add_argument(
        '--whitelist',
        help='Filter IP addresses with specified whitelist',
    )
    parser.add_argument(
        '--notext',
        action='store_true',
        help='Do not print to stdout',
    )
    parser.add_argument(
        '--load',
        help='File to load',
    )

    action_group = parser.add_mutually_exclusive_group()
    action_group.add_argument(
        '--whois',
        action='store_true',
        help='Perform whois lookup on given IPs',
    )
    action_group.add_argument(
        '--list',
        action='store_true',
        help='List resulting IP addresses',
    )
    action_group.add_argument(
        '--stats',
        action='store_true',
        help='Calculates stats about IP addresses and filters',
    )
    app.init(main)
