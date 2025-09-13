import pytest

from speky import run as speky_run


def test_usage(capfd):
    with pytest.raises(SystemExit):
        speky_run()
    err_msg = capfd.readouterr().err
    assert err_msg.startswith('usage')


def test_missing_file(capfd):
    with pytest.raises(FileNotFoundError):
        speky_run(['-p', 'project', 'missing_file.yaml'])
