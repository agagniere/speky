from unittest import TestCase

from speky import run as speky_run


class FirstTest(TestCase):
    def test_usage(self):
        with self.assertRaises(SystemExit):
            speky_run()

    def test_cmd(self):
        with self.assertRaises(OSError):
            speky_run(['unknown_file.yaml', '-p', 'project'])
