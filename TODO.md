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

## À valider sur le terrain — flux net0 (priorité, session 2026-07-01)

### Le fix pct set net0 tient après reboot
1. Renseigner l'hôte Proxmox + creds SSH root dans Paramètres.
2. Ajouter un LXC (VMID + IP DHCP + IP statique cible) et provisionner.
3. Confirmer la reconnexion sur l'IP statique juste après le provisioning.
4. `pct config <vmid>` sur l'hôte : `net0` contient bien `ip=<static>/24,gw=...`.
5. Reboot le conteneur (`pct reboot <vmid>` ou depuis le conteneur).
6. **Vérif clé** : le conteneur répond toujours sur l'IP statique, `ip a` dedans
   ne montre plus qu'une seule IPv4 (plus de DHCP en parallèle).

### Teardown restaure bien le DHCP net0
1. Supprimer une VM provisionnée depuis l'app.
2. `pct config <vmid>` sur l'hôte : `net0` repasse à `ip=dhcp`, plus de `gw=`.
3. Reboot le conteneur : reprend bien une IP DHCP normale.

### Non-régression (déjà en attente)
- [ ] Scan/upgrade réels sur un OS non-apt (Fedora/Arch/openSUSE/Alpine)
- [ ] Comportement des commandes de comptage MAJ par gestionnaire (dnf/zypper/apk affinables)

## Backlog (hors scope actuel, à décider)
- [ ] Chiffrement des mots de passe (module core/secrets prêt à l'accueillir)
- [ ] Build de production du frontend servi par le backend (au lieu de vite dev)
- [ ] Auto-découverte du VMID (`pct list` + matching) si la saisie manuelle
      devient pénible à l'usage
