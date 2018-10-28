import os
import sys
import subprocess
import pytest


def test_mypy():
    """Run mypy and fail test if there are typing errors.

    We don't want to run this test on CI, because there it is included in the
    configuration. A crude check skips this test if it is ran on Linux.
    """
    if sys.platform in ('linux', 'linux2'):
        pytest.skip("mypy pytest only runs on Windows to disable it on CI.")
    path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
    os.chdir(path)
    command = ['mypy', 'collectiegroesbeek', '--config-file', 'tox.ini']
    process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if process.stderr:
        raise RuntimeError('Error running Mypy: {}'.format(process.stderr.decode('utf-8')))
    out = process.stdout.decode('utf8').lower()
    if len(out) != 0:
        pytest.fail('Mypy found typing errors:\n{}'.format(out))
