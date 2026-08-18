"""
Modèles de données pour l'application Git Tag Manager.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class TagStatus(Enum):
    """Statut de comparaison entre les tags locaux et distants."""
    SYNCHRONIZED = "Synchronisé"
    LOCAL_ONLY = "Local"
    REMOTE_ONLY = "Remote"
    DIVERGENT = "Divergence"

    def __str__(self) -> str:
        return self.value


@dataclass
class LocalTagInfo:
    """Informations extraites pour un tag local."""
    name: str
    commit_hash: str
    date: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None


@dataclass
class RemoteTagInfo:
    """Informations extraites pour un tag distant."""
    name: str
    commit_hash: str


@dataclass
class GitTag:
    """Représentation unifiée d'un tag Git avec son état local et distant."""
    name: str
    local: bool = False
    remote: bool = False
    local_commit: Optional[str] = None
    remote_commit: Optional[str] = None
    status: TagStatus = TagStatus.LOCAL_ONLY
    date: Optional[str] = None
    author: Optional[str] = None
    message: Optional[str] = None

    @property
    def short_local_commit(self) -> str:
        """Retourne les 7 premiers caractères du commit local."""
        return self.local_commit[:7] if self.local_commit else ""

    @property
    def short_remote_commit(self) -> str:
        """Retourne les 7 premiers caractères du commit distant."""
        return self.remote_commit[:7] if self.remote_commit else ""

    @property
    def display_commit(self) -> str:
        """Retourne le hash court à afficher dans la vue tableau."""
        if self.status == TagStatus.DIVERGENT:
            return f"{self.short_local_commit} / {self.short_remote_commit}"
        if self.short_local_commit:
            return self.short_local_commit
        return self.short_remote_commit


@dataclass
class RepositoryInfo:
    """Informations globales sur le dépôt Git sélectionné."""
    path: str
    remote_name: str = "origin"
    remote_url: Optional[str] = None
    has_remote: bool = False
