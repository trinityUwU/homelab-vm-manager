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
- [x] Fix persistance IP static au reboot (durcissement cloud-init/NM/networkd/interfaces.d)
- [x] Teardown complet à la suppression (désinstall Netdata + MOTD + retour DHCP)

## À valider sur le terrain — TESTS de la session 2026-06-22 (priorité)

### Bug 1 — l'IP static tient après reboot
1. Provisionner une VM Debian neuve via l'app (DHCP -> static).
2. Confirmer que la VM répond sur l'IP static juste après provisioning.
3. `reboot` la VM, attendre le redémarrage.
4. **Vérif clé** : la VM répond toujours sur l'IP **static** (pas DHCP).
5. Sur la VM : `ip -4 a` montre l'IP static ; `cat /etc/network/interfaces` = static.
6. Si cloud-init présent : `cat /etc/cloud/cloud.cfg.d/99-disable-network-config.cfg`
   existe et `/etc/netplan/50-cloud-init.yaml` n'a PAS été régénéré au boot.
7. Cas iface ≠ ens18 (eth0) : confirmer que la détection et le durcissement ont visé la bonne.

### Bug 2 — la machine est propre après suppression
1. Supprimer une VM provisionnée et **en ligne** depuis l'app.
2. Côté machine : `which netdata` absent, `ls /etc/netdata` absent,
   `systemctl status netdata` introuvable.
3. `cat /etc/motd` = vide.
4. `cat /etc/network/interfaces` = `dhcp` ; après reboot la VM reprend une IP DHCP.
5. Côté parent Netdata (192.168.1.103) : le nœud a disparu de l'interface.
6. Cas VM **hors-ligne** à la suppression : la suppression aboutit quand même,
   nœud retiré du parent via le GUID stocké (teardown distant sauté, normal).

### Non-régression (déjà en attente)
- [ ] Provisioning bout-en-bout sur une VM Debian neuve (SSH -> réseau -> Netdata -> MOTD)
- [ ] Scan/upgrade réels sur un OS non-apt (Fedora/Arch/openSUSE/Alpine)
- [ ] Comportement des commandes de comptage MAJ par gestionnaire (dnf/zypper/apk affinables)

## Backlog (hors scope actuel, à décider)
- [ ] Chiffrement des mots de passe (module core/secrets prêt à l'accueillir)
- [ ] Build de production du frontend servi par le backend (au lieu de vite dev)
- [ ] Provisioning réseau multi-OS (actuellement Debian/ifupdown uniquement)
