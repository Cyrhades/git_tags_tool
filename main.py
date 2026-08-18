"""
Point d'entrée principal de l'application Git Tag Manager.
"""

import sys
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMessageBox

from app.git_manager import GitManager
from app.main_window import MainWindow
from app.utils import DARK_STYLE_SHEET


def main() -> None:
    """Fonction principale d'initialisation et de lancement de l'application."""
    app = QApplication(sys.argv)
    app.setApplicationName("Git Tag Manager")
    app.setOrganizationName("Cyrhades")

    # Application globale de la feuille de style sombre sur toute l'application (dialogues, popups, inputs)
    app.setStyleSheet(DARK_STYLE_SHEET)

    # 1. Vérification de l'installation de Git sur la machine
    if not GitManager.is_git_installed():
        QMessageBox.critical(
            None,
            "Git non détecté",
            "L'exécutable 'git' n'a pas été trouvé dans le PATH de votre système.\n\n"
            "Veuillez installer Git (https://git-scm.com/) puis réessayez.",
        )
        sys.exit(1)

    # 2. Récupération d'un éventuel argument de ligne de commande (chemin du dépôt)
    initial_repo = None
    if len(sys.argv) > 1:
        candidate = sys.argv[1]
        if Path(candidate).exists():
            initial_repo = candidate

    # 3. Lancement de la fenêtre principale
    window = MainWindow(initial_repo_path=initial_repo)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
