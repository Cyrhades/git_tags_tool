"""
Gestionnaire des opérations Git via subprocess.
"""

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from app.models import (
    GitTag,
    LocalTagInfo,
    RemoteTagInfo,
    RepositoryInfo,
    TagStatus,
)


class GitError(Exception):
    """Exception personnalisée pour les erreurs retournées par les commandes Git."""

    def __init__(self, command: List[str], returncode: int, stdout: str, stderr: str):
        self.command = command
        self.returncode = returncode
        self.stdout = stdout.strip()
        self.stderr = stderr.strip()
        cmd_str = " ".join(command)
        msg = f"Erreur Git (code {returncode}) lors de l'exécution de '{cmd_str}'"
        if self.stderr:
            msg += f"\n\nDetails:\n{self.stderr}"
        elif self.stdout:
            msg += f"\n\nSortie:\n{self.stdout}"
        super().__init__(msg)


class GitManager:
    """Classe encapsulant toutes les requêtes et commandes Git sous forme de sous-processus sécurisés."""

    @staticmethod
    def _build_env() -> Dict[str, str]:
        """Prépare un environnement d'exécution déterministe pour Git sans invite interactive."""
        env = os.environ.copy()
        env["GIT_TERMINAL_PROMPT"] = "0"
        env["LC_ALL"] = "C"
        return env

    @classmethod
    def _run_git(
        cls,
        args: List[str],
        cwd: Optional[str] = None,
        check: bool = True,
    ) -> subprocess.CompletedProcess:
        """
        Exécute une commande Git sous forme de sous-processus sans utiliser shell=True.
        Raises GitError si check est True et que le code de retour est non-nul.
        """
        full_args = ["git"] + args
        try:
            res = subprocess.run(
                full_args,
                cwd=cwd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=cls._build_env(),
            )
        except FileNotFoundError:
            raise GitError(
                command=full_args,
                returncode=-1,
                stdout="",
                stderr="L'exécutable 'git' est introuvable sur le système.",
            )

        if check and res.returncode != 0:
            raise GitError(
                command=full_args,
                returncode=res.returncode,
                stdout=res.stdout,
                stderr=res.stderr,
            )

        return res

    @classmethod
    def is_git_installed(cls) -> bool:
        """Vérifie si Git est accessible en ligne de commande."""
        try:
            res = cls._run_git(["--version"], check=False)
            return res.returncode == 0
        except GitError:
            return False

    @classmethod
    def get_repository_root(cls, target_path: str) -> str:
        """
        Vérifie si le chemin donné est dans un dépôt Git valide et retourne le chemin racine.
        Gère les cas où l'utilisateur sélectionne directement le dossier .git ou un sous-dossier.
        """
        path_obj = Path(target_path).resolve()
        if not path_obj.exists():
            raise GitError(
                command=["git", "rev-parse"],
                returncode=1,
                stdout="",
                stderr=f"Le chemin spécifié n'existe pas : {target_path}",
            )

        # Si l'utilisateur pointe sur le dossier .git
        search_dir = str(path_obj.parent) if path_obj.name == ".git" else str(path_obj)

        res = cls._run_git(
            ["rev-parse", "--show-toplevel"],
            cwd=search_dir,
            check=False,
        )
        if res.returncode != 0:
            raise GitError(
                command=["git", "rev-parse", "--show-toplevel"],
                returncode=res.returncode,
                stdout=res.stdout,
                stderr=f"Le dossier '{target_path}' n'est pas un dépôt Git valide.",
            )

        root = res.stdout.strip()
        return str(Path(root).resolve())

    @classmethod
    def get_remote_url(cls, repo_path: str, remote: str = "origin") -> Optional[str]:
        """Récupère l'URL d'un remote Git (ex: origin)."""
        res = cls._run_git(
            ["remote", "get-url", remote],
            cwd=repo_path,
            check=False,
        )
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
        return None

    @classmethod
    def get_repository_info(cls, repo_path: str, remote: str = "origin") -> RepositoryInfo:
        """Construit et retourne un objet RepositoryInfo complet."""
        root = cls.get_repository_root(repo_path)
        url = cls.get_remote_url(root, remote=remote)
        return RepositoryInfo(
            path=root,
            remote_name=remote,
            remote_url=url,
            has_remote=url is not None,
        )

    @classmethod
    def has_uncommitted_changes(cls, repo_path: str) -> Tuple[bool, str]:
        """
        Vérifie s'il y a des modifications non commitées dans le dépôt (git status --porcelain).
        Retourne (has_uncommitted, description).
        """
        res = cls._run_git(["status", "--porcelain"], cwd=repo_path, check=False)
        if res.returncode == 0 and res.stdout.strip():
            lines = [l for l in res.stdout.strip().splitlines() if l.strip()]
            return True, f"{len(lines)} fichier(s) modifié(s) ou non suivi(s)"
        return False, ""

    @classmethod
    def validate_tag_name(cls, repo_path: str, tag_name: str) -> Tuple[bool, str]:
        """
        Vérifie si un nom de tag est valide selon les règles de Git ref-format.
        Retourne (is_valid, error_message).
        """
        tag_name = tag_name.strip()
        if not tag_name:
            return False, "Le nom du tag ne peut pas être vide."

        res = cls._run_git(
            ["check-ref-format", "--allow-onelevel", f"refs/tags/{tag_name}"],
            cwd=repo_path,
            check=False,
        )
        if res.returncode != 0:
            return False, f"Le nom de tag '{tag_name}' est invalide pour Git."

        return True, ""

    @classmethod
    def get_local_tags(cls, repo_path: str) -> List[LocalTagInfo]:
        """
        Récupère tous les tags locaux avec leurs métadonnées.
        Formataion: refname:short|objectname|*objectname|creatordate:iso|authorname|subject
        """
        fmt = "%(refname:short)|%(objectname)|%(*objectname)|%(creatordate:iso)|%(authorname)|%(subject)"
        res = cls._run_git(
            ["for-each-ref", f"--format={fmt}", "refs/tags"],
            cwd=repo_path,
        )

        tags = []
        for line in res.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split("|", 5)
            if len(parts) < 6:
                continue

            name, obj_hash, deref_hash, date, author, subject = parts
            commit_hash = deref_hash if deref_hash else obj_hash

            tags.append(
                LocalTagInfo(
                    name=name,
                    commit_hash=commit_hash,
                    date=date if date else None,
                    author=author if author else None,
                    subject=subject if subject else None,
                )
            )

        return tags

    @classmethod
    def get_remote_tags(cls, repo_path: str, remote: str = "origin") -> List[RemoteTagInfo]:
        """
        Récupère les tags sur le remote via git ls-remote --tags.
        Gère le déréférencement ^{} pour obtenir le commit exact.
        """
        res = cls._run_git(
            ["ls-remote", "--tags", remote],
            cwd=repo_path,
            check=False,
        )

        if res.returncode != 0:
            raise GitError(
                command=["git", "ls-remote", "--tags", remote],
                returncode=res.returncode,
                stdout=res.stdout,
                stderr=f"Impossible de contacter le remote '{remote}'. Vérifiez votre connexion ou authentification.",
            )

        # Mapping: tag_name -> commit_hash
        tag_commits: Dict[str, str] = {}
        # Mapping secondaire pour enregistrer l'objet tag si ^{} n'a pas encore été vu
        tag_objects: Dict[str, str] = {}

        for line in res.stdout.splitlines():
            line = line.strip()
            if not line:
                continue

            parts = re.split(r"\s+", line)
            if len(parts) < 2:
                continue

            hash_val, ref_name = parts[0], parts[1]
            if not ref_name.startswith("refs/tags/"):
                continue

            raw_tag = ref_name.removeprefix("refs/tags/")
            if raw_tag.endswith("^{}"):
                real_tag_name = raw_tag.removesuffix("^{}")
                tag_commits[real_tag_name] = hash_val
            else:
                tag_objects[raw_tag] = hash_val

        # Pour les tags sans ^{} (tags simples), utiliser la valeur de tag_objects
        for tag_name, hash_val in tag_objects.items():
            if tag_name not in tag_commits:
                tag_commits[tag_name] = hash_val

        return [RemoteTagInfo(name=name, commit_hash=chash) for name, chash in tag_commits.items()]

    @classmethod
    def compare_tags(
        cls,
        local_tags: List[LocalTagInfo],
        remote_tags: List[RemoteTagInfo],
    ) -> List[GitTag]:
        """
        Compare les listes de tags locaux et distants et produit une liste unifiée
        avec l'état de synchronisation (Synchronisé, Local, Remote, Divergence).
        """
        local_dict = {t.name: t for t in local_tags}
        remote_dict = {t.name: t for t in remote_tags}

        all_names = sorted(set(local_dict.keys()) | set(remote_dict.keys()))
        unified_tags: List[GitTag] = []

        for name in all_names:
            loc = local_dict.get(name)
            rem = remote_dict.get(name)

            has_local = loc is not None
            has_remote = rem is not None

            loc_commit = loc.commit_hash if loc else None
            rem_commit = rem.commit_hash if rem else None

            if has_local and has_remote:
                if loc_commit == rem_commit:
                    status = TagStatus.SYNCHRONIZED
                else:
                    status = TagStatus.DIVERGENT
            elif has_local:
                status = TagStatus.LOCAL_ONLY
            else:
                status = TagStatus.REMOTE_ONLY

            unified_tags.append(
                GitTag(
                    name=name,
                    local=has_local,
                    remote=has_remote,
                    local_commit=loc_commit,
                    remote_commit=rem_commit,
                    status=status,
                    date=loc.date if loc else None,
                    author=loc.author if loc else None,
                    message=loc.subject if loc else None,
                )
            )

        return unified_tags

    @classmethod
    def fetch_tags(cls, repo_path: str, remote: str = "origin") -> None:
        """Récupère les tags du remote sans modifier les tags locaux existants."""
        cls._run_git(["fetch", remote, "--tags"], cwd=repo_path)

    @classmethod
    def create_tag(
        cls,
        repo_path: str,
        tag_name: str,
        annotated: bool = False,
        message: Optional[str] = None,
    ) -> None:
        """Crée un tag local (simple ou annoté)."""
        valid, err = cls.validate_tag_name(repo_path, tag_name)
        if not valid:
            raise ValueError(err)

        if annotated:
            msg = message.strip() if message else f"Tag {tag_name}"
            cls._run_git(["tag", "-a", tag_name, "-m", msg], cwd=repo_path)
        else:
            cls._run_git(["tag", tag_name], cwd=repo_path)

    @classmethod
    def push_tag(cls, repo_path: str, tag_name: str, remote: str = "origin") -> None:
        """Pousse un tag local vers le remote."""
        cls._run_git(["push", remote, tag_name], cwd=repo_path)

    @classmethod
    def delete_local_tag(cls, repo_path: str, tag_name: str) -> None:
        """Supprime un tag localement."""
        cls._run_git(["tag", "-d", tag_name], cwd=repo_path)

    @classmethod
    def delete_remote_tag(cls, repo_path: str, tag_name: str, remote: str = "origin") -> None:
        """Supprime un tag sur le remote."""
        cls._run_git(["push", remote, f":refs/tags/{tag_name}"], cwd=repo_path)

    @classmethod
    def show_tag(cls, repo_path: str, tag_name: str) -> str:
        """Retourne les informations détaillées fournies par git show <tag_name>."""
        res = cls._run_git(["show", tag_name], cwd=repo_path)
        return res.stdout

    @staticmethod
    def get_package_json_path(repo_path: str) -> Path:
        """Retourne le chemin vers package.json à la racine du dépôt."""
        return Path(repo_path) / "package.json"

    @classmethod
    def has_package_json(cls, repo_path: str) -> bool:
        """Indique si un fichier package.json existe à la racine du dépôt."""
        pkg_path = cls.get_package_json_path(repo_path)
        return pkg_path.is_file()

    @classmethod
    def get_package_json_version(cls, repo_path: str) -> Optional[str]:
        """
        Lit le fichier package.json et extrait la valeur du champ 'version'.
        Retourne None si le fichier n'existe pas ou n'est pas un JSON valide.
        """
        pkg_path = cls.get_package_json_path(repo_path)
        if not pkg_path.is_file():
            return None
        try:
            with open(pkg_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                version = data.get("version")
                return str(version) if version is not None else ""
        except Exception:
            return None
        return None

    @classmethod
    def update_package_json_version(cls, repo_path: str, new_version: str) -> bool:
        """
        Met à jour le champ 'version' dans package.json en préservant le formatage/l'indentation.
        Retourne True si la mise à jour a réussi, False sinon.
        """
        pkg_path = cls.get_package_json_path(repo_path)
        if not pkg_path.is_file():
            return False
        try:
            with open(pkg_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Détecter le saut de ligne
            newline = "\r\n" if "\r\n" in content else "\n"

            # Détecter l'indentation
            indent: int | str = 2
            for line in content.splitlines():
                if line.startswith("\t"):
                    indent = "\t"
                    break
                elif line.startswith("    "):
                    indent = 4
                    break
                elif line.startswith("  "):
                    indent = 2
                    break

            data = json.loads(content)
            if not isinstance(data, dict):
                return False

            data["version"] = new_version

            formatted = json.dumps(data, indent=indent, ensure_ascii=False) + "\n"
            if newline == "\r\n":
                formatted = formatted.replace("\n", "\r\n")

            with open(pkg_path, "w", encoding="utf-8", newline="") as f:
                f.write(formatted)
            return True
        except Exception:
            return False
