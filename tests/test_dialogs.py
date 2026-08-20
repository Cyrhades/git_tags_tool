"""
Tests pour les dialogues, notamment CreateTagDialog avec gestion de package.json.
"""

import sys
import tempfile
from pathlib import Path
from PySide6.QtWidgets import QApplication
import pytest

from app.dialogs import CreateTagDialog, DeleteTagsDialog
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


def test_delete_tags_dialog_local_and_remote(qapp):
    from app.models import GitTag, TagStatus

    tag_sync = GitTag(name="v1.0.0", local=True, remote=True, status=TagStatus.SYNCHRONIZED)
    tag_local = GitTag(name="v1.1.0", local=True, remote=False, status=TagStatus.LOCAL_ONLY)
    tag_remote = GitTag(name="v2.0.0", local=False, remote=True, status=TagStatus.REMOTE_ONLY)

    # 1. Sélection mixte
    dlg = DeleteTagsDialog([tag_sync, tag_local, tag_remote], remote_url="git@github.com:user/repo.git")

    assert dlg.has_local_tags is True
    assert dlg.has_remote_tags is True
    assert dlg.chk_delete_local.isEnabled() is True
    assert dlg.chk_delete_local.isChecked() is True
    assert dlg.chk_delete_remote.isEnabled() is True
    assert dlg.chk_delete_remote.isChecked() is False
    assert dlg.warn_remote_frame.isHidden() is True
    assert dlg.btn_delete.isEnabled() is True

    # Cocher la suppression distante -> avertissement affiché
    dlg.chk_delete_remote.setChecked(True)
    assert dlg.warn_remote_frame.isHidden() is False
    del_local, del_remote = dlg.get_options()
    assert del_local is True
    assert del_remote is True

    # Décocher les deux -> bouton supprimer désactivé
    dlg.chk_delete_local.setChecked(False)
    dlg.chk_delete_remote.setChecked(False)
    assert dlg.btn_delete.isEnabled() is False


def test_delete_tags_dialog_local_only(qapp):
    from app.models import GitTag, TagStatus

    tag_local = GitTag(name="v1.0.0", local=True, remote=False, status=TagStatus.LOCAL_ONLY)
    dlg = DeleteTagsDialog([tag_local])

    assert dlg.has_local_tags is True
    assert dlg.has_remote_tags is False
    assert dlg.chk_delete_local.isEnabled() is True
    assert dlg.chk_delete_local.isChecked() is True
    assert dlg.chk_delete_remote.isEnabled() is False
    assert dlg.chk_delete_remote.isChecked() is False


def test_delete_tags_dialog_remote_only(qapp):
    from app.models import GitTag, TagStatus

    tag_remote = GitTag(name="v2.0.0", local=False, remote=True, status=TagStatus.REMOTE_ONLY)
    dlg = DeleteTagsDialog([tag_remote])

    assert dlg.has_local_tags is False
    assert dlg.has_remote_tags is True
    assert dlg.chk_delete_local.isEnabled() is False
    assert dlg.chk_delete_local.isChecked() is False
    assert dlg.chk_delete_remote.isEnabled() is True
