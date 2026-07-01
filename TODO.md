# TODO

## Fait
- [x] Backend gestion VM (provisioning, réseau, sync, MOTD, Netdata) + scheduler
- [x] Frontend complet + thème sombre sémantique + design system maison
- [x] Catégorie Mises à jour : planification, machines surveillées, exclusion par VM
- [x] Journal d'événements (history/) avec mode + raison + cycle en cours->fini
- [x] Temps réel : bus d'événements + flux SSE global + rafraîchissement live
- [x] Notifications toast (Framer) avec redirection filtrée + toggle Paramètres
- [x] Resync auto sur modification de config (MOTD/lab), togglable
- [x] Maintenance paquets à la demande avec sortie live (terminal qui défile)
- [x] Polyvalence multi-OS (apt/dnf/pacman/zypper/apk) détectée en live
- [x] Upgrade non-interactif (force-conf), timeouts apt élargis
- [x] Infos système (OS, noyau, archi, interface, IP) + logos OS réels
- [x] Corrections : selects stylés, dernière activité relative, message timeout SSH
- [x] Teardown complet à la suppression (désinstall Netdata + MOTD)
- [x] ~~Fix persistance IP static au reboot (durcissement cloud-init/NM/networkd)~~
      — superseded : ne tenait pas sur un vrai LXC (Proxmox réinjecte sa config
      réseau à chaque boot, peu importe le durcissement invité).
- [x] **Pivot LXC** : IP statique portée par `net0` côté hôte Proxmox (`pct set`,
      module `vms/proxmox_host.py`), support VM QEMU Debian pure abandonné.
- [x] Netdata : timeout kickstart 60s -> 300s, erreur tronquée 300 -> 800 char + log,
      idempotence (skip si déjà actif).
- [x] **Validé sur le terrain (2026-07-01, Alex)** : flux `pct set net0` complet
      (provisioning, reboot, IP statique qui tient, teardown -> retour DHCP).
- [x] Pop-up natifs (`confirm`/`alert`) remplacés par des modales custom
      (`ConfirmDialog.jsx`, `ProgressDialog.jsx`), cohérentes avec le design system.
- [x] Suppression d'une VM passée en job SSE (comme provisioning/apt) : barre de
      progression réelle dans la modale au lieu d'un délai muet après le clic.

## En attente (non-régression, hors priorité actuelle)
- [ ] Scan/upgrade réels sur un OS non-apt (Fedora/Arch/openSUSE/Alpine)
- [ ] Comportement des commandes de comptage MAJ par gestionnaire (dnf/zypper/apk affinables)

## Backlog (hors scope actuel, à décider)
- [ ] Chiffrement des mots de passe (module core/secrets prêt à l'accueillir)
- [ ] Build de production du frontend servi par le backend (au lieu de vite dev)
- [ ] Auto-découverte du VMID (`pct list` + matching) si la saisie manuelle
      devient pénible à l'usage
