#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ==========================
# NGINX + MODSECURITY INSTALL SCRIPT
# ==========================
# 🚀 Installs and configures Nginx + ModSecurity
# 🏷️ Idempotent approach with multiple security profiles
# 📢 Author: orbitturner
# ==========================

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
# Loguru Configuration
# ------------------------------------------------------------------------------
logger.add("install_modsec.log", rotation="5 MB",
           compression="zip", backtrace=True, diagnose=True)

# ------------------------------------------------------------------------------
# Load environment variables
# ------------------------------------------------------------------------------
load_dotenv()

# ------------------------------------------------------------------------------
# Rich Configuration
# ------------------------------------------------------------------------------
console = Console()

# ------------------------------------------------------------------------------
# Definition of security profiles
# ------------------------------------------------------------------------------
PROFILES = {
    "basic": {
        "description": "Basic profile with OWASP CRS default rules and minimal filtering.",
        "rules": [
            "SecRuleEngine On",
            "Include /etc/nginx/modsec/coreruleset/crs-setup.conf",
            "Include /etc/nginx/modsec/coreruleset/rules/*.conf",
        ]
    },
    "strict": {
        "description": "Strict profile with stronger defensive rules (SQLi, XSS).",
        "rules": [
            "SecRuleEngine On",
            "Include /etc/nginx/modsec/coreruleset/crs-setup.conf",
            "Include /etc/nginx/modsec/coreruleset/rules/*.conf",
            "SecRule REQUEST_HEADERS:User-Agent \"(?i:sqlmap)\" \"id:1001,deny,log,msg:'SQLMap Scan Detected'\""
        ]
    },
    "paranoid": {
        "description": "Paranoid profile with aggressive rule activation, higher risk of false positives.",
        "rules": [
            "SecRuleEngine On",
            "Include /etc/nginx/modsec/coreruleset/crs-setup.conf",
            "Include /etc/nginx/modsec/coreruleset/rules/*.conf",
            "SecRule ARGS \"(?i:select|union|drop|insert)\" \"id:2001,deny,log,msg:'SQL Keywords Detected'\"",
            "SecRule ARGS \"<script>\" \"id:2002,deny,log,msg:'XSS Detected'\""
        ]
    }
}

# ------------------------------------------------------------------------------
# Utility Functions
# ------------------------------------------------------------------------------


def run_command(cmd: str) -> bool:
    """
    Execute a shell command and return True if successful, otherwise False.
    Logs errors if needed.
    """
    logger.debug(f"Executing command: {cmd}")
    try:
        result = subprocess.run(
            cmd, shell=True, check=False, capture_output=True, text=True)
        if result.returncode == 0:
            logger.debug(f"Success: {result.stdout.strip()}")
            return True
        else:
            logger.error(
                f"Error ({result.returncode}): {result.stderr.strip()}")
            return False
    except Exception as e:
        logger.exception(f"Exception while running command: {cmd}")
        return False


def is_nginx_installed() -> bool:
    """
    Check if Nginx is installed.
    """
    logger.debug("Checking if Nginx is installed...")
    check = subprocess.run("which nginx", shell=True, capture_output=True)
    return check.returncode == 0


def is_modsecurity_installed() -> bool:
    """
    Check if ModSecurity is installed (assuming 'libnginx-mod-security2' package for Debian/Ubuntu).
    Adjust accordingly for other distributions (e.g., CentOS/RedHat).
    """
    logger.debug("Checking if ModSecurity is installed...")
    check = subprocess.run("dpkg -s libnginx-mod-security2",
                           shell=True, capture_output=True, text=True)
    return check.returncode == 0


def install_nginx() -> bool:
    """
    Install Nginx (Debian/Ubuntu). Idempotent, checks first if it's already installed.
    """
    start_time = time.time()

    if is_nginx_installed():
        rprint("[green]✅ Nginx is already installed.[/green]")
        logger.info("Nginx is already installed")
        logger.debug(
            f"install_nginx() completed in {time.time() - start_time:.2f}s")
        return True

    rprint("[yellow]⚠️  Nginx is not installed on this system.[/yellow]")
    console.print("Do you want to install it? [y/n]", style="bold cyan")
    choice = Prompt.ask("")

    if choice.lower() == "y":
        rprint("🚀 [blue]Installing Nginx...[/blue]")
        if run_command("sudo apt-get update && sudo apt-get install -y nginx"):
            rprint("[green]✅ Nginx installed successfully![/green]")
            logger.info("Nginx installed successfully")
            logger.debug(
                f"install_nginx() completed in {time.time() - start_time:.2f}s")
            return True
        else:
            rprint("[red]❌ Failed to install Nginx[/red]")
            logger.error("Failed to install Nginx")
            logger.debug(
                f"install_nginx() completed in {time.time() - start_time:.2f}s (error)")
            return False
    else:
        rprint("[red]Nginx installation was refused. Aborting.[/red]")
        logger.warning("Nginx installation refused by user")
        sys.exit(1)


def install_modsecurity() -> bool:
    """
    Install ModSecurity (Debian/Ubuntu). Idempotent, checks first if it's already installed.
    """
    start_time = time.time()

    if is_modsecurity_installed():
        rprint("[green]✅ ModSecurity is already installed.[/green]")
        logger.info("ModSecurity is already installed")
        logger.debug(
            f"install_modsecurity() completed in {time.time() - start_time:.2f}s")
        return True

    rprint("🚀 [blue]Installing ModSecurity...[/blue]")
    if run_command("sudo apt-get update && sudo apt-get install -y libnginx-mod-security2 git"):
        rprint("[green]✅ ModSecurity installed successfully![/green]")
        logger.info("ModSecurity installed successfully")
        logger.debug(
            f"install_modsecurity() completed in {time.time() - start_time:.2f}s")
        return True
    else:
        rprint("[red]❌ Failed to install ModSecurity[/red]")
        logger.error("Failed to install ModSecurity")
        logger.debug(
            f"install_modsecurity() completed in {time.time() - start_time:.2f}s (error)")
        return False


def configure_modsecurity(profile_name: str, disable_rules=None, enable_rules=None):
    """
    Configure ModSecurity using a chosen profile.
    - disable_rules / enable_rules are lists of rule IDs to disable/enable.
    """
    start_time = time.time()

    modsec_conf = "/etc/nginx/modsecurity.conf"
    crs_repo = "/etc/nginx/modsec/coreruleset"

    # Clone OWASP CRS if not already present (idempotent)
    if not os.path.isdir(crs_repo):
        run_command(
            f"sudo git clone https://github.com/coreruleset/coreruleset.git {crs_repo}")
        run_command(
            f"sudo mv {crs_repo}/crs-setup.conf.example {crs_repo}/crs-setup.conf")

    if profile_name not in PROFILES:
        rprint(f"[red]❌ Unknown profile {profile_name}. Aborting.[/red]")
        logger.error(f"Unknown profile {profile_name}.")
        sys.exit(1)

    rules = PROFILES[profile_name]["rules"].copy()

    # Disable rules with SecRuleUpdateActionById
    if disable_rules:
        for rule_id in disable_rules:
            logger.debug(f"Disabling rule ID {rule_id}")
            rules.append(f"SecRuleUpdateActionById {rule_id} \"nolog,pass\"")

    # Enable rules with SecRuleUpdateActionById
    if enable_rules:
        for rule_id in enable_rules:
            logger.debug(f"Enabling rule ID {rule_id}")
            rules.append(f"SecRuleUpdateActionById {rule_id} \"deny,log\"")

    # Write the configuration file
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

        # Check if "modsecurity on;" is already in /etc/nginx/nginx.conf
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
            f"[green]✅ ModSecurity configured with the [bold]{profile_name}[/bold] profile.[/green]")
        logger.info(f"ModSecurity configured with the {profile_name} profile.")
        logger.debug(
            f"configure_modsecurity() completed in {time.time() - start_time:.2f}s")

    except Exception as e:
        rprint(f"[red]❌ Error while configuring ModSecurity: {e}[/red]")
        logger.exception("Exception while configuring ModSecurity")
        logger.debug(
            f"configure_modsecurity() completed in {time.time() - start_time:.2f}s (error)")
        sys.exit(1)

# ------------------------------------------------------------------------------
# Signal Handling (Ctrl + C)
# ------------------------------------------------------------------------------


def signal_handler(sig, frame):
    rprint(
        "\n[bold red]❗ Interruption (Ctrl + C) detected. Exiting the script.[/bold red]")
    logger.warning("Script interrupted by Ctrl + C")
    sys.exit(1)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# ------------------------------------------------------------------------------
# Main Entry Point
# ------------------------------------------------------------------------------


def main():
    """
    Main script to install/configure Nginx and ModSecurity.
    """
    parser = argparse.ArgumentParser(
        description="Idempotent script for installing and configuring Nginx + ModSecurity."
    )
    parser.add_argument(
        "--profile",
        type=str,
        default=os.getenv("MODSEC_PROFILE", "basic"),
        help="ModSecurity profile choice (basic, strict, paranoid)."
    )
    parser.add_argument(
        "--disable-rules",
        nargs='*',
        default=None,
        help="List of rule IDs to disable."
    )
    parser.add_argument(
        "--enable-rules",
        nargs='*',
        default=None,
        help="List of rule IDs to re-enable (deny,log)."
    )
    args = parser.parse_args()

    profile = args.profile
    disable_rules = args.disable_rules
    enable_rules = args.enable_rules

    rprint("[bold magenta]Welcome to the ModSecurity installation script for Nginx![/bold magenta] 🎉")
    logger.info("Starting the ModSecurity installation script")

    # 1) Check or install Nginx
    if not install_nginx():
        sys.exit(1)  # Could not install, exit

    # 2) Check or install ModSecurity
    if not install_modsecurity():
        sys.exit(1)  # Could not install, exit

    # 3) Configure ModSecurity according to the chosen profile
    configure_modsecurity(profile, disable_rules, enable_rules)

    rprint("[bold green]✨ All done![/bold green]")
    logger.info("Installation and configuration completed successfully.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Script interrupted by Ctrl+C")
        sys.exit(0)
