import pytest
import speky
import yaml


def test_invalid_file(tests_folder):
    with pytest.raises(FileNotFoundError):
        speky.run(['-p', 'project', 'doesntexist'])
    with pytest.raises(OSError, match='File name too long'):
        speky.run(['-p', 'project', 'ToooOOOoooOOOLLllLllooOOoOOoOooOOnnnNnnNGGGgGgggG' * 32])
    with pytest.raises(NotADirectoryError):
        speky.run(['-p', 'project', str(tests_folder / 'conftest.py' / 'foo.yaml')])
    with pytest.raises(yaml.reader.ReaderError):
        speky.run(['-p', 'project', '/dev/zero'])
    with pytest.raises(RuntimeError, match='Empty file'):
        speky.run(['-p', 'project', '/dev/null'])


def test_error_msg(sample):
    error_list = [
        ('com_missing_about', 'Missing field from Definition of a Comment in "[^"]+": about'),
        ('com_missing_date', 'Missing field from Definition of a Comment in "[^"]+": date'),
        ('com_missing_from', 'Missing field from Definition of a Comment in "[^"]+": from'),
        ('com_missing_text', 'Missing field from Definition of a Comment in "[^"]+": text'),
        ('com_missing_3_fields', 'Missing fields from Definition of a Comment in "[^"]+": about, date, from'),
        ('com_unknown_ref', r'Requirement or Test \w+, referred from a comment, does not exist'),
        ('missing_kind', 'Missing field from Top-level of "[^"]+": kind'),
        ('req_missing_category', 'Missing field from Top-level of requirements file "[^"]+": category'),
        ('req_missing_id', 'Missing field from Definition of a Requirement in "[^"]+": id'),
        ('req_missing_long', r'Missing field from Definition of Requirement \w+ in "[^"]+": long'),
        ('req_redefinition', r'Multiple definitions of requirement "\w+"'),
        ('req_unknown_ref', r'Requirement \w+, referred from \w+, does not exist'),
        ('test_missing_ref', r'Missing field from Definition of Test \w+ in "[^"]+": ref'),
        ('test_missing_steps', r'Missing field from Definition of Test \w+ in "[^"]+": steps'),
        ('test_missing_ref_and_steps', r'Missing fields from Definition of Test \w+ in [^:]+: ref, steps'),
        ('test_unknwon_ref', r'Requirement \w+, referred from \w+, does not exist'),
        ('test_step_missing_action', r'Missing field from Step \d+ of Test \w+ in "[^"]+": action'),
    ]

    for name, reason in error_list:
        with pytest.raises(KeyError, match=reason):
            speky.run(['-p', 'project', sample(name)])
