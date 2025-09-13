import pytest
import speky


def test_usage(capfd):
    with pytest.raises(SystemExit):
        speky.run()
    err_msg = capfd.readouterr().err
    assert err_msg.startswith('usage')


def test_simple_sample(sample):
    speky.run(['-p', 'project', sample('simple_requirements'), sample('simple_comments'), sample('simple_tests')])
