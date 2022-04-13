from sameproject.cli import version
from click.testing import CliRunner


def test_version():
    # just testing that version works - should never fail
    runner = CliRunner()
    result = runner.invoke(version)
    assert result.exit_code == 0
