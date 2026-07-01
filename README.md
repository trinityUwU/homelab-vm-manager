# HomeLab VM Manager

Une web app pour gérer vos machines Proxmox de bout en bout — VM QEMU pures ou
conteneurs LXC — : les créer, les passer en IP fixe, brancher le monitoring
Netdata, suivre les mises à jour, poser un message d'accueil (MOTD) et les
supprimer quand vous n'en voulez plus. Elle tourne sur une VM ou un conteneur
dédié, qu'on appelle ici la « VM maître ».

Le guide part de zéro. Pas besoin d'être développeur : suivez les étapes dans
l'ordre et copiez-collez chaque commande dans un terminal sur la VM maître.

---

## À savoir avant de commencer

- À l'ajout d'une machine, vous choisissez son **type** : **LXC** (conteneur
  Proxmox), **QEMU** (VM Debian pure) ou **Auto** (détection à la première
  connexion). La manière de poser l'IP statique diffère selon le cas — voir plus
  bas — donc le bon choix évite des galères de configuration.
- **LXC** : l'app a besoin d'un accès SSH à **l'hôte Proxmox lui-même** (pas
  seulement au conteneur) : c'est lui qui pose l'IP statique via `pct set net0`,
  car un LXC ne peut pas la faire tenir tout seul (Proxmox réinjecte sa config
  réseau à chaque démarrage du conteneur). Ça se règle en Paramètres, section
  « Hôte Proxmox ». Chaque LXC doit préciser son **VMID** Proxmox (visible dans
  l'interface Proxmox ou via `pct list` sur l'hôte).
- **QEMU** : l'IP statique est posée directement dans la VM (`/etc/network/interfaces`),
  aucun accès à l'hôte Proxmox n'est nécessaire, pas de VMID à saisir.
- **Auto** : la détection se fait au premier provisioning (signature réseau de
  l'invité). Si la machine s'avère être un LXC et qu'aucun VMID n'a été
  renseigné, le provisioning s'arrête avec un message clair — remplissez alors
  le VMID sur la fiche et relancez. Renseignez-le d'emblée si vous savez déjà
  que c'est un LXC.
- Le Netdata central, celui qui regroupe le monitoring de tout le lab, tourne sur
  la machine `192.168.1.103`, son tableau de bord est sur le port `19999`.
- On se connecte aux VMs avec un identifiant et un mot de passe SSH, pas avec une
  clé.

---

## Étape 1 — Installer les outils

Ce bloc installe Python, l'outil `bun` (pour la partie web) et de quoi pinguer le
réseau. Copiez-collez-le tel quel.

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git curl unzip iputils-ping
curl -fsSL https://bun.sh/install | bash
source ~/.bashrc
```

Placez-vous ensuite dans le dossier du projet (s'il n'est pas encore sur la
machine, récupérez-le d'abord) :

```bash
cd ~/homelab-vm-manager
```

Installez le moteur (le backend) :

```bash
cd ~/homelab-vm-manager/backend
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

Puis l'interface (le frontend) :

```bash
cd ~/homelab-vm-manager/frontend
bun install
```

---

## Étape 2 — Créer la clé Netdata (à faire une seule fois)

Netdata raccorde chaque VM au tableau de bord central grâce à une clé partagée. On
la crée une fois sur la machine centrale `192.168.1.103`, et l'app la réutilise
ensuite pour toutes les VMs.

Connectez-vous sur `192.168.1.103` et générez la clé :

```bash
uuidgen
```

Vous obtenez quelque chose comme `3f7c1e9a-...`. Copiez cette ligne, on en a
besoin tout de suite. Ouvrez le fichier de configuration du streaming :

```bash
sudo nano /etc/netdata/stream.conf
```

Tout en bas, ajoutez ce bloc en remplaçant `VOTRE_CLE` par la clé que vous venez
de copier :

```
[VOTRE_CLE]
    enabled = yes
    default history = 3600
    health enabled by default = auto
```

Enregistrez (`Ctrl+O` puis `Entrée`, et `Ctrl+X` pour sortir), puis relancez
Netdata :

```bash
sudo systemctl restart netdata
```

Gardez la clé sous la main, vous la collerez dans l'app à l'étape 4.

---

## Étape 3 — Lancer l'application

Retournez sur la VM maître, à la racine du projet, et lancez :

```bash
cd ~/homelab-vm-manager
./start.sh
```

Ouvrez ensuite votre navigateur sur `http://localhost:8421`. Depuis un autre
ordinateur du réseau, remplacez `localhost` par l'IP de la VM maître :
`http://IP-DE-LA-VM-MAITRE:8421`.

Pour arrêter, `./stop.sh`. Pour redémarrer, `./restart.sh`.

---

## Étape 4 — Régler l'app au premier lancement

Allez dans la page Paramètres et remplissez :

1. L'hôte Proxmox (IP) + un utilisateur/mot de passe SSH root dessus — c'est lui
   qui applique l'IP statique des conteneurs LXC, indispensable avant leur
   provisioning (inutile si vous ne gérez que des VM QEMU).
2. L'identifiant et le mot de passe SSH par défaut de vos VMs. Le formulaire
   d'ajout se pré-remplira avec, ça évite de les retaper à chaque fois.
3. La clé de streaming Netdata, celle générée à l'étape 2.
4. L'heure de la vérification quotidienne (03h00 par défaut) et son activation.
5. Le nom du lab et la ligne perso qui s'afficheront dans le MOTD.

Enregistrez. Vous pouvez maintenant ajouter une machine depuis « Ajouter une VM »
(en choisissant son type — LXC/QEMU/Auto, et son VMID si LXC), tester la
connexion SSH, puis lancer le provisioning.

---

## Étape 5 — Laisser l'app tourner en permanence

Pour qu'elle redémarre toute seule après un reboot ou un plantage, on l'installe
comme service système. Les deux fichiers sont dans le dossier `systemd/`.

Vérifiez d'abord le chemin et l'utilisateur dans ces fichiers s'ils ne
correspondent pas à votre installation, puis copiez-les :

```bash
sudo cp ~/homelab-vm-manager/systemd/homelab-backend.service /etc/systemd/system/
sudo cp ~/homelab-vm-manager/systemd/homelab-frontend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now homelab-backend homelab-frontend
```

Contrôlez que les deux tournent :

```bash
sudo systemctl status homelab-backend homelab-frontend
```

Ils se relancent tout seuls si l'un plante (`Restart=always`) et au démarrage de
la machine.

---

## Quand ça coince

- Le test SSH renvoie « mauvais user/mot de passe ou IP injoignable » : revérifiez
  l'IP, l'identifiant et le mot de passe. La VM doit être allumée et joignable.
- Le provisioning reste bloqué sur « Attente de la VM » : c'est normal pendant
  quelques dizaines de secondes, le réseau coupe au moment où l'IP change. Si ça
  finit par échouer, l'IP fixe choisie est sans doute déjà prise par autre chose.
- Tout est tracé dans `logs/backend.log` et `logs/frontend.log` si vous voulez
  comprendre ce qui s'est passé.

---

## La stack

- Backend : Python + FastAPI, SSH via Paramiko, planificateur APScheduler.
- Frontend : React (Vite), interface en français.
- Stockage : deux fichiers JSON dans `backend/data/`, pas de base de données.
- Ports : `8420` pour le backend, `8421` pour le frontend.
