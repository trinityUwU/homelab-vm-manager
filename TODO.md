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

## À valider sur le terrain
- [ ] Provisioning bout-en-bout sur une VM Debian neuve (SSH -> réseau -> Netdata -> MOTD)
- [ ] Scan/upgrade réels sur un OS non-apt (Fedora/Arch/openSUSE/Alpine)
- [ ] Comportement des commandes de comptage MAJ par gestionnaire (dnf/zypper/apk affinables)

## Backlog (hors scope actuel, à décider)
- [ ] Chiffrement des mots de passe (module core/secrets prêt à l'accueillir)
- [ ] Build de production du frontend servi par le backend (au lieu de vite dev)
- [ ] Provisioning réseau multi-OS (actuellement Debian/ifupdown uniquement)
- [ ] Purge des anciennes configs réseau résiduelles
