import pytest

import speky


@pytest.mark.xfail(raises=KeyError)
def test_ref_field(sample):
    speky.run(['-p', 'project', sample('requirement_ref')])


@pytest.mark.xfail(reason='A comment referencing an unknown req/test should not be ignored')
def test_long_with_trailing_whitespace(sample):
    with pytest.raises(SystemExit):
        speky.run(['-p', 'project', sample('comment_about')])
