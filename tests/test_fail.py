import pytest
import speky
import yaml


def test_invalid_file():
    with pytest.raises(FileNotFoundError):
        speky.run(['-p', 'project', 'doesntexist'])
    with pytest.raises(OSError, match='File name too long'):
        speky.run(['-p', 'project', 'ToooOOOoooOOOLLllLllooOOoOOoOooOOnnnNnnNGGGgGgggG' * 32])
    with pytest.raises(NotADirectoryError):
        speky.run(['-p', 'project', 'LICENSE/foo.yaml'])
    with pytest.raises(yaml.reader.ReaderError):
        speky.run(['-p', 'project', '/dev/zero'])
    with pytest.raises(RuntimeError, match='Empty file'):
        speky.run(['-p', 'project', '/dev/null'])


def test_error_msg(capfd, sample):
    error_list = [
        ('com_missing_about', 'Missing the field "about" from Definition of a Comment'),
        ('com_missing_date', 'Missing the field "date" from Definition of a Comment'),
        ('com_missing_from', 'Missing the field "from" from Definition of a Comment'),
        ('com_missing_text', 'Missing the field "text" from Definition of a Comment'),
        ('com_unknown_ref', 'Requirement RF00, referred from a comment, does not exist'),
        ('missing_kind', 'Missing the field "kind" from Top-level of "[^.]+.yaml"'),
        ('req_missing_category', 'Missing the field "category" from Top-level of requirements file "[^.]+.yaml"'),
        ('req_missing_id', 'Missing the field "id" from Definition of a Requirement'),
        ('req_missing_long', r'Missing the field "long" from Definition of Requirement \w+'),
        ('req_redefinition', 'Multiple definitions of requirement "RF01"'),
        ('req_unknown_ref', 'Requirement RF00, referred from RF01, does not exist'),
        ('test_missing_ref', r'Missing the field "ref" from Definition of Test \w+'),
        ('test_missing_steps', r'Missing the field "steps" from Definition of Test \w+'),
        ('test_unknwon_ref', r'Requirement RF00, referred from \w+, does not exist'),
    ]

    for name, reason in error_list:
        with pytest.raises(KeyError, match=reason):
            speky.run(['-p', 'project', sample(name)])
