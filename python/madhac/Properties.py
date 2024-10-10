"""Management of the properties.

This module handles properties that can be used to modify the behaviour of the script.

The file `properties.json` should be used at the root of the project to store the properties of the
script.
"""
from __future__ import annotations

import json
import typing
import traceback

if typing.TYPE_CHECKING:
    import argparse


class Properties:
    """Handles the properties of the script.

    The properties are stored in a file `properties.json` located at the root of the project.
    """

    _instances = {}

    @staticmethod
    def instance(filename: str = 'properties.json') -> Properties:
        """Creates an instance of Properties.

        An instance is linked to its file. If you call multiple time the instance() method with the
        same filename, you'll obtain the exact instance.
        But if you call instance() with different filenames, then you'll obtain a different
        instance for each unique filename.
        """
        if filename not in Properties._instances:
            Properties._instances[filename] = Properties(filename)
        return Properties._instances[filename]

    def __init__(self, filename: str) -> None:
        """ Virutally private constructor.

        DO NOT INSTANTIATE THE PROPERTIES DIRECTLY: use `Properties.instance()` instead.
        """

        self.filename = filename
        self.save_required = False

        # Load property file
        self.properties = {}
        try:
            with open(filename) as fin:
                self.properties = json.load(fin)
        except FileNotFoundError:
            # Silently ignore missing file
            # print(f'File not found: {filename}')
            pass
        except Exception:
            print('Error openning properties')
            traceback.print_exc()

    def save(self) -> None:
        """Saves the current property data to the disk.
        """

        if self.save_required:
            try:
                with open(self.filename, 'w+') as fout:
                    json.dump(self.properties, fout)
                    self.save_required = False
            except Exception:
                print('Error saving properties')
                traceback.print_exc()

    def get(self, prop: str, default: typing.Any = None) -> typing.Any:
        """Gets the value of the specified property prop.

        The resolution of the value is made in the following order:
        1. Look for a property value passed by the command line (argparser)
        2. Look for a property value defined in the properties.json file
        3. Returns the default value passed to this function

        Arguments:
            prop {str} -- Name of the property to get

        Keyword Arguments:
            default {any} -- Default value to return if the specified property has no value set
            (default: {None})

        Returns:
            str|None -- Value of the property or `None` if the property is not present
        """
        # Use default value
        value = default
        # Access property by path
        if '/' in prop:
            keys = prop.split('/')
            props = self.properties
            for key in keys:
                if key not in props:
                    # Use default value
                    value = default
                    break

                if key == keys[-1]:
                    value = props[key]
                    break

                props = props[key]

        # Check if set by argparser
        elif prop in self.properties:
            value = self.properties[prop]

        # Use default value
        else:
            value = default

        # Return correct value
        if isinstance(default, bool) and isinstance(value, str):
            TRUTH = ['true', '1', 'yes']
            LIES = ['false', '0', 'no']
            if value.lower() in TRUTH:
                return True
            if value.lower() in LIES:
                return False
        return value

    def need(self, prop: str) -> typing.Any:
        """Gets the value of the specified property prop.

        The resolution of the value is made in the following order:
        1. Look for a property value passed by the command line (argparser)
        2. Look for a property value defined in the properties.json file

        Unlike the `get` method, this method raises a ValueError if the property is not present.

        Arguments:
            prop {str} -- Name of the property to get

        Returns:
            Value of the property or raises ValueError if the property is not present.
        """
        val = self.get(prop, None)
        if val is None:
            raise ValueError(f'Missing property "{prop}" value.')
        return val

    def set_prop(self, prop: str, value: typing.Any) -> None:
        """Changes the value of the specified property.

        If it is required to remove this property completely, then pass `None` as a value instead
        of a string

        Arguments:
            prop {str} -- Name of the property to set
            value {str|None} -- Value of the property or `None` if the property should be removed
        """
        def set_nest(tree, prop):
            if '/' in prop:
                # Nested property
                keys = prop.split('/')
                key = keys[0]
                if key not in tree:
                    tree[key] = {}
                set_nest(tree[key], '/'.join(keys[1:]))
            else:
                # Leaf property
                if value:
                    # Set value
                    tree[prop] = value
                    self.save_required = True
                elif prop in tree:
                    # Delete property
                    del tree[prop]
                    self.save_required = True

        set_nest(self.properties, prop)

    def is_set(self, prop: str) -> bool:
        """Checks if the specified property has a value

        Arguments:
            prop {str} -- Name of the property to get

        Returns:
            bool -- TRUE if the property has a value and FALSE otherwise
        """
        return prop in self.properties

    def parse_arguments(self, args: argparse.Namespace) -> None:
        """Parses the arguments of the argparser to get the properties that have been set.
        """
        if args.prop:
            for prop in args.prop:
                if '/' in prop[0]:
                    keys = prop[0].split('/')
                    props = self.properties
                    for key in keys:
                        if key == keys[-1]:
                            props[key] = prop[1]
                        else:
                            if key not in props:
                                props[key] = {}
                            props = props[key]
                else:
                    self.properties[prop[0]] = prop[1]


def add_property_argument(parser: argparse.ArgumentParser) -> None:
    """Adds an argument to store properties from the command line.

    Useful to get properties as command line arguments.
    """
    parser.add_argument(
        '--prop',
        nargs=2,
        action='append',
        help='Set a property manually (this overrides the properties.json file)',
        metavar=('PROPERTY', 'VALUE')
    )
