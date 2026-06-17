# TODO

## Fait
- [x] Backend complet (9 fonctionnalités) + scheduler + WebSocket logs
- [x] Frontend complet (6 pages) + thème sombre sémantique
- [x] Stockage JSON + module store + isolation des secrets
- [x] Scripts start/stop/restart + services systemd
- [x] README copier-coller + STATE/ARBORESCENCE/ARCHITECTURE
- [x] Validation : import backend runtime + build frontend

## À valider sur une vraie VM Debian (terrain)
- [ ] Provisioning bout-en-bout (SSH réel → netplan → reconnexion → Netdata → MOTD)
- [ ] Vérifier que l'user SSH est bien sudoer (sinon ajuster `sudo -S`)
- [ ] Vérifier & Synchroniser sur une VM déjà provisionnée
- [ ] Check quotidien déclenché à l'heure configurée

## Backlog (hors scope actuel, à décider)
- [ ] Chiffrement des mots de passe (le module core/secrets est prêt à l'accueillir)
- [ ] Build de production du frontend servi par le backend (au lieu de vite dev)
- [ ] Suppression propre des anciennes configs netplan DHCP résiduelles
