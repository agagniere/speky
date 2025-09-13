import pytest


@pytest.fixture(scope='session')
def sample():
    """
    Fixture to get the path of a sample from its name
    (they are files inside samples/)
    """
    # TODO check if the file exists and look for absolute path?
    return lambda s: 'tests/samples/' + s + '.yaml'
