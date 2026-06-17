# STATE — HomeLab VM Manager

## Statut global
Application complète et lançable. Backend importé et testé en runtime (health,
settings, CRUD VM, aperçu MOTD OK). Frontend buildé sans erreur (Vite).

## Ce qui est livré
- **Backend FastAPI** : 9 fonctionnalités câblées.
  - Ajout VM + test SSH + provisioning séquentiel avec logs live (WebSocket).
  - Switch réseau netplan (ens18) + attente reconnexion sur IP statique.
  - Cas « déjà en statique » géré (dhcp_ip vide → saute les étapes réseau).
  - Types Standard (MAJ auto) / Essentielle (MAJ notifiées seulement).
  - Scheduler quotidien APScheduler (heure configurable, réarmé au changement).
  - MOTD à balises dynamiques, dont {{VM_PORT_<N>}} pour N'IMPORTE quel port.
  - Vérifier & Synchroniser idempotent (IP / MOTD / Netdata, ne touche que l'écart).
  - Suppression manuelle (désactive streaming si online, distingue online/offline).
  - Streaming Netdata enfant via stream.conf + clé partagée.
- **Frontend React/Vite** (français) : Dashboard, Ajout, Détail/Sync, MAJ, MOTD
  (aperçu live), Paramètres. Thème sombre, bleu (Standard) / orange (Essentielle).
- **Stockage** : 2 fichiers JSON (vms, settings), module store thread-safe.
- **Secrets** : isolés dans core/secrets (seal/reveal identité aujourd'hui).
- Scripts start/stop/restart, services systemd, README copier-coller, docs.

## Décisions notables
- Frontend en JSX (pas TS) : brief impose « React (Vite) » + simplicité lab.
- Logs live via WebSocket + thread (Paramiko bloquant), pas SSE.
- Passerelle réseau déduite du /24 de l'IP statique (`x.y.z.1`).
- Versions de deps en planchers (`>=`) : Python 3.14 sur la machine de build,
  les versions épinglées n'avaient pas de wheels.

## Points à valider sur le terrain (non testables hors vraie VM)
- Provisioning bout-en-bout (SSH réel, netplan apply, kickstart Netdata).
- `sudo -S` avec le mot de passe SSH suppose un user sudoer ; à confirmer en lab.

## Hors scope (signalé, non implémenté — conforme au brief)
- Multi-OS, auth de l'app, chiffrement (au-delà du module d'isolation), base de
  données, clés SSH, tests automatisés.
