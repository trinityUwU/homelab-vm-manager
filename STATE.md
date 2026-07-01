# STATE — HomeLab VM Manager

## Session du 2026-07-01 (suite 2) — retour du support QEMU en parallèle du LXC

Revirement sur la décision de scope du matin même : Chris redemande finalement
de gérer les deux types de machine (le parc réel n'est pas *que* du LXC), avec
un sélecteur explicite à l'ajout plutôt qu'un abandon d'un des deux chemins.

**Modèle** : `MachineType` (`qemu` / `lxc` / `auto`) sur chaque VM. `auto`
n'existe qu'à la création — résolu en `qemu`/`lxc` dès la première connexion
du provisioning (signature d'interface invité : `eth0@ifNN` = paire veth = LXC,
sinon QEMU) puis persisté ; ne réapparaît jamais après. `vmid` redevient
optionnel dans le modèle, mais un `model_validator` Pydantic rejette toute VM
`machine_type=lxc` sans `vmid` (à la création **et** à la mise à jour — un
`model_copy` seul ne re-déclenche pas les validators, `repository.update_vm`
revalide explicitement le résultat fusionné).

**Deux chemins réseau, choisis par `machine_type` dans provisioning/sync/teardown** :
- **LXC** : inchangé depuis le pivot du matin — `net0` côté hôte Proxmox
  (`proxmox_host.py`, `pct set`), VMID requis.
- **QEMU** : chemin **restauré depuis l'historique git** (commit `039d234`,
  avant le pivot) — bascule IP statique côté invité (`/etc/network/interfaces`,
  durcissement cloud-init/NetworkManager/systemd-networkd), aucun VMID ni accès
  à l'hôte Proxmox nécessaire. Fonctions renommées publiques dans `network.py`
  (`restart_networking`, `write_resolv_conf`, avant préfixées `_`) pour être
  réutilisées proprement depuis `sync.py`.
- **Auto** : détection au premier provisioning uniquement. Si LXC détecté sans
  VMID, le provisioning s'arrête avec un message explicite (pas de blocage
  silencieux, pas de crash sur `pct` avec un VMID absent).

Frontend : `MachineTypeSelector.jsx` (3 options, style générique à accent CSS var
`--opt-accent`, réutilise le shell visuel de `TypeSelector` sans le coupler à
ses couleurs figées standard/essentielle). Champ VMID conditionnel dans
`AddVM.jsx`/`VMDetail.jsx` : requis si LXC, optionnel-conseillé si Auto, masqué
si QEMU.

**Non validé sur le terrain** : le chemin QEMU restauré n'a été rejoué que par
lecture de code (git history + tests unitaires de validation Pydantic), pas
sur une vraie VM Debian pure. Le mode Auto non plus. Voir `TODO.md`.

## Session du 2026-07-01 (suite) — validation terrain + pop-up custom

Alex a validé en conditions réelles le flux `pct set net0` du pivot LXC :
provisioning, reboot, IP statique qui tient, teardown -> retour DHCP propre.
Netdata (install + désinstall) confirmé OK aussi.

Remplacement des `confirm()`/`alert()` natifs du navigateur par des modales
custom (`components/ConfirmDialog.jsx`, `components/ProgressDialog.jsx`),
cohérentes avec le design system (dark, tokens `--bg-elevated`/`--r-lg`).
Utilisées pour : confirmation avant upgrade paquets, confirmation +
progression de la suppression d'une VM.

**Suppression passée en job SSE** (`teardown.run_deletion`, comme le
provisioning) au lieu d'un `DELETE` synchrone bloquant : le clic "Supprimer"
ouvrait une requête qui pouvait prendre plusieurs secondes sans aucun retour
visuel avant l'`alert()` final. Désormais `POST /api/vms/{id}/delete` renvoie
un `job_id`, et la modale affiche une vraie barre de progression + le libellé
de l'étape en cours (connexion, désinstall Netdata, purge MOTD, retour DHCP,
retrait du nœud parent, suppression de l'enregistrement) via SSE.

## Session du 2026-07-01 — pivot LXC (le parc réel n'est pas du QEMU Debian pur)

Test terrain en direct (Alex, Proxmox réel) : l'IP statique repartait en DHCP au
reboot malgré le fix du 22/06. Root cause trouvée après investigation web —
`pve-container` réinjecte la config réseau de l'invité **à chaque démarrage**
d'après `net0` (le paramètre `ip=` stocké côté hôte Proxmox), peu importe le
durcissement interne (cloud-init/NetworkManager/systemd-networkd). Aucun fix
côté invité ne peut tenir face à ça.

**Fix retenu** : faire porter l'IP statique par `net0` lui-même, via `pct set`
côté hôte Proxmox (hotplug, pas de reboot conteneur) — nouveau module
`vms/proxmox_host.py`. L'app a désormais besoin d'un accès SSH à l'**hôte**
Proxmox (Paramètres → « Hôte Proxmox »), distinct des creds de chaque conteneur.

**Décision de scope (validée avec Chris)** : le parc étant essentiellement des
LXC, le support VM QEMU Debian pure est abandonné plutôt que maintenu en double
chemin. `network.py` réduit aux utilitaires invité en lecture seule (détection
d'interface pour `sysinfo`, attente reconnexion) ; toute la logique d'écriture
réseau (ifupdown, cloud-init, harden_static_persistence) supprimée — obsolète
et activement contre-productive sur un LXC.

Chaque VM ajoutée doit désormais préciser son **VMID** Proxmox (`vmid: int`,
champ requis dans `VMBase`) — décision d'implémentation : champ manuel à
l'ajout plutôt qu'auto-découverte via `pct list` (matching par IP/hostname jugé
trop fragile pour un ajout au coup par coup).

Corrections annexes trouvées pendant le test : timeout de 60s trop court pour
le kickstart Netdata réel (passé à 300s dans `install_netdata`), erreur
tronquée à 300 caractères qui masquait la vraie cause (passée à 800 + log
complet), et idempotence ajoutée (`systemctl is-active netdata` avant de
relancer le kickstart — la VM de test était réutilisée entre essais).

**Non validé sur le terrain** : le nouveau flux `pct set net0` doit encore être
testé en conditions réelles par Alex (provisioning + reboot du conteneur).

## Session du 2026-06-22 — corrections terrain
Deux bugs remontés du terrain, corrigés (non rejouables hors vraie VM, à valider) :
- **IP static qui repassait en DHCP au reboot** → `network.harden_static_persistence()`
  appelée dans `apply_static_ip`. Neutralise les couches qui reprennent la main au boot :
  cloud-init (config réseau désactivée + fichiers purgés), NetworkManager (iface unmanaged),
  systemd-networkd (désactivé), `interfaces.d` résiduel (déclarations DHCP de l'iface retirées).
  Best effort conditionnel : sans risque sur une Debian ifupdown pure.
- **Résidus à la suppression d'une VM** (Netdata, MOTD, conf réseau restaient) → nouveau
  module `vms/teardown.py`. `teardown_machine()` désinstalle Netdata + purge `/etc/netdata`,
  vide `/etc/motd`, remet l'iface en DHCP (en dernier, coupe la session). Câblé dans
  `routes.delete` via `_teardown_remote` : le GUID est lu **avant** la purge de `/etc/netdata`
  (sinon impossible de retirer le nœud du parent). `disable_streaming` retiré (dead code).

## Statut global
Application complète et lançable. Backend validé en runtime (santé, settings, CRUD,
sync, scan, maintenance live, inspect système) — testé contre une vraie Pi (192.168.1.69).
Frontend buildé sans erreur (Vite). Provisioning bout-en-bout reste à valider sur une
VM Debian neuve (non rejouable depuis cette machine).

## Ce qui est livré

### Gestion VM (socle)
- Ajout VM (+ VMID Proxmox) + test SSH + provisioning séquentiel avec logs live (SSE).
- Switch réseau via `pct set net0` côté hôte Proxmox (IP statique persistante sur LXC), attente reconnexion.
- Types Standard (MAJ auto) / Essentielle (MAJ notifiées).
- MOTD à balises dynamiques ; Vérifier & Synchroniser idempotent (IP/MOTD/Netdata).
- Streaming Netdata enfant + purge du nœud parent à la suppression.

### Mises à jour & historique
- **Scan planifié** (APScheduler, heure configurable) + **« Lancer maintenant »**.
- **Exclusion par VM** du scan automatique (`scan_excluded`).
- **Journal d'événements** (`history/`) : scans et resync tracés avec date, machine,
  **mode** (MAJ auto / notifié), **raison** (planifié / modif config / manuel), statut.
- **Cycle de vie** des actions : chaque opération naît « en cours » puis passe à
  terminé / appliqué / erreur — visible en direct (accompagnement, anti double-clic).
- **Resync auto** sur modification d'un paramètre resyncable (MOTD/lab) — togglable.

### Temps réel & notifications
- **Bus d'événements** (`core/events`) + **flux SSE global** `/api/history/stream`.
- `LiveProvider` : rafraîchit Dashboard / Updates en direct, sans refresh manuel.
- **Toasts** bas-droite (Framer Motion) sur action terminée, avec redirection filtrée
  vers la fiche machine ou les Mises à jour. Activables depuis les Paramètres.

### Maintenance & polyvalence OS
- **Actions paquets à la demande** depuis la fiche : vérifier / tout mettre à jour,
  **sortie live** dans un terminal qui défile.
- **Abstraction multi-OS** (`package_manager`) : apt/dnf/pacman/zypper/apk détectés
  via le binaire présent. Scan, comptage et upgrade corrects sur chaque OS.
- Upgrade 100% non-interactif (apt : `--force-confdef/--force-confold`, etc.).
- **Infos système** (`sysinfo`, lecture seule) : OS + version, noyau, archi, interface,
  IP actuelle, indicateur de MAJ. Affichées dans la fiche, rafraîchies à l'ouverture.
- **Logos OS réels** (simple-icons, bundlé local) dans la fiche et le Dashboard.

### Frontend
- React/Vite (français), thème sombre, design system maison à tokens.
- Sélecteurs custom (chevron SVG), dernière activité en temps relatif.

## Décisions notables
- Frontend en JSX (pas TS) : brief impose « React (Vite) » + simplicité lab.
- Logs/maintenance live via SSE + thread (Paramiko bloquant), pas WebSocket.
- `exec_stream` sans PTY + `set_combine_stderr` : apt sort des lignes propres (pas de \r).
- Détection du gestionnaire par binaire présent, pas par os-release (plus fiable).
- Logos via simple-icons local (aucun CDN) — cohérent avec la souveraineté.
- Versions de deps en planchers (`>=`) côté Python (build sur Python 3.14).

## Points à valider sur le terrain (non testables hors vraie VM neuve)
- Provisioning bout-en-bout (SSH réel, switch réseau, kickstart Netdata, MOTD).
- Scan/upgrade réels sur OS non-apt (dnf/pacman/zypper/apk) : commandes posées,
  non rejouées faute de machines cibles.

## Hors scope (signalé, conforme au brief)
- Support VM QEMU Debian pure (abandonné le 01/07 au profit du tout-LXC), auth
  de l'app, chiffrement au-delà du module d'isolation, base de données, clés SSH,
  tests automatisés.
