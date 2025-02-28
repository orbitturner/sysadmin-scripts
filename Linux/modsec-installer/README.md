# Installation et Configuration Automatisées de Nginx + ModSecurity

Ce projet fournit un **script Python idempotent** permettant :

1. **D’installer** et **configurer** [Nginx](https://nginx.org) et [ModSecurity](https://modsecurity.org) sous Debian/Ubuntu.  
2. **D’activer** et **de personnaliser** les règles de sécurité ModSecurity via différents profils (ex : `basic`, `strict`, `paranoid`).  
3. De **désactiver / activer** certaines règles spécifiques.  
4. De **logger** (via [Loguru](https://pypi.org/project/loguru/)) les détails et la **durée** (en secondes) de chaque opération principale.  
5. D’avoir une sortie **colorée** et “fancy” via [Rich](https://pypi.org/project/rich).

## Sommaire

- [Prérequis](#prérequis)  
- [Installation](#installation)  
  - [1. Cloner le dépôt](#1-cloner-le-dépôt)  
  - [2. Créer un environnement virtuel (venv)](#2-créer-un-environnement-virtuel-venv)  
  - [3. Installer les dépendances](#3-installer-les-dépendances)  
- [Configuration](#configuration)  
  - [Via un fichier `.env`](#via-un-fichier-env)  
  - [Via paramètres en ligne de commande (CLI)](#via-paramètres-en-ligne-de-commande-cli)  
- [Utilisation](#utilisation)  
  - [Exemples de commandes](#exemples-de-commandes)  
- [Logs & Mesures de performances](#logs--mesures-de-performances)  
- [Personnalisation](#personnalisation)  
- [License](#license)

---

## Prérequis

- Distribution **Debian/Ubuntu** (ou dérivée) disposant de `apt-get` pour installer Nginx et ModSecurity.  
- **Python 3.7+** recommandé.  
- Accès **root** ou **sudo** pour installer/configurer des paquets système (Nginx, ModSecurity).  
- Outils `git` pour cloner les règles [OWASP Core Rule Set (CRS)](https://github.com/coreruleset/coreruleset).

---

## Installation

### 1. Cloner le dépôt

```bash
git clone https://github.com/votre_compte/mon_projet_modsec.git
cd mon_projet_modsec
```

Adaptez l’URL de votre dépôt selon votre configuration.

### 2. Créer un environnement virtuel (venv)

```bash
python3 -m venv venv
source venv/bin/activate
```

Sous Windows (PowerShell) :

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Installer les dépendances

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Configuration

### Via un fichier `.env`

Vous pouvez définir certaines variables d’environnement dans un fichier `.env` (situé à la racine du projet). Par exemple :

```ini
# .env
MODSEC_PROFILE=basic
```

- `MODSEC_PROFILE` : Définit le profil de règles ModSecurity (ex : `basic`, `strict`, `paranoid`).  

> **Remarque** : Le script lit ces variables via [python-dotenv](https://pypi.org/project/python-dotenv/).  

### Via paramètres en ligne de commande (CLI)

Les **paramètres CLI** permettent de surcharger ou de compléter les valeurs du `.env`. Exemple :

- `--profile <nom>` : pour choisir un profil ModSecurity.  
- `--disable-rules <ID1> <ID2> ...` : désactive des règles ModSecurity existantes par ID.  
- `--enable-rules <ID1> <ID2> ...` : réactive certaines règles.

Exemples :

```bash
# Profil "strict", désactivation des règles 1001 et 1002
./install_modsec.py --profile strict --disable-rules 1001 1002

# Profil "paranoid", activation de la règle 2001
./install_modsec.py --profile paranoid --enable-rules 2001
```

---

## Utilisation

1. **Activer** votre environnement virtuel (si ce n’est pas déjà fait).  
2. **Lancer** le script :

```bash
python install_modsec.py
```

ou

```bash
./install_modsec.py
```

Si vous avez rendu le script exécutable (`chmod +x install_modsec.py`).

Le script :

1. Vérifie si **Nginx** est déjà installé (via `which nginx`).  
2. Vérifie si **ModSecurity** (`dpkg -s libnginx-mod-security2`) est déjà installé.  
3. Installe ce qui manque, si vous y consentez.  
4. Configure ModSecurity avec le **profil** (ex : `basic`) et adapte la configuration Nginx en conséquence.  
5. Affiche un **résumé** en fin d’exécution.

---

### Exemples de commandes

- **Installation & configuration par défaut** :  
  ```bash
  ./install_modsec.py
  ```
  Utilise le profil défini dans le `.env` ou le **profil “basic”** par défaut.

- **Passage en mode "strict" + désactivation de certaines règles** :  
  ```bash
  ./install_modsec.py --profile strict --disable-rules 1001 1002
  ```

- **Passage en mode "paranoid" + réactivation d’une règle** :  
  ```bash
  ./install_modsec.py --profile paranoid --enable-rules 2001
  ```

---

## Logs & Mesures de performances

- Le script génère un fichier de logs **`install_modsec.log`** (rotation automatique à 5 MB, compression au format zip) grâce à **Loguru**.  
- Les logs incluent :
  - Les **actions** effectuées (installation Nginx/ModSecurity, configuration, etc.).  
  - Les **erreurs** potentielles (y compris stacktrace en cas d’exception).  
  - Les **durées** (mesures de performances) de chaque opération principale (installation, configuration), logguées au niveau **DEBUG**.  
    - Exemple :  
      ```
      DEBUG - install_nginx() terminé en 2.53s
      DEBUG - configure_modsecurity() terminé en 1.22s
      ```  
- Pour voir ces messages de debug dans la console, vous pouvez **augmenter le niveau de verbosité** :

```bash
export LOGURU_LEVEL=DEBUG
./install_modsec.py
```

---

## Personnalisation

- **Dépôts et versions** : Pour un autre OS (CentOS, Fedora, etc.), adaptez la logique d’installation (`yum`, `dnf`) et la détection de paquets (ex : `rpm -q ...`).  
- **Profils de configuration** : Dans le fichier `install_modsec.py`, le dictionnaire `PROFILES` contient vos règles de base. Vous pouvez **ajouter**, **modifier** ou **supprimer** des règles en fonction de vos besoins.  
- **Gestion d’erreurs** : Vous pouvez renforcer la stratégie de rollback (sauvegarder/restaurer l’ancien `nginx.conf`, etc.).  
- **Logs** : Personnalisez le format Loguru, le chemin d’accès au fichier log, la stratégie de rotation, etc.

---

## License

Ce projet est distribué sous licence [MIT](./LICENSE) (ou la licence de votre choix).  
Vous êtes libres de le **modifier**, de le **redistribuer**, et de l’**améliorer**.  

---

**Bon déploiement !**  
Pour toute question ou suggestion, ouvrez une **issue** ou proposez une **Pull Request**.