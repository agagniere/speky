import pytest
import speky


@pytest.mark.xfail(raises=FileNotFoundError)
def test_missing_file():
    speky.run(['-p', 'project', 'doesntexiste'])


def test_error_msg(capfd, sample):
    error_list = [
        ('com_missing_about', 'about'),
        ('com_missing_date', 'date'),
        ('com_missing_from', 'from'),
        ('com_missing_text', 'text'),
        ('com_unknown_ref', 'ref'),
        ('missing_kind', 'kind'),
        ('req_missing_category', 'category'),
        ('req_missing_id', 'id'),
        ('req_missing_long', 'long'),
        ('req_redefinition', 'RF01'),
        ('req_unknown_ref', 'RF00'),
        ('test_missing_ref', 'ref'),
        ('test_missing_steps', 'steps'),
        ('test_unknwon_ref', 'ref'),
    ]

    for name, reason in error_list:
        with pytest.raises(SystemExit):
            speky.run(['-p', 'project', sample(name)])
        err_msg = capfd.readouterr().err
        assert reason in err_msg
