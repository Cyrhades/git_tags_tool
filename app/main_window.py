"""
Fenêtre principale PySide6 pour l'application Git Tag Manager.
"""

from datetime import datetime
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QAction, QColor, QFont, QIcon
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QFileDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.dialogs import ConfirmDeleteDialog, CreateTagDialog, TagDetailsDialog
from app.git_manager import GitError, GitManager
from app.models import GitTag, RepositoryInfo, TagStatus
from app.utils import DARK_STYLE_SHEET, STATUS_BG_COLORS, STATUS_COLORS, STATUS_ICONS, format_date_display
from app.workers import GitWorker, RefreshTagsWorker


class MainWindow(QMainWindow):
    """Fenêtre principale de gestion des tags Git."""

    def __init__(self, initial_repo_path: Optional[str] = None):
        super().__init__()
        self.setWindowTitle("Git Tag Manager")
        self.resize(1000, 700)
        self.setMinimumSize(850, 550)

        self.current_repo_path: Optional[str] = None
        self.repo_info: Optional[RepositoryInfo] = None
        self.tags: List[GitTag] = []
        self.active_worker: Optional[GitWorker | RefreshTagsWorker] = None

        self._init_ui()
        self.setStyleSheet(DARK_STYLE_SHEET)

        if initial_repo_path:
            self._load_repository(initial_repo_path)

    def _init_ui(self) -> None:
        """Initialise l'ensemble de l'interface utilisateur."""
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(14)

        # 1. En-tête : Informations sur le Dépôt
        header_frame = QFrame()
        header_frame.setObjectName("HeaderFrame")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(12, 10, 12, 10)

        info_vbox = QVBoxLayout()
        info_vbox.setSpacing(4)

        repo_hbox = QHBoxLayout()
        repo_lbl_title = QLabel("Repository:")
        repo_lbl_title.setStyleSheet("font-weight: bold; color: #a0a0b0;")
        self.repo_path_lbl = QLabel("Aucun dépôt sélectionné")
        self.repo_path_lbl.setObjectName("RepoPathLabel")
        repo_hbox.addWidget(repo_lbl_title)
        repo_hbox.addWidget(self.repo_path_lbl)
        repo_hbox.addStretch()

        remote_hbox = QHBoxLayout()
        remote_lbl_title = QLabel("Remote:")
        remote_lbl_title.setStyleSheet("font-weight: bold; color: #a0a0b0;")
        self.remote_url_lbl = QLabel("-")
        self.remote_url_lbl.setObjectName("RemoteUrlLabel")
        remote_hbox.addWidget(remote_lbl_title)
        remote_hbox.addWidget(self.remote_url_lbl)
        remote_hbox.addStretch()

        info_vbox.addLayout(repo_hbox)
        info_vbox.addLayout(remote_hbox)

        self.btn_change_repo = QPushButton("Changer de dépôt")
        self.btn_change_repo.setIconSize(QSize(16, 16))
        self.btn_change_repo.clicked.connect(self._select_repository_dialog)

        header_layout.addLayout(info_vbox, stretch=1)
        header_layout.addWidget(self.btn_change_repo)

        main_layout.addWidget(header_frame)

        # 2. Barre de recherche et de filtres
        filter_layout = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Rechercher un tag par son nom...")
        self.search_input.textChanged.connect(self._apply_filters)

        self.status_filter_combo = QComboBox()
        self.status_filter_combo.addItems([
            "Tous les statuts",
            TagStatus.SYNCHRONIZED.value,
            TagStatus.LOCAL_ONLY.value,
            TagStatus.REMOTE_ONLY.value,
            TagStatus.DIVERGENT.value,
        ])
        self.status_filter_combo.currentTextChanged.connect(self._apply_filters)

        self.btn_fetch = QPushButton("Fetch Remote Tags")
        self.btn_fetch.clicked.connect(lambda: self._refresh_tags(do_fetch=True))

        self.btn_refresh = QPushButton("Actualiser")
        self.btn_refresh.clicked.connect(lambda: self._refresh_tags(do_fetch=False))

        filter_layout.addWidget(self.search_input, stretch=2)
        filter_layout.addWidget(self.status_filter_combo, stretch=1)
        filter_layout.addWidget(self.btn_fetch)
        filter_layout.addWidget(self.btn_refresh)

        main_layout.addLayout(filter_layout)

        # 3. Tableau des Tags
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Tag", "Local", "Remote", "Statut", "Commit", "Date / Sujet"
        ])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 180)
        self.table.setColumnWidth(4, 120)

        # Signal de double clic et menu contextuel
        self.table.itemDoubleClicked.connect(self._on_table_double_click)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        self.table.itemSelectionChanged.connect(self._update_action_buttons_state)

        main_layout.addWidget(self.table, stretch=3)

        # 4. Barre de boutons d'actions
        action_layout = QHBoxLayout()

        self.btn_create_tag = QPushButton("Créer un tag")
        self.btn_create_tag.setObjectName("PrimaryButton")
        self.btn_create_tag.clicked.connect(self._create_tag_action)

        self.btn_push_tag = QPushButton("Push vers origin")
        self.btn_push_tag.clicked.connect(self._push_tag_action)

        self.btn_delete_local = QPushButton("Supprimer local")
        self.btn_delete_local.clicked.connect(self._delete_local_tag_action)

        self.btn_delete_remote = QPushButton("Supprimer distant")
        self.btn_delete_remote.setObjectName("DangerButton")
        self.btn_delete_remote.clicked.connect(self._delete_remote_tag_action)

        self.btn_show_details = QPushButton("Afficher")
        self.btn_show_details.clicked.connect(self._show_details_action)

        action_layout.addWidget(self.btn_create_tag)
        action_layout.addWidget(self.btn_push_tag)
        action_layout.addWidget(self.btn_delete_local)
        action_layout.addWidget(self.btn_delete_remote)
        action_layout.addWidget(self.btn_show_details)
        action_layout.addStretch()

        main_layout.addLayout(action_layout)

        # 5. Console de Journalisation
        log_group = QGroupBox("Journal d'opérations")
        log_vbox = QVBoxLayout(log_group)
        log_vbox.setContentsMargins(8, 8, 8, 8)

        self.log_console = QPlainTextEdit()
        self.log_console.setReadOnly(True)
        self.log_console.setMaximumHeight(130)

        log_top_layout = QHBoxLayout()
        log_top_layout.addStretch()
        btn_clear_log = QPushButton("Effacer le journal")
        btn_clear_log.setStyleSheet("padding: 2px 8px; font-size: 11px;")
        btn_clear_log.clicked.connect(self.log_console.clear)
        log_top_layout.addWidget(btn_clear_log)

        log_vbox.addLayout(log_top_layout)
        log_vbox.addWidget(self.log_console)

        main_layout.addWidget(log_group, stretch=1)

        # 6. Barre de Statut
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Prêt. Sélectionnez un dépôt Git pour commencer.")

        self._update_action_buttons_state()

    def log(self, message: str) -> None:
        """Ajoute une entrée horodatée dans la console du journal."""
        now = datetime.now().strftime("[%H:%M:%S]")
        self.log_console.appendPlainText(f"{now} {message}")

    def _select_repository_dialog(self) -> None:
        """Ouvre un sélecteur de dossier pour choisir un dépôt Git."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Sélectionner la racine du dépôt Git ou le dossier .git",
            self.current_repo_path or str(Path.home()),
        )
        if folder:
            self._load_repository(folder)

    def _load_repository(self, path: str) -> None:
        """Valide et charge le dépôt Git spécifié."""
        try:
            root_path = GitManager.get_repository_root(path)
            self.current_repo_path = root_path
            self.repo_path_lbl.setText(root_path)
            self.log(f"Dépôt sélectionné : {root_path}")
            self._refresh_tags(do_fetch=False)
        except GitError as err:
            self.log(f"❌ Erreur Dépôt : {err.stderr or err.stdout}")
            QMessageBox.critical(
                self,
                "Dépôt Git invalide",
                f"Le dossier sélectionné n'est pas un dépôt Git valide.\n\n{err.stderr or err.stdout}",
            )

    def _set_ui_busy(self, busy: bool, status_msg: str = "") -> None:
        """Active/Désactive l'IHM pendant les traitements asynchrones."""
        self.btn_change_repo.setEnabled(not busy)
        self.btn_fetch.setEnabled(not busy)
        self.btn_refresh.setEnabled(not busy)
        self.btn_create_tag.setEnabled(not busy and self.current_repo_path is not None)

        if busy:
            self.btn_push_tag.setEnabled(False)
            self.btn_delete_local.setEnabled(False)
            self.btn_delete_remote.setEnabled(False)
            self.btn_show_details.setEnabled(False)
            self.status_bar.showMessage(f"⟳ {status_msg}")
        else:
            self.status_bar.showMessage("✓ Prêt")
            self._update_action_buttons_state()

    def _refresh_tags(self, do_fetch: bool = False) -> None:
        """Lance le worker de rafraîchissement des tags."""
        if not self.current_repo_path:
            return

        self._set_ui_busy(True, "Chargement des tags...")
        self.worker = RefreshTagsWorker(
            repo_path=self.current_repo_path,
            remote_name="origin",
            do_fetch=do_fetch,
        )
        self.worker.progress_signal.connect(self.log)
        self.worker.finished_signal.connect(self._on_refresh_finished)
        self.worker.error_signal.connect(self._on_worker_error)
        self.worker.start()

    def _on_refresh_finished(self, tags: List[GitTag], repo_info: RepositoryInfo) -> None:
        """Callback lorsque le rafraîchissement des tags est terminé."""
        self.tags = tags
        self.repo_info = repo_info

        if repo_info.has_remote:
            self.remote_url_lbl.setText(f"{repo_info.remote_name} → {repo_info.remote_url}")
        else:
            self.remote_url_lbl.setText("Aucun remote 'origin' configuré")

        self.log(f"Total : {len(tags)} tag(s) analysé(s).")
        self._populate_table()
        self._set_ui_busy(False)

    def _on_worker_error(self, err_msg: str) -> None:
        """Callback en cas d'erreur dans un worker."""
        self.log(f"❌ Erreur : {err_msg}")
        self._set_ui_busy(False)
        QMessageBox.critical(self, "Erreur Git", err_msg)

    def _populate_table(self) -> None:
        """Remplit le tableau des tags avec filtrage et tri."""
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)

        search_text = self.search_input.text().strip().lower()
        selected_status = self.status_filter_combo.currentText()

        for tag in self.tags:
            # Filtre de recherche texte
            if search_text and search_text not in tag.name.lower():
                continue

            # Filtre de statut
            if selected_status != "Tous les statuts" and tag.status.value != selected_status:
                continue

            row = self.table.rowCount()
            self.table.insertRow(row)

            # Item Tag
            item_name = QTableWidgetItem(tag.name)
            item_name.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
            item_name.setData(Qt.ItemDataRole.UserRole, tag)

            # Item Local
            item_local = QTableWidgetItem("  ✓  " if tag.local else "  ✗  ")
            item_local.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_local.setForeground(QColor("#2ecc71") if tag.local else QColor("#e74c3c"))

            # Item Remote
            item_remote = QTableWidgetItem("  ✓  " if tag.remote else "  ✗  ")
            item_remote.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_remote.setForeground(QColor("#2ecc71") if tag.remote else QColor("#e74c3c"))

            # Item Statut
            status_text = f"{STATUS_ICONS.get(tag.status, '')} {tag.status.value}"
            item_status = QTableWidgetItem(status_text)
            item_status.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_status.setForeground(STATUS_COLORS.get(tag.status, QColor("#ffffff")))
            item_status.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))

            # Item Commit
            item_commit = QTableWidgetItem(tag.display_commit)
            item_commit.setFont(QFont("Consolas", 9))
            item_commit.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # Item Date / Sujet
            meta = []
            if tag.date:
                meta.append(format_date_display(tag.date))
            if tag.message:
                meta.append(tag.message)
            item_meta = QTableWidgetItem(" | ".join(meta) if meta else "-")

            self.table.setItem(row, 0, item_name)
            self.table.setItem(row, 1, item_local)
            self.table.setItem(row, 2, item_remote)
            self.table.setItem(row, 3, item_status)
            self.table.setItem(row, 4, item_commit)
            self.table.setItem(row, 5, item_meta)

        self.table.setSortingEnabled(True)
        self._update_action_buttons_state()

    def _apply_filters(self) -> None:
        """Déclenché lors du changement de texte dans la barre de recherche ou du filtre statut."""
        self._populate_table()

    def _get_selected_tag(self) -> Optional[GitTag]:
        """Retourne l'objet GitTag sélectionné dans le tableau."""
        selected_items = self.table.selectedItems()
        if not selected_items:
            return None
        row = selected_items[0].row()
        item_name = self.table.item(row, 0)
        if item_name:
            return item_name.data(Qt.ItemDataRole.UserRole)
        return None

    def _update_action_buttons_state(self) -> None:
        """Active/Désactive les boutons selon l'état du tag sélectionné."""
        tag = self._get_selected_tag()
        has_repo = self.current_repo_path is not None

        self.btn_create_tag.setEnabled(has_repo)

        if not tag:
            self.btn_push_tag.setEnabled(False)
            self.btn_delete_local.setEnabled(False)
            self.btn_delete_remote.setEnabled(False)
            self.btn_show_details.setEnabled(False)
            return

        self.btn_show_details.setEnabled(True)
        self.btn_delete_local.setEnabled(tag.local)
        self.btn_delete_remote.setEnabled(tag.remote)

        # Le Push est activé dès que le tag est présent localement
        self.btn_push_tag.setEnabled(has_repo and tag.local)

    def _on_table_double_click(self, item: QTableWidgetItem) -> None:
        """Déclenche la vue détaillée au double-clic."""
        self._show_details_action()

    def _show_context_menu(self, position) -> None:
        """Affiche le menu contextuel clic droit sur la ligne sélectionnée."""
        tag = self._get_selected_tag()
        menu = QMenu(self)

        if tag:
            action_show = QAction("Afficher les détails", self)
            action_show.triggered.connect(self._show_details_action)
            menu.addAction(action_show)

            menu.addSeparator()

            if tag.local:
                action_push = QAction("Push vers origin", self)
                action_push.triggered.connect(self._push_tag_action)
                menu.addAction(action_push)

            if tag.local:
                action_del_loc = QAction("Supprimer localement", self)
                action_del_loc.triggered.connect(self._delete_local_tag_action)
                menu.addAction(action_del_loc)

            if tag.remote:
                action_del_rem = QAction("Supprimer du remote (origin)", self)
                action_del_rem.triggered.connect(self._delete_remote_tag_action)
                menu.addAction(action_del_rem)

            menu.addSeparator()

        action_refresh = QAction("Actualiser", self)
        action_refresh.triggered.connect(lambda: self._refresh_tags(do_fetch=False))
        menu.addAction(action_refresh)

        menu.exec(self.table.viewport().mapToGlobal(position))

    # --- Actions Git ---

    def _create_tag_action(self) -> None:
        """Ouvre le dialogue de création de tag et exécute la création avec vérification préalable."""
        if not self.current_repo_path:
            return

        existing_names = [t.name for t in self.tags]
        has_uncommitted, uncommitted_desc = GitManager.has_uncommitted_changes(self.current_repo_path)
        remote_hashes = {t.name: t.remote_commit for t in self.tags if t.remote and t.remote_commit}

        dlg = CreateTagDialog(
            repo_path=self.current_repo_path,
            existing_tags=existing_names,
            uncommitted_info=uncommitted_desc if has_uncommitted else "",
            remote_tag_hashes=remote_hashes,
            parent=self,
        )
        if dlg.exec() == CreateTagDialog.DialogCode.Accepted:
            tag_name, annotated, message = dlg.get_data()
            self.log(f"Création du tag '{tag_name}' (Annoté: {annotated})...")

            def action():
                GitManager.create_tag(self.current_repo_path, tag_name, annotated, message)
                return tag_name

            self._run_async_git_action("Création de tag", action, success_msg=f"✓ Tag '{tag_name}' créé avec succès.")

    def _push_tag_action(self) -> None:
        """Pousse le tag sélectionné vers le remote."""
        tag = self._get_selected_tag()
        if not tag or not self.current_repo_path:
            return

        if tag.status == TagStatus.DIVERGENT:
            res = QMessageBox.warning(
                self,
                "Avertissement Divergence",
                f"Le tag '{tag.name}' pointe vers des commits différents en local et sur le remote.\n\n"
                f"Local: {tag.short_local_commit}\nRemote: {tag.short_remote_commit}\n\n"
                "Voulez-vous forcer le push vers origin ?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if res != QMessageBox.StandardButton.Yes:
                return

        self.log(f"Push du tag '{tag.name}' vers origin...")

        def action():
            GitManager.push_tag(self.current_repo_path, tag.name, remote="origin")
            return tag.name

        self._run_async_git_action("Push tag", action, success_msg=f"✓ Tag '{tag.name}' envoyé vers origin.")

    def _delete_local_tag_action(self) -> None:
        """Supprime le tag sélectionné du dépôt local après confirmation."""
        tag = self._get_selected_tag()
        if not tag or not self.current_repo_path:
            return

        dlg = ConfirmDeleteDialog(tag.name, is_remote=False, parent=self)
        if dlg.exec() == ConfirmDeleteDialog.DialogCode.Accepted:
            self.log(f"Suppression locale du tag '{tag.name}'...")

            def action():
                GitManager.delete_local_tag(self.current_repo_path, tag.name)
                return tag.name

            self._run_async_git_action("Suppression local tag", action, success_msg=f"✓ Tag local '{tag.name}' supprimé.")

    def _delete_remote_tag_action(self) -> None:
        """Supprime le tag sélectionné du remote origin après confirmation renforcée."""
        tag = self._get_selected_tag()
        if not tag or not self.current_repo_path:
            return

        remote_url = self.repo_info.remote_url if self.repo_info else None
        dlg = ConfirmDeleteDialog(tag.name, is_remote=True, remote_url=remote_url, parent=self)
        if dlg.exec() == ConfirmDeleteDialog.DialogCode.Accepted:
            self.log(f"Suppression distante du tag '{tag.name}' sur origin...")

            def action():
                GitManager.delete_remote_tag(self.current_repo_path, tag.name, remote="origin")
                return tag.name

            self._run_async_git_action("Suppression remote tag", action, success_msg=f"✓ Tag distant '{tag.name}' supprimé de origin.")

    def _show_details_action(self) -> None:
        """Récupère la sortie de git show et l'affiche dans un dialogue dédié."""
        tag = self._get_selected_tag()
        if not tag or not self.current_repo_path:
            return

        self.log(f"Lecture des détails du tag '{tag.name}' via git show...")

        def action():
            return GitManager.show_tag(self.current_repo_path, tag.name)

        def on_success(git_show_output: str):
            dlg = TagDetailsDialog(tag, git_show_output, self)
            dlg.exec()

        self._run_async_git_action("git show", action, callback=on_success)

    def _run_async_git_action(self, action_name: str, fn, success_msg: str = "", callback=None) -> None:
        """Exécute une fonction Git dans un thread async avec gestion de la barre de statut et du journal."""
        self._set_ui_busy(True, f"Exécution : {action_name}...")

        self.active_worker = GitWorker(action_name, fn)

        def on_finished(result):
            if success_msg:
                self.log(success_msg)
            self._set_ui_busy(False)
            if callback:
                callback(result)
            self._refresh_tags(do_fetch=False)

        def on_error(err_msg):
            self.log(f"❌ Erreur ({action_name}) : {err_msg}")
            self._set_ui_busy(False)
            QMessageBox.critical(self, f"Erreur Git - {action_name}", err_msg)

        self.active_worker.finished_signal.connect(on_finished)
        self.active_worker.error_signal.connect(on_error)
        self.active_worker.start()
