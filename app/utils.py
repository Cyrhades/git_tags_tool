"""
Utilitaires de style, thèmes QSS et helpers de mise en forme.
"""

from PySide6.QtGui import QColor
from app.models import TagStatus

# Palettes de couleurs pour les statuts
STATUS_COLORS = {
    TagStatus.SYNCHRONIZED: QColor("#2ecc71"),  # Vert Succès
    TagStatus.LOCAL_ONLY: QColor("#3498db"),     # Bleu Local
    TagStatus.REMOTE_ONLY: QColor("#9b59b6"),    # Violet Remote
    TagStatus.DIVERGENT: QColor("#e74c3c"),      # Rouge/Orange Alerte
}

STATUS_BG_COLORS = {
    TagStatus.SYNCHRONIZED: "rgba(46, 204, 113, 0.15)",
    TagStatus.LOCAL_ONLY: "rgba(52, 152, 219, 0.15)",
    TagStatus.REMOTE_ONLY: "rgba(155, 89, 182, 0.15)",
    TagStatus.DIVERGENT: "rgba(231, 76, 60, 0.2)",
}

STATUS_ICONS = {
    TagStatus.SYNCHRONIZED: "✓",
    TagStatus.LOCAL_ONLY: "✦",
    TagStatus.REMOTE_ONLY: "☁",
    TagStatus.DIVERGENT: "⚠",
}

DARK_STYLE_SHEET = """
/* Base Application & Dialogs */
QMainWindow, QDialog, QMessageBox {
    background-color: #1e1e24;
    color: #e0e0e0;
}

QWidget {
    font-family: 'Segoe UI', 'Roboto', 'Helvetica Neue', sans-serif;
    font-size: 13px;
    color: #e0e0e0;
}

/* QMessageBox & Popups */
QMessageBox {
    background-color: #1e1e28;
    border: 1px solid #383848;
}

QMessageBox QLabel {
    color: #ffffff;
    font-size: 13px;
}

QMessageBox QPushButton {
    min-width: 85px;
    padding: 7px 16px;
}

/* File Dialog */
QFileDialog {
    background-color: #1e1e24;
    color: #ffffff;
}

QFileDialog QLabel {
    color: #ffffff;
}

QFileDialog QTreeView, QFileDialog QListView {
    background-color: #16161d;
    color: #ffffff;
    border: 1px solid #383848;
    border-radius: 6px;
}

QFileDialog QTreeView::item:selected, QFileDialog QListView::item:selected {
    background-color: #2563eb;
    color: #ffffff;
}

/* Radio Buttons & CheckBoxes */
QRadioButton, QCheckBox {
    color: #ffffff;
    spacing: 8px;
    font-weight: 500;
}

QRadioButton::indicator {
    width: 16px;
    height: 16px;
    border-radius: 9px;
    border: 2px solid #4da6ff;
    background-color: #14141e;
}

QRadioButton::indicator:hover {
    border-color: #60a5fa;
}

QRadioButton::indicator:checked {
    background-color: #3b82f6;
    border: 2px solid #60a5fa;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 2px solid #4da6ff;
    background-color: #14141e;
}

QCheckBox::indicator:hover {
    border-color: #60a5fa;
}

QCheckBox::indicator:checked {
    background-color: #3b82f6;
    border: 2px solid #60a5fa;
}

/* ToolTips */
QToolTip {
    background-color: #252538;
    color: #ffffff;
    border: 1px solid #4da6ff;
    border-radius: 4px;
    padding: 5px 9px;
    font-size: 12px;
}

/* GroupBox & Frames */
QGroupBox {
    border: 1px solid #33333f;
    border-radius: 8px;
    margin-top: 14px;
    padding-top: 12px;
    font-weight: bold;
    color: #a0a0b0;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
    background-color: #1e1e24;
}

QFrame#HeaderFrame {
    background-color: #252530;
    border-radius: 8px;
    border: 1px solid #333342;
    padding: 8px;
}

/* Labels */
QLabel {
    color: #d0d0e0;
}

QLabel#TitleLabel {
    font-size: 18px;
    font-weight: bold;
    color: #ffffff;
}

QLabel#RepoPathLabel {
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 13px;
    color: #4da6ff;
    font-weight: bold;
}

QLabel#RemoteUrlLabel {
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 12px;
    color: #9a9ab0;
}

/* LineEdit & ComboBox */
QLineEdit, QComboBox {
    background-color: #252535;
    border: 1px solid #383848;
    border-radius: 6px;
    padding: 6px 10px;
    color: #ffffff;
    selection-background-color: #3b82f6;
    selection-color: #ffffff;
}

QLineEdit:focus, QComboBox:focus {
    border: 1px solid #3b82f6;
}

QComboBox:hover {
    border: 1px solid #3b82f6;
    background-color: #2c2c40;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border-left: none;
}

QComboBox QAbstractItemView {
    background-color: #1a1a24;
    border: 1px solid #383848;
    border-radius: 6px;
    color: #ffffff;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
    padding: 4px;
    outline: none;
}

QComboBox QAbstractItemView::item {
    min-height: 26px;
    padding: 4px 8px;
    color: #ffffff;
    background-color: #1a1a24;
}

QComboBox QAbstractItemView::item:hover, QComboBox QAbstractItemView::item:selected {
    background-color: #2563eb;
    color: #ffffff;
}

/* QMenu (Menu Contextuel) */
QMenu {
    background-color: #1e1e28;
    border: 1px solid #383848;
    border-radius: 6px;
    padding: 4px;
}

QMenu::item {
    padding: 6px 20px;
    border-radius: 4px;
    color: #e0e0e0;
}

QMenu::item:selected {
    background-color: #2563eb;
    color: #ffffff;
}

QMenu::separator {
    height: 1px;
    background-color: #383848;
    margin: 4px 0px;
}

/* Buttons */
QPushButton {
    background-color: #2c2c3a;
    border: 1px solid #3e3e52;
    border-radius: 6px;
    padding: 7px 14px;
    color: #ffffff;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #38384a;
    border-color: #4f4f68;
}

QPushButton:pressed {
    background-color: #22222c;
}

QPushButton:disabled {
    background-color: #1a1a22;
    color: #555566;
    border-color: #282833;
}

QPushButton#PrimaryButton {
    background-color: #2563eb;
    border: 1px solid #3b82f6;
    color: #ffffff;
}

QPushButton#PrimaryButton:hover {
    background-color: #1d4ed8;
}

QPushButton#DangerButton {
    background-color: #dc2626;
    border: 1px solid #ef4444;
    color: #ffffff;
}

QPushButton#DangerButton:hover {
    background-color: #b91c1c;
}

/* Table Widget */
QTableWidget {
    background-color: #16161d;
    border: 1px solid #2d2d3c;
    border-radius: 8px;
    gridline-color: #252533;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
    alternate-background-color: #191922;
    color: #ffffff;
}

QTableWidget::item {
    padding: 6px;
    color: #ffffff;
}

QTableWidget::item:selected {
    background-color: #2563eb;
    color: #ffffff;
}

QHeaderView::section {
    background-color: #20202b;
    color: #9a9ab0;
    padding: 8px;
    border: none;
    border-bottom: 2px solid #2d2d3c;
    font-weight: bold;
}

/* TextEdit / PlainTextEdit */
QPlainTextEdit, QTextEdit {
    background-color: #14141a;
    border: 1px solid #2a2a38;
    border-radius: 6px;
    color: #e0e0e0;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 12px;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
}

/* Status Bar */
QStatusBar {
    background-color: #17171e;
    color: #9a9ab0;
    border-top: 1px solid #282836;
}

/* Scrollbars */
QScrollBar:vertical {
    background-color: #16161d;
    width: 10px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background-color: #323244;
    border-radius: 5px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #474760;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background-color: #16161d;
    height: 10px;
    margin: 0px;
}

QScrollBar::handle:horizontal {
    background-color: #323244;
    border-radius: 5px;
    min-width: 20px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #474760;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}
"""


def format_date_display(date_str: str | None) -> str:
    """Formatte une chaîne de date ISO pour un affichage lisible dans l'IHM."""
    if not date_str:
        return "-"
    cleaned = date_str.split("+")[0].split("Z")[0]
    return cleaned
