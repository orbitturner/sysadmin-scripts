#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import signal
import argparse
import time

from loguru import logger
from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Prompt
from rich import print as rprint

# ------------------------------------------------------------------------------
# Configuration du logger Loguru
# ------------------------------------------------------------------------------
logger.add("install_modsec.log", rotation="5 MB",
           compression="zip", backtrace=True, diagnose=True)

# ------------------------------------------------------------------------------
# Chargement des variables d'environnement
# ------------------------------------------------------------------------------
load_dotenv()

# ------------------------------------------------------------------------------
# Configuration Rich
# ------------------------------------------------------------------------------
console = Console()

# ------------------------------------------------------------------------------
# Définition de quelques profils de base
# ------------------------------------------------------------------------------
PROFILES = {
    "basic": {
        "description": "Profil basique, règles OWASP CRS par défaut, filtrage minimal.",
        "rules": [
            # Exemple de règles OWASP de base
            "SecRuleEngine On",
            "Include /etc/nginx/modsec/coreruleset/crs-setup.conf",
            "Include /etc/nginx/modsec/coreruleset/rules/*.conf",
            # Possibilité d'ajouter des règles custom
        ]
    },
    "strict": {
        "description": "Profil strict, active plus de règles défensives (SQLi, XSS).",
        "rules": [
            "SecRuleEngine On",
            "Include /etc/nginx/modsec/coreruleset/crs-setup.conf",
            "Include /etc/nginx/modsec/coreruleset/rules/*.conf",
            # Exemple de règle supplémentaire
            "SecRule REQUEST_HEADERS:User-Agent \"(?i:sqlmap)\" \"id:1001,deny,log,msg:'SQLMap Scan Detected'\""
        ]
    },
    "paranoid": {
        "description": "Profil paranoïaque, activations agressives de règles, risque de faux positifs.",
        "rules": [
            "SecRuleEngine On",
            "Include /etc/nginx/modsec/coreruleset/crs-setup.conf",
            "Include /etc/nginx/modsec/coreruleset/rules/*.conf",
            # Exemple de règle plus sensible
            "SecRule ARGS \"(?i:select|union|drop|insert)\" \"id:2001,deny,log,msg:'SQL Keywords Detected'\"",
            "SecRule ARGS \"<script>\" \"id:2002,deny,log,msg:'XSS Detected'\""
        ]
    }
}

# ------------------------------------------------------------------------------
# Fonctions utilitaires
# ------------------------------------------------------------------------------


def run_command(cmd):
    """
    Lance une commande shell et renvoie True si tout se passe bien,
    sinon False. Affiche aussi les logs d'erreurs si besoin.
    """
    logger.debug(f"Exécution de la commande : {cmd}")
    try:
        result = subprocess.run(
            cmd, shell=True, check=False, capture_output=True, text=True)
        if result.returncode == 0:
            logger.debug(f"Succès: {result.stdout.strip()}")
            return True
        else:
            logger.error(
                f"Erreur ({result.returncode}): {result.stderr.strip()}")
            return False
    except Exception as e:
        logger.exception(
            f"Exception lors de l'exécution de la commande : {cmd}")
        return False


def is_nginx_installed():
    """
    Vérifie si Nginx est installé.
    """
    logger.debug("Vérification de l'installation de Nginx...")
    check = subprocess.run("which nginx", shell=True, capture_output=True)
    return check.returncode == 0


def is_modsecurity_installed():
    """
    Vérifie si ModSecurity est installé (en supposant la présence d'un paquet).
    Ajuster en fonction de la distribution (Debian/RedHat).
    """
    logger.debug("Vérification de l'installation de ModSecurity...")
    check = subprocess.run("dpkg -s libnginx-mod-security2",
                           shell=True, capture_output=True, text=True)
    return check.returncode == 0


def install_nginx():
    """
    Installe Nginx (Debian/Ubuntu). Idempotent, vérifie avant si c'est déjà installé.
    """
    start_time = time.time()

    if is_nginx_installed():
        rprint("[green]✅ Nginx est déjà installé.[/green]")
        logger.info("Nginx déjà installé")
        logger.debug(
            f"install_nginx() terminé en {time.time() - start_time:.2f}s")
        return True

    rprint("[yellow]⚠️  Nginx n'est pas installé sur ce système.[/yellow]")
    console.print("Voulez-vous l'installer ? [y/n]", style="bold cyan")
    choice = Prompt.ask("")

    if choice.lower() == "y":
        rprint("🚀 [blue]Installation de Nginx en cours...[/blue]")
        if run_command("sudo apt-get update && sudo apt-get install -y nginx"):
            rprint("[green]✅ Nginx installé avec succès ![/green]")
            logger.info("Nginx installé avec succès")
            logger.debug(
                f"install_nginx() terminé en {time.time() - start_time:.2f}s")
            return True
        else:
            rprint("[red]❌ Échec de l'installation de Nginx[/red]")
            logger.error("Échec de l'installation de Nginx")
            logger.debug(
                f"install_nginx() terminé en {time.time() - start_time:.2f}s (erreur)")
            return False
    else:
        rprint("[red]Installation de Nginx refusée. Abandon.[/red]")
        logger.warning("Installation de Nginx refusée par l'utilisateur")
        sys.exit(1)


def install_modsecurity():
    """
    Installe ModSecurity (Debian/Ubuntu). Idempotent, vérifie avant.
    """
    start_time = time.time()

    if is_modsecurity_installed():
        rprint("[green]✅ ModSecurity est déjà installé.[/green]")
        logger.info("ModSecurity déjà installé")
        logger.debug(
            f"install_modsecurity() terminé en {time.time() - start_time:.2f}s")
        return True

    rprint("🚀 [blue]Installation de ModSecurity en cours...[/blue]")
    if run_command("sudo apt-get update && sudo apt-get install -y libnginx-mod-security2 git"):
        rprint("[green]✅ ModSecurity installé avec succès ![/green]")
        logger.info("ModSecurity installé avec succès")
        logger.debug(
            f"install_modsecurity() terminé en {time.time() - start_time:.2f}s")
        return True
    else:
        rprint("[red]❌ Échec de l'installation de ModSecurity[/red]")
        logger.error("Échec de l'installation de ModSecurity")
        logger.debug(
            f"install_modsecurity() terminé en {time.time() - start_time:.2f}s (erreur)")
        return False


def configure_modsecurity(profile_name, disable_rules=None, enable_rules=None):
    """
    Configure ModSecurity avec un profil donné.
    - disable_rules / enable_rules sont des listes d'IDs de règles à activer/désactiver.
    """
    start_time = time.time()

    modsec_conf = "/etc/nginx/modsecurity.conf"
    crs_repo = "/etc/nginx/modsec/coreruleset"

    # Cloner les règles OWASP CRS si pas déjà fait (idempotent)
    if not os.path.isdir(crs_repo):
        run_command(
            f"sudo git clone https://github.com/coreruleset/coreruleset.git {crs_repo}")
        run_command(
            f"sudo mv {crs_repo}/crs-setup.conf.example {crs_repo}/crs-setup.conf")

    if profile_name not in PROFILES:
        rprint(f"[red]❌ Profil {profile_name} inconnu. Abandon.[/red]")
        logger.error(f"Profil {profile_name} inconnu.")
        sys.exit(1)

    rules = PROFILES[profile_name]["rules"].copy()

    # Désactivation de règles via SecRuleUpdateActionById
    if disable_rules:
        for rule_id in disable_rules:
            # On fait juste un debug pour signaler
            logger.debug(f"Désactivation de la règle ID {rule_id}")
            rules.append(f"SecRuleUpdateActionById {rule_id} \"nolog,pass\"")

    # Activation de règles via SecRuleUpdateActionById
    if enable_rules:
        for rule_id in enable_rules:
            logger.debug(f"Activation de la règle ID {rule_id}")
            rules.append(f"SecRuleUpdateActionById {rule_id} \"deny,log\"")

    # Écriture du fichier de conf
    try:
        with open("/tmp/modsecurity.conf.tmp", "w") as f:
            f.write("SecAuditLog /var/log/nginx/modsec_audit.log\n")
            f.write("SecAuditEngine RelevantOnly\n")
            f.write("SecAuditLogParts ABIJDEFHZ\n\n")
            for line in rules:
                f.write(line + "\n")

        run_command(f"sudo mv /tmp/modsecurity.conf.tmp {modsec_conf}")
        run_command(f"sudo chown root:root {modsec_conf}")
        run_command(f"sudo chmod 644 {modsec_conf}")

        # Vérifier et insérer la directive modsecurity on; dans /etc/nginx/nginx.conf si nécessaire
        with open("/etc/nginx/nginx.conf", "r") as f:
            nginx_conf_content = f.read()

        if "modsecurity on;" not in nginx_conf_content:
            updated_conf = nginx_conf_content.replace(
                "http {",
                "http {\n    modsecurity on;\n    modsecurity_rules_file /etc/nginx/modsecurity.conf;\n"
            )
            with open("/tmp/nginx.conf.tmp", "w") as tmpf:
                tmpf.write(updated_conf)

            run_command("sudo mv /tmp/nginx.conf.tmp /etc/nginx/nginx.conf")
            run_command("sudo chown root:root /etc/nginx/nginx.conf")
            run_command("sudo chmod 644 /etc/nginx/nginx.conf")

        run_command("sudo systemctl restart nginx")

        rprint(
            f"[green]✅ ModSecurity configuré avec le profil [bold]{profile_name}[/bold].[/green]")
        logger.info(f"ModSecurity configuré avec le profil {profile_name}.")
        logger.debug(
            f"configure_modsecurity() terminé en {time.time() - start_time:.2f}s")

    except Exception as e:
        rprint(
            f"[red]❌ Erreur lors de la configuration de ModSecurity: {e}[/red]")
        logger.exception("Exception lors de la configuration de ModSecurity")
        logger.debug(
            f"configure_modsecurity() terminé en {time.time() - start_time:.2f}s (erreur)")
        sys.exit(1)

# ------------------------------------------------------------------------------
# Gestion des signaux (Ctrl + C)
# ------------------------------------------------------------------------------


def signal_handler(sig, frame):
    rprint(
        "\n[bold red]❗ Interruption (Ctrl + C) détectée. Arrêt du script.[/bold red]")
    logger.warning("Script interrompu par Ctrl + C")
    sys.exit(1)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# ------------------------------------------------------------------------------
# Point d'entrée principal
# ------------------------------------------------------------------------------


def main():
    """
    Script principal pour installer/configurer Nginx et ModSecurity.
    """
    parser = argparse.ArgumentParser(
        description="Script idempotent d'installation et configuration de Nginx + ModSecurity."
    )
    parser.add_argument(
        "--profile",
        type=str,
        default=os.getenv("MODSEC_PROFILE", "basic"),
        help="Choix du profil ModSecurity (basic, strict, paranoid)."
    )
    parser.add_argument(
        "--disable-rules",
        nargs='*',
        default=None,
        help="Liste d'IDs de règles à désactiver."
    )
    parser.add_argument(
        "--enable-rules",
        nargs='*',
        default=None,
        help="Liste d'IDs de règles à réactiver (deny,log)."
    )
    args = parser.parse_args()

    profile = args.profile
    disable_rules = args.disable_rules
    enable_rules = args.enable_rules

    rprint("[bold magenta]Bienvenue dans le script d'installation de ModSecurity pour Nginx![/bold magenta] 🎉")
    logger.info("Démarrage du script d'installation ModSecurity")

    # 1) Vérifier ou installer Nginx
    if not install_nginx():
        sys.exit(1)  # Impossible d'installer, on quitte

    # 2) Vérifier ou installer ModSecurity
    if not install_modsecurity():
        sys.exit(1)  # Impossible d'installer, on quitte

    # 3) Configurer ModSecurity selon le profil choisi
    configure_modsecurity(profile, disable_rules, enable_rules)

    rprint("[bold green]✨ Tout est terminé ![/bold green]")
    logger.info("Installation et configuration terminées avec succès.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Interruption du script par Ctrl+C")
        sys.exit(0)
