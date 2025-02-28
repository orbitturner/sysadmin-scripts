#!/bin/bash

# ==========================
# SCRIPT DE BUILD & RELEASE
# ==========================
# 🚀 Compile le script Python en binaire avec PyInstaller
# 🏷️ Versionne et publie sur GitHub Releases
# 📢 Auteur : orbitturner
# ==========================

set -e  # Arrêter le script en cas d'erreur

# 🛠️ Configurations
REPO_OWNER="orbitturner"
REPO_NAME="sysadmin-scripts"
PROJECT_DIR="Linux/modsec-installer"
BIN_NAME="install_modsec"
BUILD_DIR="./bin"
GITHUB_API="https://api.github.com/repos/$REPO_OWNER/$REPO_NAME"
GITHUB_RELEASES="https://github.com/$REPO_OWNER/$REPO_NAME/releases/latest/download/$BIN_NAME"

# 🔍 Vérification des dépendances
echo "🔎 Vérification des dépendances..."
if ! command -v pyinstaller &>/dev/null; then
    echo "❌ PyInstaller n'est pas installé !"
    echo "➡️  Installation : pip install pyinstaller"
    exit 1
fi
if ! command -v jq &>/dev/null; then
    echo "❌ jq n'est pas installé (nécessaire pour gérer la version)."
    echo "➡️  Installation : sudo apt install jq"
    exit 1
fi
if ! command -v gh &>/dev/null; then
    echo "❌ GitHub CLI (gh) n'est pas installé."
    echo "➡️  Installation : https://cli.github.com/"
    exit 1
fi

# 🔥 Aller dans le bon dossier
cd "$(dirname "$0")"

# 🔄 Récupérer la dernière version publiée sur GitHub
echo "🔍 Récupération de la dernière version..."
LATEST_VERSION=$(curl -s "$GITHUB_API/releases/latest" | jq -r .tag_name)

# Si aucune version n'existe, on démarre à v1.0.0
if [[ "$LATEST_VERSION" == "null" || -z "$LATEST_VERSION" ]]; then
    NEW_VERSION="v1.0.0"
else
    # 📈 Incrémentation automatique de version (ex: v1.0.0 → v1.0.1)
    VERSION_PARTS=(${LATEST_VERSION//./ })
    PATCH=$((VERSION_PARTS[2] + 1))
    NEW_VERSION="v${VERSION_PARTS[0]}.${VERSION_PARTS[1]}.$PATCH"
fi

echo "🆕 Nouvelle version : $NEW_VERSION"

# 🚀 Compilation avec PyInstaller
echo "⚙️  Compilation du binaire..."
pyinstaller --onefile --distpath $BUILD_DIR "$PROJECT_DIR/install_modsec.py"

# 📌 Vérifier si le build a réussi
if [[ ! -f "$BUILD_DIR/$BIN_NAME" ]]; then
    echo "❌ Erreur : Le binaire n'a pas été généré correctement."
    exit 1
fi
chmod +x "$BUILD_DIR/$BIN_NAME"

# 🏷️ Création du tag et push
echo "🏷️ Création du tag Git : $NEW_VERSION"
git tag -a "$NEW_VERSION" -m "Release $NEW_VERSION - ModSecurity Installer"
git push origin "$NEW_VERSION"

# 🚀 Création d'une release sur GitHub
echo "📦 Création de la release sur GitHub..."
gh release create "$NEW_VERSION" "$BUILD_DIR/$BIN_NAME" --title "Release $NEW_VERSION" --notes "🚀 Nouvelle version de install_modsec"

# 📢 Affichage du lien de téléchargement
echo "✅ Build & release terminé !"
echo "📥 Vous pouvez télécharger le binaire avec :"
echo "curl -sL $GITHUB_RELEASES -o $BIN_NAME && chmod +x $BIN_NAME && ./$BIN_NAME"
echo "wget -qO $BIN_NAME $GITHUB_RELEASES && chmod +x $BIN_NAME && ./$BIN_NAME"
