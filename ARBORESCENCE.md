# Arborescence

```
homelab-vm-manager/
├── start.sh                      Démarre backend + frontend (PID, reset logs)
├── stop.sh                       Arrête les deux services via PID
├── restart.sh                    stop puis start
├── README.md                     Guide d'install copier-coller (non-dev)
├── .env.example                  Ports optionnels
├── .gitignore
├── systemd/
│   ├── homelab-backend.service   Service systemd backend (Restart=always)
│   └── homelab-frontend.service  Service systemd frontend (Restart=always)
├── backend/
│   ├── requirements.txt          Dépendances Python
│   ├── data/                     Stockage JSON (vms, settings, history) — créé au runtime
│   └── app/
│       ├── main.py               Point d'entrée FastAPI, monte les routers, lifespan scheduler
│       ├── ws.py                 Flux SSE des logs de provisioning (/api/jobs/{id}/stream)
│       ├── core/                 Briques transverses (shared)
│       │   ├── config.py         Chemins, constantes réseau/Netdata, settings par défaut
│       │   ├── store.py          Lecture/écriture JSON thread-safe (vms, settings, history)
│       │   ├── events.py         Bus d'événements en mémoire (pont thread -> SSE temps réel)
│       │   ├── secrets.py        Isolation des secrets (seal/reveal) — point de branchement chiffrement
│       │   ├── ssh_client.py     Session SSH Paramiko (run + exec_stream live), test de connexion
│       │   └── jobs.py           Registre de jobs + files d'événements pour logs live
│       ├── vms/                  Domaine VM (cœur métier)
│       │   ├── models.py         Schémas Pydantic VM (config, infos système), helpers ports/date
│       │   ├── repository.py     CRUD JSON des VMs (via secrets)
│       │   ├── routes.py         Endpoints HTTP du domaine VM (CRUD, sync, inspect, apt, provision)
│       │   ├── provisioning.py   Flux de provisioning étape par étape (live)
│       │   ├── proxmox_host.py   IP statique LXC via net0/pct set côté hôte Proxmox (source de vérité réseau)
│       │   ├── network.py        Utilitaires invité lecture seule (détection interface, attente reconnexion)
│       │   ├── teardown.py       Démantèlement à la suppression (en job, étapes live) : Netdata + MOTD + net0 DHCP
│       │   ├── sync.py           Vérifier & Synchroniser (idempotent : IP/MOTD/Netdata) + journalise
│       │   ├── sysinfo.py        Collecte SSH lecture seule : OS, noyau, archi, interface, IP
│       │   ├── package_manager.py Abstraction multi-OS (apt/dnf/pacman/zypper/apk) détectée en live
│       │   ├── updates.py        Comptage/application des MAJ, délègue au package_manager
│       │   ├── maintenance.py    Actions paquets à la demande, sortie live + état en cours->fini
│       │   ├── auto_sync.py      Resync auto des VMs sur modification d'un paramètre resyncable
│       │   ├── updates_routes.py Endpoints page Mises à jour (aperçu, machines, run-now)
│       │   └── status.py         Ping ICMP et rafraîchissement online/offline
│       ├── history/              Journal d'événements (scans, resync) avec cycle de vie
│       │   ├── models.py         HistoryEvent : kind, reason, mode, status (running->final)
│       │   ├── repository.py     record / update_event (rediffusé sur le bus) / list filtrée
│       │   └── routes.py         Lecture filtrable + flux SSE temps réel (/api/history/stream)
│       ├── netdata/
│       │   ├── streaming.py      Install Netdata + config streaming enfant + lecture GUID/hostname
│       │   └── parent.py         Déclaration/purge du nœud côté parent Netdata
│       ├── motd/
│       │   ├── render.py         Rendu du template à balises dynamiques
│       │   ├── apply.py          Écriture/lecture du MOTD sur la VM
│       │   └── routes.py         Endpoints template + aperçu live (déclenche resync auto)
│       ├── settings/
│       │   └── routes.py         Endpoints paramètres globaux (réarme scheduler, déclenche resync)
│       └── schedule/
│           └── daily.py          Scheduler APScheduler (scan quotidien, journalisé en cours->fini)
└── frontend/
    ├── package.json              Dépendances React/Vite (+ simple-icons pour les logos OS)
    ├── vite.config.js            Proxy /api et /ws vers le backend
    ├── index.html
    └── src/
        ├── main.jsx              Bootstrap React + Router + import fonts Geist
        ├── App.jsx               Layout, sidebar, transitions de route, LiveProvider + ToastStack
        ├── api/client.js         Wrappers fetch + flux SSE (job + historique temps réel)
        ├── styles/global.css     Design system à tokens (clean-minimal × bento-saas), dark only
        ├── components/
        │   ├── motion.js         Variants Framer partagés (stagger, rise, page, hover)
        │   ├── icons.jsx         Jeu d'icônes inline (stroke unique, sans dépendance)
        │   ├── AnimatedNumber.jsx  Compteur count-up au montage (KPI)
        │   ├── Badges.jsx        Badges type (bleu/orange) et statut (dot online pulsé)
        │   ├── HistoryBadges.jsx Badges du journal : opération, mode, raison, statut (En cours pulsé)
        │   ├── OsLogo.jsx        Logo OS réel (simple-icons, bundlé local, repli Tux)
        │   ├── relativeTime.js   Horodatage ISO -> « il y a 3 min »
        │   ├── TypeSelector.jsx  Sélecteur Standard/Essentielle visuel + hover lift
        │   ├── ProvisionConsole.jsx  Terminal live + barre de progression animée
        │   ├── ConfirmDialog.jsx Confirmation custom (remplace window.confirm natif)
        │   ├── ProgressDialog.jsx Modale de progression live sur job SSE (ex: suppression)
        │   └── live/
        │       ├── LiveContext.jsx  Flux SSE global : version (refresh pages) + toasts gatés
        │       └── ToastStack.jsx   Notifications bas-droite animées (Framer) + redirection filtrée
        └── pages/
            ├── Dashboard.jsx     Compteurs + tableau VMs (logo OS, dernière activité, temps réel)
            ├── AddVM.jsx         Formulaire + test SSH + provisioning live
            ├── VMDetail.jsx      Fiche : système (infos+logo+MAJ), config, sync, maintenance, suppression
            ├── Updates.jsx       Planification, machines surveillées, historique filtrable temps réel
            ├── Motd.jsx          Éditeur MOTD + aperçu live
            └── Settings.jsx      Paramètres globaux (SSH, Netdata, MOTD, notifications)
```
