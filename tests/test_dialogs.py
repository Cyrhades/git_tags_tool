"""
Tests pour les dialogues, notamment CreateTagDialog avec gestion de package.json.
"""

import sys
import tempfile
from pathlib import Path
from PySide6.QtWidgets import QApplication
import pytest

from app.dialogs import CreateTagDialog
from app.git_manager import GitManager


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


def test_create_tag_dialog_without_package_json(qapp):
    with tempfile.TemporaryDirectory() as tmpdir:
        # Initialiser git
        import subprocess
        subprocess.run(["git", "init"], cwd=tmpdir, check=True, capture_output=True)

        dlg = CreateTagDialog(
            repo_path=tmpdir,
            existing_tags=[],
        )

        assert dlg.has_package_json is False
        assert dlg.pkg_version_input is None

        dlg.name_input.setText("v1.0.0")
        name, annotated, message, pkg_ver = dlg.get_data()
        assert name == "v1.0.0"
        assert annotated is False
        assert message == ""
        assert pkg_ver is None


def test_create_tag_dialog_with_package_json(qapp):
    with tempfile.TemporaryDirectory() as tmpdir:
        # Initialiser git
        import subprocess
        subprocess.run(["git", "init"], cwd=tmpdir, check=True, capture_output=True)

        # Créer package.json
        pkg_file = Path(tmpdir) / "package.json"
        pkg_file.write_text('{\n  "name": "test-pkg",\n  "version": "1.0.0"\n}\n', encoding="utf-8")

        dlg = CreateTagDialog(
            repo_path=tmpdir,
            existing_tags=[],
        )

        assert dlg.has_package_json is True
        assert dlg.pkg_version_input is not None
        assert dlg.pkg_version_input.text() == "1.0.0"
        # Le nom du tag par défaut doit être v<version>
        assert dlg.name_input.text() == "v1.0.0"

        # Modification de la version -> mise à jour automatique du tag
        dlg.pkg_version_input.setText("1.1.0")
        assert dlg.name_input.text() == "v1.1.0"

        name, annotated, message, pkg_ver = dlg.get_data()
        assert name == "v1.1.0"
        assert pkg_ver == "1.1.0"
