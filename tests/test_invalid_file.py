import pytest

import speky


def test_ref_field(sample):
    with pytest.raises(KeyError):
        speky.run(['-p', 'project', sample('unknown_ref')])
