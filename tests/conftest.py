import importlib.resources

import pytest

tests = importlib.resources.files(__package__)


@pytest.fixture(scope='session')
def sample():
    """
    Fixture to get the path of a sample from its name
    (they are files inside samples/ or failing_samples/)
    """

    def get_path(name) -> str:
        for subdir in ['samples', 'failing_samples']:
            path = tests / subdir / (name + '.yaml')
            if path.is_file():
                return str(path)
        message = f'Sample {name} not found in {tests}'
        raise FileNotFoundError(message)

    return get_path
