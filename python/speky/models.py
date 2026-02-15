"""Data models for Speky requirements, tests, and comments."""

import datetime
from types import SimpleNamespace

from .utils import ensure_fields, import_fields, warn_extra_fields


class SpecItem(SimpleNamespace):
    """Base class for specification items (requirements and tests)."""

    folder = 'misc'
    id_field = 'id'
    mandatory_fields = ['long']
    optional_fields = ['short']

    @classmethod
    def fields(cls):
        """Return all fields (id + mandatory + optional)."""
        return [cls.id_field] + cls.mandatory_fields + cls.optional_fields

    @classmethod
    def from_yaml(cls, data: dict, location: str):
        """
        Create a SpecItem from YAML data.

        Args:
            data: Dictionary from YAML
            location: Source file path for error messages

        Returns:
            Instance of the class

        Raises:
            KeyError: If required fields are missing
        """
        result = SimpleNamespace()
        ensure_fields(f'Definition of a {cls.__name__} in "{location}"', data, [cls.id_field])
        location = f'Definition of {cls.__name__} {data[cls.id_field]} in "{location}"'
        ensure_fields(location, data, cls.mandatory_fields)
        warn_extra_fields(location, data, cls.fields())
        import_fields(result, data, cls.fields())
        return cls(**result.__dict__)

    @property
    def title(self):
        """Return formatted title with ID and optional short description."""
        return f'`{self.id}` {self.short}' if self.short else f'`{self.id}`'

    def __lt__(self, other):
        """Compare by ID field for sorting."""
        return getattr(self, self.id_field) < getattr(other, other.id_field)


class Requirement(SpecItem):
    """Requirement specification item."""

    folder = 'requirements'
    optional_fields = SpecItem.optional_fields + ['tags', 'client_statement', 'properties', 'ref']


class Test(SpecItem):
    """Test specification item."""

    folder = 'tests'
    mandatory_fields = SpecItem.mandatory_fields + ['ref', 'steps']
    optional_fields = SpecItem.optional_fields + ['initial', 'prereq']

    step_fields = {'action', 'run', 'expected', 'sample', 'sample_lang'}

    @classmethod
    def from_yaml(cls, data: dict, location: str):
        """
        Create a Test from YAML data, validating step structure.

        Args:
            data: Dictionary from YAML
            location: Source file path for error messages

        Returns:
            Test instance

        Raises:
            KeyError: If required fields are missing
        """
        result = super().from_yaml(data, location)
        for i, step in enumerate(result.steps, 1):
            name = f'Step {i} of {cls.__name__} {data[cls.id_field]} in "{location}"'
            ensure_fields(name, step, ['action'])
            warn_extra_fields(name, step, cls.step_fields)
        return result


class Comment(SimpleNamespace):
    """Comment on a requirement or test."""

    fields = ['about', 'from', 'date', 'text', 'external']

    @classmethod
    def from_yaml(cls, data: dict, location: str):
        """
        Create a Comment from YAML data.

        Args:
            data: Dictionary from YAML
            location: Source file path for error messages

        Returns:
            Comment instance

        Raises:
            KeyError: If required fields are missing
        """
        result = SimpleNamespace()
        location = f'Definition of a {cls.__name__} in "{location}"'
        ensure_fields(location, data, cls.fields)
        warn_extra_fields(location, data, cls.fields)
        import_fields(result, data, cls.fields)
        result.external = result.external in ['True', 'true', True, 1, '1']
        result.time = datetime.datetime.strptime(result.date, '%d/%m/%Y').astimezone(datetime.UTC)
        return cls(**result.__dict__)

    def __lt__(self, other):
        """Compare by timestamp for chronological sorting."""
        return self.time < other.time
