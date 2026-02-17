"""Utility functions for Speky specification processing."""

import logging

logger = logging.getLogger(__name__)


def import_fields(destination, source: dict, fields: list[str]):
    """
    Creates members to the destination objects, that have the name and values
    of the desired fields from the source dictionary.
    """
    for field in fields:
        setattr(destination, field, source.get(field, None))


def warn_extra_fields(location: str, obj: dict, expected_fields: list[str]):
    """Warn about unexpected fields in the input data."""
    extras = obj.keys() - set(expected_fields)
    if extras:
        s = 's' if len(extras) > 1 else ''
        logger.warning('Found extra field%s in %s: %s', s, location, extras)


def ensure_fields(location: str, obj: dict, fields: list[str]):
    """
    Raise an exception if one of the expected fields is missing.

    Raises:
        KeyError: If any required field is missing
    """
    missing = set(fields) - obj.keys()
    if missing:
        if len(missing) > 1:
            message = f'Missing fields from {location}: {", ".join(sorted(missing))}'
        else:
            message = f'Missing field from {location}: {next(iter(missing))}'
        raise KeyError(message)
