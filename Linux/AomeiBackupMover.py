import os
import shutil
from loguru import logger

# Chemins sources et destination
source_path = r'/mntjlehowe'
destination_path = r'/mnt/wewewwcd'

# Configuration du logger
logger.add(
    "script.log", format="<level>{level}</level> {message}", level="INFO")

# Fonction pour déplacer les dossiers


def move_folders(source, destination):
    if os.path.exists(destination):
        logger.info("🗑️ Suppression du dossier existant : {}", destination)
        shutil.rmtree(destination)

    logger.info("📂 Déplacement des dossiers de {} vers {}",
                source, destination)

    # Liste des dossiers déplacés
    moved_folders = []

    for folder in os.listdir(source):
        source_folder_path = os.path.join(source, folder)
        destination_folder_path = os.path.join(destination, folder)

        logger.info("📁 Déplacement du dossier : {}", folder)
        shutil.move(source_folder_path, destination_folder_path)

        moved_folders.append(folder)

    logger.info("✅ Déplacement terminé !")
    logger.info("📦 Dossiers déplacés : {}", moved_folders)


# Exécution du script
if __name__ == "__main__":
    try:
        move_folders(source_path, destination_path)
    except Exception as e:
        logger.error("❌ Une erreur est survenue : {}", e)
