from __future__ import annotations
import shutil
import tabulate
import argparse

from madhac.app import App
from typing import Callable, Optional, TypeVar
from rich.console import Console
from rich.markup import escape
from typing_extensions import deprecated

CONSOLE = Console()


def add_tui_argument(parser: argparse.ArgumentParser) -> None:
    """Adds an argument to store properties from the command line.

    Useful to get properties as command line arguments.
    """
    parser.add_argument(
        '--visible-fields',
        help='Comma separated list of visible fields',
        metavar='LIST',
    )


T = TypeVar('T')
# A PossibleField can be either:
# - str: that is the field
# - tuple[str, str]: The first string is the original field name, and the second string is the desired (new) field name
# - tuple[str, Optional[str], Callable[[T], any]]: Same as before, but the second string can be None to keep the same field name, and the callable is a function that will be applied to the field value
PossibleField = str | tuple[str, str] | tuple[str, Optional[str], Callable[[T], any]]
PossibleFields = list[PossibleField]


def filter_fields(array: list[dict[str, T]], fields: PossibleFields, default=None) -> dict[str, any]:
    """Given a array of JSON objects, this function filters the fields available.
    If the field is a tuple, the first value is the filter and the second is the new value in the resulting array (useful to rename fields).
    If a selected field is not present in the object, the default value is put instead.
    You can also provide a third tuple value to apply a function that will be used on the field value.

    Example:
        The following dict:
        ```
        {
            "field1": "value1",
            "field2": "value2",
            "field3": "value3"
        }
        ```
        The fields parameter is:
        ```
        ['field1', ('field3', 'Field 3'), ('field2', 'field2', lambda v: 'toto')]
        ```
        Will result in the following dict:
        ```
        {
            "field1": "value1",
            "Field 3": "value3",
            "field2": "toto"
        }
        ```
    """
    def examine_field(obj: dict[str, any], field: PossibleField) -> tuple[str, any]:
        if isinstance(field, str):
            return (field, obj[field] or default)
        if len(field) == 2:
            return (field[1], obj[field[0]] or default)
        if field[0] in obj:
            return (field[1] or field[0], field[2](obj[field[0]]))
        return (field[1], default)
    return [
        {field[0]: field[1] for field in [examine_field(obj, field) for field in fields]}
        for obj in array
    ]


def print_dicts(app: App, data: list[dict], visible_fields: Optional[PossibleFields] = None, default=None, override=False, filter_function=filter_fields):
    """Nicely print data to the user.
    The data is a list of dict to display in a table.
    The visible_fields are which fields from the dict to show. If this parameter is not set, then all fields are considered visible.
    This is overwridden by the option --visible-fields
    If you don't want this behaviour, and only print the fields you want, set the override parameter to True.
    The default parameter is the default value to put if the chosen visible field doesn't exist in the dict.
    If write_output is set to True and the option --out is provided, then the visible fields are written to a JSON file.
    """
    if not override and app.options.visible_fields:
        visible_fields = app.options.visible_fields.split(',')
    if visible_fields is not None:
        data = filter_function(data, visible_fields, default=default)
    if not data:
        app.logger.warning('No data')
        return
    maxwidth = int(shutil.get_terminal_size().columns / len(data[0]))
    app.console.print(tabulate.tabulate(data, headers='keys', maxcolwidths=maxwidth), markup=False)


@deprecated('Use print_dicts instead')
def print_dict(app: App, data: list[dict], visible_fields: Optional[PossibleFields] = None, default=None, override=False, filter_function=filter_fields):
    """Nicely print data to the user.
    The data is a list of dict to display in a table.
    The visible_fields are which fields from the dict to show. If this parameter is not set, then all fields are considered visible.
    This is overwridden by the option --visible-fields
    If you don't want this behaviour, and only print the fields you want, set the override parameter to True.
    The default parameter is the default value to put if the chosen visible field doesn't exist in the dict.
    If write_output is set to True and the option --out is provided, then the visible fields are written to a JSON file.
    """
    return print_dicts(app, data, visible_fields, default, override, filter_function)


def prompt(msg: any, console=CONSOLE, highlight=True):
    console.print(f"[bold pink]\\[?][/bold pink] {escape(str(msg))} ", highlight=highlight)
    return input()


def prompt_yn(msg: any, default=True, console=CONSOLE, highlight=True):
    console.print(f"[bold pink]\\[?][/bold pink] {escape(str(msg))} ({'Y/n' if default else 'y/N'}) ", highlight=highlight)
    value = input()
    return value.lower() in ('y', 'yes') or (not value and default)


def prompt_with_default(msg: any, default: any, console=CONSOLE, highlight=True):
    console.print(f"[bold pink]\\[?][/bold pink] {escape(str(msg))} ({escape(str(default))}) ", highlight=highlight)
    value = input()
    return default if value == '' else value
