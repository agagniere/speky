import pytest

import speky


def test_usage(capfd):
    with pytest.raises(SystemExit):
        speky.run()
    err_msg = capfd.readouterr().err
    assert err_msg.startswith('usage')


def test_missing_file(capfd):
    with pytest.raises(FileNotFoundError):
        speky.run(['-p', 'project', 'missing_file.yaml'])
