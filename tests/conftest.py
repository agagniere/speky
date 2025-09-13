import pytest


@pytest.fixture(scope='session')
def sample():
    """
    Fixture to get the path of a sample from its name
    (they are files inside samples/)
    """
    # TODO
    # - check if the file exists
    # - build the path from the location of this file
    # - test at the end if files in sample are not used
    return lambda s: 'tests/samples/' + s + '.yaml'
