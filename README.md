# Git Tag Manager 🏷️

**Git Tag Manager** est une application desktop Python complète et moderne basée sur **PySide6 (Qt)** permettant de visualiser, créer, pousser, synchroniser et supprimer les tags Git locaux et distants sans manipuler directement la ligne de commande.

---

## 🚀 Fonctionnalités

- 📂 **Sélection intuitive de dépôt** : Détection automatique de la racine Git en pointant sur le dossier projet ou directement sur le dossier `.git`.
- 🌐 **Détection du Remote** : Affichage automatique de l'URL du remote `origin`.
- 🔄 **Comparaison temps-réel** : Visualisation claire du statut de chaque tag :
  - **✓ Synchronisé** (Présent en local et sur le remote avec le même commit)
  - **✦ Local** (Présent uniquement dans votre dépôt local)
  - **☁ Remote** (Présent uniquement sur le serveur origin)
  - **⚠ Divergence** (Même nom mais pointe vers des commits différents)
- ➕ **Création de Tags** : Prise en charge des tags **simples** (*lightweight*) et **annotés** avec messages personnalisés et validation du nom en temps réel.
- 🚀 **Push vers Remote** : Publication d'un tag local vers `origin` en un clic.
- 🗑️ **Suppression sécurisée** :
  - Confirmation simple pour la suppression locale (`git tag -d`).
  - Confirmation renforcée et explicite pour la suppression sur le serveur remote (`git push origin :refs/tags/<name>`).
- 🔎 **Détails & Logs** :
  - Vue complète de la commande `git show` avec bouton de copie dans le presse-papier.
  - Journal d'opérations horodaté pour suivre l'exécution des commandes en arrière-plan.
- ⚡ **Exécution Asynchrone** : Aucune interruption ou gel d'IHM pendant les requêtes réseau ou les commandes Git.

---

## 🛠️ Prérequis

1. **Python 3.11+** répertorié dans le `PATH`.
2. **Git** (version 2.20+) installé sur votre machine.

> ℹ️ *L'application utilise les clés SSH et identifiants déjà configurés sur votre système par votre gestionnaire de credentials Git.*

---

## 📥 Installation

1. **Cloner ou ouvrir le dossier du projet** :
   ```bash
   cd tool_tags
   ```

2. **Créer un environnement virtuel Python** :
   ```bash
   python -m venv .venv
   ```

3. **Activer l'environnement virtuel** :
   - **Windows** (PowerShell) :
     ```powershell
     .\.venv\Scripts\Activate.ps1
     ```
   - **Linux / macOS** :
     ```bash
     source .venv/bin/activate
     ```

4. **Installer les dépendances** :
   ```bash
   pip install -r requirements.txt
   ```

---

## 💻 Lancement

### Sous Windows (Script Batch)
Double-cliquez simplement sur [run.bat](file:///c:/Users/cyrha/Desktop/les_CTFs_de_Cyrhades/version_3.1/tool_tags/run.bat) ou exécutez dans un terminal :

```cmd
run.bat
```

### Via la ligne de commande Python
Exécuter la commande suivante depuis la racine du projet :

```bash
python main.py
```

Vous pouvez également passer optionnellement le chemin d'un dépôt Git directement en argument :

```bash
python main.py /chemin/vers/mon/depot
```

---

## 🧪 Lancement des Tests Unitaires

Le projet inclut une suite de tests automatisés utilisant `pytest` qui créent de vrais dépôts Git temporaires sur le disque pour valider les comportements.

```bash
pytest
```

---

## 📦 Packaging (Création de l'Exécutable Autonome)

L'application peut être compilée en exécutable autonome sans dépendance Python requise pour l'utilisateur final en utilisant **PyInstaller**.

### Génération pour Windows (`GitTagManager.exe`)

```powershell
pyinstaller --noconfirm --onedir --windowed --name "GitTagManager" main.py
```

L'exécutable généré se trouvera dans le dossier `dist/GitTagManager/GitTagManager.exe`.

### Génération pour Linux / macOS

```bash
pyinstaller --noconfirm --onedir --windowed --name "GitTagManager" main.py
```

---

## 🏗️ Architecture du Projet

```text
git-tag-manager/
├── main.py                    # Point d'entrée de l'application PySide6
├── requirements.txt           # Liste des dépendances Python
├── README.md                  # Documentation du projet
├── .gitignore                 # Exclusion des fichiers temporaires
│
├── app/                       # Package d'application
│   ├── __init__.py
│   ├── git_manager.py         # Encapsulation des commandes Git via subprocess
│   ├── models.py              # Dataclasses GitTag, RepositoryInfo et Enum TagStatus
│   ├── workers.py             # Exécution asynchrone (QThread, QWorker)
│   ├── dialogs.py             # Boîtes de dialogue (Création, Détails, Confirmations)
│   ├── main_window.py         # Interface utilisateur principale PySide6
│   └── utils.py               # Thème sombre QSS et formateurs
│
└── tests/                     # Tests automatisés
    ├── __init__.py
    ├── test_models.py         # Tests des structures de données
    └── test_git_manager.py    # Tests d'intégration des commandes Git
```
