"""
Tests unitaires d'intégration pour la classe GitManager utilisant de vrais dépôts temporaires.
"""

import os
import subprocess
import tempfile
from pathlib import Path

import pytest
from app.git_manager import GitError, GitManager
from app.models import LocalTagInfo, RemoteTagInfo, TagStatus


def _init_git_repo(repo_path: str) -> None:
    """Helper pour initialiser un dépôt Git temporaire et ajouter un commit initial."""
    subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True, capture_output=True)

    dummy_file = Path(repo_path) / "file.txt"
    dummy_file.write_text("hello git tag manager")

    subprocess.run(["git", "add", "file.txt"], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_path, check=True, capture_output=True)


def test_is_git_installed():
    assert GitManager.is_git_installed() is True


def test_get_repository_root():
    with tempfile.TemporaryDirectory() as tmpdir:
        _init_git_repo(tmpdir)

        # Test sur le dossier racine
        root = GitManager.get_repository_root(tmpdir)
        assert Path(root).resolve() == Path(tmpdir).resolve()

        # Test sur le dossier .git
        git_folder = Path(tmpdir) / ".git"
        root_from_git = GitManager.get_repository_root(str(git_folder))
        assert Path(root_from_git).resolve() == Path(tmpdir).resolve()

        # Test sur un dossier non-git
        with tempfile.TemporaryDirectory() as non_git_dir:
            with pytest.raises(GitError):
                GitManager.get_repository_root(non_git_dir)


def test_validate_tag_name():
    with tempfile.TemporaryDirectory() as tmpdir:
        _init_git_repo(tmpdir)

        # Valides
        val, _ = GitManager.validate_tag_name(tmpdir, "v1.0.0")
        assert val is True
        val, _ = GitManager.validate_tag_name(tmpdir, "release-2.0")
        assert val is True

        # Invalides
        val, err = GitManager.validate_tag_name(tmpdir, "")
        assert val is False
        val, err = GitManager.validate_tag_name(tmpdir, "tag with spaces")
        assert val is False
        val, err = GitManager.validate_tag_name(tmpdir, "tag..double-dot")
        assert val is False


def test_create_and_get_local_tags():
    with tempfile.TemporaryDirectory() as tmpdir:
        _init_git_repo(tmpdir)

        # Créer un tag simple
        GitManager.create_tag(tmpdir, "v1.0.0", annotated=False)

        # Créer un tag annoté
        GitManager.create_tag(tmpdir, "v1.1.0", annotated=True, message="Release v1.1.0")

        tags = GitManager.get_local_tags(tmpdir)
        tag_names = [t.name for t in tags]

        assert "v1.0.0" in tag_names
        assert "v1.1.0" in tag_names
        assert len(tags) == 2


def test_delete_local_tag():
    with tempfile.TemporaryDirectory() as tmpdir:
        _init_git_repo(tmpdir)

        GitManager.create_tag(tmpdir, "v1.0.0", annotated=False)
        tags_before = GitManager.get_local_tags(tmpdir)
        assert len(tags_before) == 1

        GitManager.delete_local_tag(tmpdir, "v1.0.0")
        tags_after = GitManager.get_local_tags(tmpdir)
        assert len(tags_after) == 0


def test_show_tag():
    with tempfile.TemporaryDirectory() as tmpdir:
        _init_git_repo(tmpdir)

        GitManager.create_tag(tmpdir, "v1.0.0", annotated=True, message="Descriptive message")
        output = GitManager.show_tag(tmpdir, "v1.0.0")

        assert "v1.0.0" in output
        assert "Descriptive message" in output


def test_compare_tags():
    local_tags = [
        LocalTagInfo(name="v1.0.0", commit_hash="abc1234"),
        LocalTagInfo(name="v1.1.0", commit_hash="def5678"),
        LocalTagInfo(name="v1.2.0", commit_hash="local_hash"),
    ]

    remote_tags = [
        RemoteTagInfo(name="v1.0.0", commit_hash="abc1234"),
        RemoteTagInfo(name="v1.2.0", commit_hash="remote_hash"),
        RemoteTagInfo(name="v2.0.0", commit_hash="9999999"),
    ]

    compared = GitManager.compare_tags(local_tags, remote_tags)
    comp_dict = {t.name: t for t in compared}

    assert comp_dict["v1.0.0"].status == TagStatus.SYNCHRONIZED
    assert comp_dict["v1.1.0"].status == TagStatus.LOCAL_ONLY
    assert comp_dict["v1.2.0"].status == TagStatus.DIVERGENT
    assert comp_dict["v2.0.0"].status == TagStatus.REMOTE_ONLY


def test_remote_tag_operations():
    """Test d'intégration poussé simulant un remote Git 'origin' bare sur le disque."""
    with tempfile.TemporaryDirectory() as local_dir, tempfile.TemporaryDirectory() as remote_dir:
        # Initialiser le bare repository comme remote
        subprocess.run(["git", "init", "--bare"], cwd=remote_dir, check=True, capture_output=True)

        # Initialiser le dépôt local
        _init_git_repo(local_dir)

        # Ajouter le remote origin
        subprocess.run(["git", "remote", "add", "origin", remote_dir], cwd=local_dir, check=True, capture_output=True)

        # Créer un tag local annoté v3.1.0 et le pousser
        GitManager.create_tag(local_dir, "v3.1.0", annotated=True, message="Push remote v3.1.0 test")
        GitManager.push_tag(local_dir, "v3.1.0", remote="origin")

        # Vérifier sur le remote
        rem_tags = GitManager.get_remote_tags(local_dir, remote="origin")
        rem_names = [r.name for r in rem_tags]
        assert "v3.1.0" in rem_names
        assert "v3.1." not in rem_names

        # Comparer les tags locaux et distants
        loc_tags = GitManager.get_local_tags(local_dir)
        compared = GitManager.compare_tags(loc_tags, rem_tags)
        tag_v310 = next(t for t in compared if t.name == "v3.1.0")
        assert tag_v310.status == TagStatus.SYNCHRONIZED
        assert tag_v310.local is True
        assert tag_v310.remote is True

        # Supprimer le tag du remote
        GitManager.delete_remote_tag(local_dir, "v3.1.0", remote="origin")
        rem_tags_after = GitManager.get_remote_tags(local_dir, remote="origin")
        assert len(rem_tags_after) == 0


def test_has_uncommitted_changes():
    with tempfile.TemporaryDirectory() as tmpdir:
        _init_git_repo(tmpdir)

        # Dépôt propre juste après le commit initial
        has_changes, _ = GitManager.has_uncommitted_changes(tmpdir)
        assert has_changes is False

        # Création d'un nouveau fichier non commité
        new_file = Path(tmpdir) / "uncommitted.txt"
        new_file.write_text("modified content")

        has_changes_after, desc = GitManager.has_uncommitted_changes(tmpdir)
        assert has_changes_after is True
        assert "1 fichier(s)" in desc
