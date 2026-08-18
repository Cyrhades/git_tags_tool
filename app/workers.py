"""
Gestion des opérations asynchrones via les threads PySide6.
"""

from typing import Any, Callable, List, Optional
from PySide6.QtCore import QThread, Signal

from app.git_manager import GitManager
from app.models import GitTag, RepositoryInfo


class GitWorker(QThread):
    """
    Worker QThread générique pour exécuter une tâche Git en arrière-plan
    sans bloquer la boucle d'événements de l'interface graphique Qt.
    """
    started_signal = Signal(str)
    finished_signal = Signal(object)
    error_signal = Signal(str)

    def __init__(self, action_name: str, fn: Callable[[], Any], parent=None):
        super().__init__(parent)
        self.action_name = action_name
        self.fn = fn

    def run(self) -> None:
        """Exécution du thread."""
        self.started_signal.emit(self.action_name)
        try:
            result = self.fn()
            self.finished_signal.emit(result)
        except Exception as exc:
            self.error_signal.emit(str(exc))


class RefreshTagsWorker(QThread):
    """
    Worker dédié à la synchronisation et au chargement complet des tags
    (local, remote et comparaison).
    """
    started_signal = Signal(str)
    progress_signal = Signal(str)
    finished_signal = Signal(list, object)  # (List[GitTag], RepositoryInfo)
    error_signal = Signal(str)

    def __init__(self, repo_path: str, remote_name: str = "origin", do_fetch: bool = False, parent=None):
        super().__init__(parent)
        self.repo_path = repo_path
        self.remote_name = remote_name
        self.do_fetch = do_fetch

    def run(self) -> None:
        """Exécute les étapes de rafraîchissement des tags."""
        self.started_signal.emit("Chargement des informations du dépôt...")
        try:
            repo_info = GitManager.get_repository_info(self.repo_path, remote=self.remote_name)

            if self.do_fetch and repo_info.has_remote:
                self.progress_signal.emit(f"Synchronisation avec {self.remote_name} (git fetch --tags)...")
                try:
                    GitManager.fetch_tags(self.repo_path, remote=self.remote_name)
                except Exception as fetch_err:
                    # Ne pas bloquer la suite si fetch échoue, mais notifier l'erreur
                    self.progress_signal.emit(f"Avertissement Fetch: {fetch_err}")

            self.progress_signal.emit("Lecture des tags locaux...")
            local_tags = GitManager.get_local_tags(self.repo_path)

            remote_tags = []
            if repo_info.has_remote:
                self.progress_signal.emit(f"Lecture des tags distants ({self.remote_name})...")
                try:
                    remote_tags = GitManager.get_remote_tags(self.repo_path, remote=self.remote_name)
                except Exception as rem_err:
                    self.progress_signal.emit(f"Avertissement Remote: {rem_err}")

            self.progress_signal.emit("Comparaison des tags locaux et distants...")
            compared_tags = GitManager.compare_tags(local_tags, remote_tags)

            self.finished_signal.emit(compared_tags, repo_info)
        except Exception as exc:
            self.error_signal.emit(str(exc))
