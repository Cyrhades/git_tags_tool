"""
Tests pour MainWindow et la sélection par case à cocher.
"""

import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
import pytest

from app.main_window import MainWindow
from app.models import GitTag, TagStatus


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


def test_main_window_checkbox_selection(qapp):
    win = MainWindow()

    tag1 = GitTag(name="v1.0.0", local=True, remote=False, status=TagStatus.LOCAL_ONLY)
    tag2 = GitTag(name="v1.1.0", local=True, remote=True, status=TagStatus.SYNCHRONIZED)
    tag3 = GitTag(name="v2.0.0", local=False, remote=True, status=TagStatus.REMOTE_ONLY)
    win.tags = [tag1, tag2, tag3]
    win.current_repo_path = "C:/fake/repo"
    win._populate_table()

    assert win.table.rowCount() == 3
    assert len(win._get_checked_tags()) == 0

    # Cocher la première ligne
    win.table.item(0, 0).setCheckState(Qt.CheckState.Checked)
    checked = win._get_checked_tags()
    assert len(checked) == 1
    assert checked[0].name == "v1.0.0"

    # Test "Tout cocher"
    win._check_all_tags(True)
    assert len(win._get_checked_tags()) == 3

    # Test "Tout décocher"
    win._check_all_tags(False)
    assert len(win._get_checked_tags()) == 0
