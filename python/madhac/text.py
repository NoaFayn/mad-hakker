"""Module to provide support for text operations.
"""


def pluralise(number, singular='', plural='s'):
    """Returns the correct plural form for the specified number.

    Args:
        number (int): Number to check
        singular (str, optional): Singular form. Defaults to ''.
        plural (str, optional): Plural form. Defaults to 's'.

    Returns:
        str: Correct plural form depending on the given number
    """
    if number <= 1:
        return singular
    return plural
