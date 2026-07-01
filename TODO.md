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
      — superseded pour le cas LXC : ne tenait pas sur un vrai LXC (Proxmox
      réinjecte sa config réseau à chaque boot). Restauré comme chemin QEMU
      (voir plus bas), toujours valide pour ce cas-là.
- [x] **Pivot LXC** : IP statique portée par `net0` côté hôte Proxmox (`pct set`,
      module `vms/proxmox_host.py`).
- [x] Netdata : timeout kickstart 60s -> 300s, erreur tronquée 300 -> 800 char + log,
      idempotence (skip si déjà actif).
- [x] **Validé sur le terrain (2026-07-01, Alex)** : flux `pct set net0` complet
      (provisioning, reboot, IP statique qui tient, teardown -> retour DHCP).
- [x] Pop-up natifs (`confirm`/`alert`) remplacés par des modales custom
      (`ConfirmDialog.jsx`, `ProgressDialog.jsx`), cohérentes avec le design system.
- [x] Suppression d'une VM passée en job SSE (comme provisioning/apt) : barre de
      progression réelle dans la modale au lieu d'un délai muet après le clic.
- [x] **Retour du support QEMU en parallèle du LXC** : sélecteur de type à
      l'ajout (LXC/QEMU/Auto), VMID requis seulement si LXC, chemin réseau
      invité restauré depuis l'historique git pour QEMU, détection auto par
      signature d'interface (`eth0@ifNN` = LXC) si mode Auto choisi.
- [x] **Heartbeat online/offline temps réel** : nouveau scheduler dédié
      (`schedule/liveness.py`, APScheduler, interval 5s) ping toutes les VMs
      en parallèle (`vms/status.check_liveness`), ne persiste/diffuse que les
      transitions d'état sur le bus d'événements existant. Le Dashboard se
      met à jour tout seul (shutdown/reboot détecté en quelques secondes) sans
      clic « Actualiser » — corrige le décalage remonté par Alex.

## À valider sur le terrain (priorité)
- [ ] **Chemin QEMU restauré** : provisioning + reboot + teardown sur une vraie
      VM Debian pure (aucune régression attendue vs l'ancien comportement
      pré-pivot, mais non rejoué en conditions réelles depuis sa réintégration).
- [ ] **Mode Auto** : ajouter une machine sans préciser son type, vérifier que
      la détection au provisioning tombe juste (LXC vs QEMU) et que le blocage
      "VMID manquant" s'affiche clairement si un LXC est détecté sans VMID.
- [ ] **Heartbeat** : shutdown puis boot d'une VM réelle, vérifier que le
      Dashboard bascule online/offline en quelques secondes sans rechargement
      manuel (validé par lecture de code + test unitaire, pas encore rejoué
      sur le parc réel).
- [ ] Changer le `machine_type` d'une VM déjà provisionnée depuis sa fiche puis
      relancer une synchro : vérifier qu'elle bascule proprement sur le nouveau
      chemin réseau (cas non testé, usage attendu rare).

## En attente (non-régression, hors priorité actuelle)
- [ ] Scan/upgrade réels sur un OS non-apt (Fedora/Arch/openSUSE/Alpine)
- [ ] Comportement des commandes de comptage MAJ par gestionnaire (dnf/zypper/apk affinables)

## Backlog (hors scope actuel, à décider)
- [ ] Chiffrement des mots de passe (module core/secrets prêt à l'accueillir)
- [ ] Build de production du frontend servi par le backend (au lieu de vite dev)
- [ ] Auto-découverte du VMID (`pct list` + matching) si la saisie manuelle
      devient pénible à l'usage
