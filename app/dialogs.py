"""
Fenêtres de dialogue pour la création, la suppression et l'affichage des détails des tags.
"""

from typing import Optional, Tuple
from PySide6.QtCore import Qt
from PySide6.QtGui import QClipboard, QFont
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QRadioButton,
    QTextEdit,
    QVBoxLayout,
)

from app.models import GitTag
from app.git_manager import GitManager


class CreateTagDialog(QDialog):
    """Dialogue interactif pour la création d'un nouveau tag (simple ou annoté)."""

    def __init__(
        self,
        repo_path: str,
        existing_tags: list[str],
        uncommitted_info: str = "",
        remote_tag_hashes: Optional[dict] = None,
        parent=None,
    ):
        super().__init__(parent)
        self.repo_path = repo_path
        self.existing_tags = existing_tags
        self.uncommitted_info = uncommitted_info
        self.remote_tag_hashes = remote_tag_hashes or {}
        self.has_package_json = GitManager.has_package_json(self.repo_path)
        self.current_pkg_version = GitManager.get_package_json_version(self.repo_path) if self.has_package_json else None
        self.pkg_version_input: Optional[QLineEdit] = None

        self.setWindowTitle("Créer un tag Git")
        self.setMinimumWidth(480)
        self.setModal(True)

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # 1. Bannière d'avertissement en cas de modifications non commitées
        if self.uncommitted_info:
            warn_frame = QFrame()
            warn_frame.setStyleSheet(
                "background-color: rgba(245, 158, 11, 0.15); "
                "border: 1px solid #f59e0b; "
                "border-radius: 6px; "
                "padding: 8px;"
            )
            warn_layout = QVBoxLayout(warn_frame)
            warn_lbl = QLabel(
                f"<b>⚠️ Modifications non commitées détectées :</b><br>{self.uncommitted_info}.<br>"
                f"<span style='color: #d1d5db; font-size: 11px;'>"
                f"💡 Conseil : Pensez à commiter vos changements avant de créer le tag. "
                f"Sinon, le tag sera attaché au commit HEAD précédent."
                f"</span>"
            )
            warn_lbl.setWordWrap(True)
            warn_layout.addWidget(warn_lbl)
            layout.addWidget(warn_frame)

        # Formulaire
        form = QFormLayout()
        form.setSpacing(10)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("ex: v1.0.0, release-2.3")
        form.addRow("Nom du tag :", self.name_input)

        if self.has_package_json:
            self.pkg_version_input = QLineEdit()
            self.pkg_version_input.setPlaceholderText("ex: 1.0.0")
            if self.current_pkg_version is not None:
                self.pkg_version_input.setText(self.current_pkg_version)
            form.addRow("Version package.json :", self.pkg_version_input)

        # Message d'erreur dynamique
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #ef4444; font-size: 12px; font-weight: bold;")
        self.error_label.setWordWrap(True)
        form.addRow("", self.error_label)

        # Message d'avertissement de divergence dynamique
        self.warning_label = QLabel("")
        self.warning_label.setStyleSheet("color: #f59e0b; font-size: 12px; font-weight: bold;")
        self.warning_label.setWordWrap(True)
        form.addRow("", self.warning_label)

        # Selection type de tag
        type_layout = QHBoxLayout()
        self.radio_simple = QRadioButton("Tag simple (lightweight)")
        self.radio_annotated = QRadioButton("Tag annoté")
        self.radio_simple.setChecked(True)

        type_group = QButtonGroup(self)
        type_group.addButton(self.radio_simple)
        type_group.addButton(self.radio_annotated)

        type_layout.addWidget(self.radio_simple)
        type_layout.addWidget(self.radio_annotated)
        form.addRow("Type de tag :", type_layout)

        # Message d'annotation
        self.message_input = QPlainTextEdit()
        self.message_input.setPlaceholderText("Saisissez un message décrivant la version...")
        self.message_input.setMaximumHeight(90)
        self.message_input.setEnabled(False)
        form.addRow("Message :", self.message_input)

        self.radio_annotated.toggled.connect(
            lambda checked: self.message_input.setEnabled(checked)
        )

        layout.addLayout(form)

        # Boutons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_cancel = QPushButton("Annuler")
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_create = QPushButton("Créer le tag")
        self.btn_create.setObjectName("PrimaryButton")
        self.btn_create.setEnabled(False)
        self.btn_create.clicked.connect(self.accept)

        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_create)

        layout.addLayout(btn_layout)

        # Connecteurs et pré-remplissage une fois tous les widgets initialisés
        self.name_input.textChanged.connect(self._validate_input)
        if self.has_package_json and self.pkg_version_input is not None:
            self.pkg_version_input.textChanged.connect(self._on_pkg_version_changed)

        if self.current_pkg_version:
            default_tag_name = f"v{self.current_pkg_version}" if not self.current_pkg_version.startswith("v") else self.current_pkg_version
            self.name_input.setText(default_tag_name)
            self.name_input.selectAll()
        else:
            self._validate_input()

    def _validate_input(self) -> None:
        if not hasattr(self, "error_label") or not hasattr(self, "btn_create"):
            return
        tag_name = self.name_input.text().strip()
        if not tag_name:
            self.error_label.setText("")
            self.warning_label.setText("")
            self.btn_create.setEnabled(False)
            return

        if tag_name in self.existing_tags:
            self.error_label.setText(f"Un tag local nommé '{tag_name}' existe déjà.")
            self.warning_label.setText("")
            self.btn_create.setEnabled(False)
            return

        valid, err = GitManager.validate_tag_name(self.repo_path, tag_name)
        if not valid:
            self.error_label.setText(err)
            self.warning_label.setText("")
            self.btn_create.setEnabled(False)
        else:
            self.error_label.setText("")
            self.btn_create.setEnabled(True)

            if tag_name in self.remote_tag_hashes:
                rem_commit = self.remote_tag_hashes[tag_name][:7]
                self.warning_label.setText(
                    f"⚠️ Attention : Le tag '{tag_name}' existe déjà sur origin (commit {rem_commit}). "
                    f"Sa création locale entraînera une DIVERGENCE."
                )
            else:
                self.warning_label.setText("")

    def _on_pkg_version_changed(self, new_val: str) -> None:
        val = new_val.strip()
        if val:
            tag_name = f"v{val}" if not val.startswith("v") else val
            current_tag = self.name_input.text().strip()
            if not current_tag or current_tag.startswith("v"):
                self.name_input.setText(tag_name)

    def get_data(self) -> Tuple[str, bool, str, Optional[str]]:
        """Retourne (tag_name, is_annotated, message, package_version)."""
        pkg_ver = self.pkg_version_input.text().strip() if self.pkg_version_input else None
        return (
            self.name_input.text().strip(),
            self.radio_annotated.isChecked(),
            self.message_input.toPlainText().strip(),
            pkg_ver,
        )


class TagDetailsDialog(QDialog):
    """Dialogue de visualisation complète des détails d'un tag avec git show."""

    def __init__(self, tag: GitTag, git_show_output: str, parent=None):
        super().__init__(parent)
        self.tag = tag
        self.git_show_output = git_show_output

        self.setWindowTitle(f"Détails du tag : {tag.name}")
        self.resize(700, 550)
        self.setModal(True)

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Entête synthétique
        info_form = QFormLayout()
        info_form.setSpacing(6)

        tag_name_lbl = QLabel(self.tag.name)
        font = tag_name_lbl.font()
        font.setBold(True)
        font.setPointSize(14)
        tag_name_lbl.setFont(font)
        tag_name_lbl.setStyleSheet("color: #60a5fa;")
        info_form.addRow("Nom du tag :", tag_name_lbl)

        info_form.addRow("Statut :", QLabel(f"{self.tag.status.value} (Local: {'✓' if self.tag.local else '✗'}, Remote: {'✓' if self.tag.remote else '✗'})"))

        if self.tag.local_commit:
            info_form.addRow("Commit Local :", QLabel(self.tag.local_commit))
        if self.tag.remote_commit:
            info_form.addRow("Commit Remote :", QLabel(self.tag.remote_commit))
        if self.tag.date:
            info_form.addRow("Date :", QLabel(self.tag.date))
        if self.tag.author:
            info_form.addRow("Auteur :", QLabel(self.tag.author))

        layout.addLayout(info_form)

        # Section Git Show
        sep_lbl = QLabel("--- Sortie complète de `git show` ---")
        sep_lbl.setStyleSheet("color: #9ca3af; font-weight: bold; margin-top: 5px;")
        layout.addWidget(sep_lbl)

        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setPlainText(self.git_show_output)
        self.text_edit.setFont(QFont("Consolas", 10))
        layout.addWidget(self.text_edit)

        # Boutons bas
        btn_layout = QHBoxLayout()

        self.btn_copy = QPushButton("Copier dans le presse-papier")
        self.btn_copy.clicked.connect(self._copy_to_clipboard)

        self.btn_close = QPushButton("Fermer")
        self.btn_close.clicked.connect(self.accept)

        btn_layout.addWidget(self.btn_copy)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_close)

        layout.addLayout(btn_layout)

    def _copy_to_clipboard(self) -> None:
        clipboard = QApplication.clipboard()
        clipboard.setText(self.git_show_output)
        self.btn_copy.setText("✓ Copié !")
        self.btn_copy.setEnabled(False)


class ConfirmDeleteDialog(QDialog):
    """Dialogue de confirmation adapté pour la suppression locale et renforcé pour le remote."""

    def __init__(self, tag_name: str, is_remote: bool, remote_url: Optional[str] = None, parent=None):
        super().__init__(parent)
        self.tag_name = tag_name
        self.is_remote = is_remote
        self.remote_url = remote_url

        title = "Supprimer le tag distant" if is_remote else "Supprimer le tag local"
        self.setWindowTitle(title)
        self.setMinimumWidth(450)
        self.setModal(True)

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        if self.is_remote:
            icon_lbl = QLabel("⚠️ ATTENTION : SUPPRESSION DISTANTE ⚠️")
            icon_lbl.setStyleSheet("color: #ef4444; font-size: 15px; font-weight: bold;")
            icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(icon_lbl)

            msg = (
                f"Vous êtes sur le point de supprimer définitivement le tag :\n\n"
                f"    👉  '{self.tag_name}'\n\n"
                f"du dépôt distant origin ({self.remote_url or 'Remote origin'}).\n\n"
                f"Cette action modifiera le dépôt distant pour tous les collaborateurs."
            )
            lbl = QLabel(msg)
            lbl.setStyleSheet("color: #fca5a5; font-size: 13px;")
            lbl.setWordWrap(True)
            layout.addWidget(lbl)

            btn_del = QPushButton("Supprimer du remote")
            btn_del.setObjectName("DangerButton")
        else:
            icon_lbl = QLabel("Suppression du tag local")
            icon_lbl.setStyleSheet("color: #f59e0b; font-size: 14px; font-weight: bold;")
            layout.addWidget(icon_lbl)

            msg = (
                f"Êtes-vous sûr de vouloir supprimer le tag local '{self.tag_name}' ?\n\n"
                f"Cette opération supprimera le tag uniquement de votre dépôt local."
            )
            lbl = QLabel(msg)
            lbl.setWordWrap(True)
            layout.addWidget(lbl)

            btn_del = QPushButton("Supprimer le tag local")
            btn_del.setObjectName("PrimaryButton")

        # Boutons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_cancel = QPushButton("Annuler")
        btn_cancel.clicked.connect(self.reject)

        btn_del.clicked.connect(self.accept)

        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_del)

        layout.addLayout(btn_layout)
