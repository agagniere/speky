from os.path import isfile

import pytest


@pytest.fixture(scope='session')
def sample():
    """
    Fixture to get the path of a sample from its name
    (they are files inside samples/)
    """

    def get_path(name):
        for d in ['tests/samples/', 'tests/failing_samples/']:
            f = d + name + '.yaml'
            if isfile(f):
                return f
        print(f'sample("{name}") file not found')
        exit(1)

    return get_path
