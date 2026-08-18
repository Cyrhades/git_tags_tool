"""
Tests unitaires pour les modèles de données et la logique d'état des tags.
"""

from app.models import (
    GitTag,
    LocalTagInfo,
    RemoteTagInfo,
    RepositoryInfo,
    TagStatus,
)


def test_tag_status_enum():
    assert TagStatus.SYNCHRONIZED.value == "Synchronisé"
    assert TagStatus.LOCAL_ONLY.value == "Local"
    assert TagStatus.REMOTE_ONLY.value == "Remote"
    assert TagStatus.DIVERGENT.value == "Divergence"


def test_git_tag_commit_formatting():
    # Tag synchronisé
    tag_sync = GitTag(
        name="v1.0.0",
        local=True,
        remote=True,
        local_commit="abcdef1234567890",
        remote_commit="abcdef1234567890",
        status=TagStatus.SYNCHRONIZED,
    )
    assert tag_sync.short_local_commit == "abcdef1"
    assert tag_sync.short_remote_commit == "abcdef1"
    assert tag_sync.display_commit == "abcdef1"

    # Tag divergent
    tag_div = GitTag(
        name="v2.0.0",
        local=True,
        remote=True,
        local_commit="1111111222222222",
        remote_commit="3333333444444444",
        status=TagStatus.DIVERGENT,
    )
    assert tag_div.display_commit == "1111111 / 3333333"

    # Tag remote uniquement
    tag_rem = GitTag(
        name="v3.0.0",
        local=False,
        remote=True,
        remote_commit="9999999888888888",
        status=TagStatus.REMOTE_ONLY,
    )
    assert tag_rem.short_local_commit == ""
    assert tag_rem.short_remote_commit == "9999999"
    assert tag_rem.display_commit == "9999999"


def test_repository_info():
    repo = RepositoryInfo(
        path="/tmp/test_repo",
        remote_name="origin",
        remote_url="git@github.com:user/repo.git",
        has_remote=True,
    )
    assert repo.path == "/tmp/test_repo"
    assert repo.has_remote is True
