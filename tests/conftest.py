import importlib.resources

import pytest


@pytest.fixture(scope='package')
def tests_folder():
    return importlib.resources.files(__package__)


@pytest.fixture(scope='package')
def sample(tests_folder):
    """
    Fixture to get the path of a sample from its name
    (they are files inside samples/ or failing_samples/)
    """

    def get_path(name) -> str:
        for subdir in ['samples', 'failing_samples']:
            path = tests_folder / subdir / (name + '.yaml')
            if path.is_file():
                return str(path)
        message = f'Sample {name} not found'
        raise FileNotFoundError(message)

    return get_path
