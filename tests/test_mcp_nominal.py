from unittest.mock import patch

import speky_mcp.server


def test_simple_sample(sample):
    with patch('speky_mcp.server.run_server'):
        speky_mcp.server.run(
            [
                sample('simple_requirements'),
                sample('simple_comments'),
                sample('simple_tests'),
            ]
        )


def test_more_samples(sample):
    with patch('speky_mcp.server.run_server'):
        speky_mcp.server.run(
            [
                sample('simple_requirements'),
                sample('simple_comments'),
                sample('simple_tests'),
                sample('more_requirements'),
                sample('more_comments'),
                sample('more_tests'),
            ]
        )
