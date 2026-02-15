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
            '-p',
            'project',
            sample('simple_requirements'),
            sample('simple_comments'),
            sample('simple_tests'),
        ]
    )


def test_more_samples(sample):
    speky.run(
        [
            '--check-only',
            '--project-name',
            'Project',
            sample('simple_requirements'),
            sample('simple_comments'),
            sample('simple_tests'),
            sample('more_requirements'),
            sample('more_comments'),
            sample('more_tests'),
        ]
    )
