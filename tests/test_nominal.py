import pytest
import speky


def test_usage(capfd):
    with pytest.raises(SystemExit):
        speky.run()
    err_msg = capfd.readouterr().err
    assert err_msg.startswith('usage')


def test_simple_sample(sample):
    speky.run(
        [
            '--check-only',
            sample('simple_requirements'),
            sample('simple_comments'),
            sample('simple_tests'),
        ]
    )


# The manifest loads all samples
def test_more_samples(sample):
    speky.run(['--check-only', sample('more_samples')])
