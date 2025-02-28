import os
import subprocess

# Définir le chemin absolu vers le script
chemin_script = os.path.abspath(__file__)

# Définir le dossier racine du projet
dossier_projet = os.path.dirname(os.path.dirname(chemin_script))

# Définir les dossiers à ignorer
dossiers_ignores = ["node_modules"]

# Emoji pour les logs
emoji_success = "✅"
emoji_warning = "⚠️"
emoji_error = "❌"

print(f"⚙️ REQUIREMENTS.TXT FILES INSTALLER 🚀")

# Parcourir récursivement le dossier projet
for dossier_racine, dossiers, fichiers in os.walk(dossier_projet):
    # Ignorer les dossiers spécifiés
    dossiers[:] = [d for d in dossiers if d not in dossiers_ignores]
    
    for fichier in fichiers:
        if fichier == "requirements.txt":
            chemin_requirements = os.path.join(dossier_racine, fichier)
            
            # Installer les dépendances à l'aide de pip
            commande_pip = ["pip", "install", "-r", chemin_requirements]
            
            # Afficher un log de démarrage
            print(f"{emoji_success} Installation des dépendances de {chemin_requirements}")
            
            # Exécuter la commande pip
            try:
                subprocess.check_output(commande_pip)
                print(f"{emoji_success} Dépendances installées avec succès.")
            except Exception as e:
                print(f"{emoji_error} Une erreur s'est produite lors de l'installation des dépendances : {e}")
