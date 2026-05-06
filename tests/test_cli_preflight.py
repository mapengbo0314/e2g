import pytest
from unittest import mock
import sys
from harness.indexer_wrapper import check_indxr_installed

def test_check_indxr_installed_fails_when_missing():
    with mock.patch("shutil.which", return_value=None):
        with pytest.raises(SystemExit):
            check_indxr_installed()

def test_check_indxr_installed_passes_when_present():
    with mock.patch("shutil.which", return_value="/usr/bin/indxr"):
        assert check_indxr_installed() is True
