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
│   ├── data/                     Stockage JSON (vms.json, settings.json) — créé au runtime
│   └── app/
│       ├── main.py               Point d'entrée FastAPI, monte les routers, lifespan scheduler
│       ├── ws.py                 WebSocket de streaming des logs de provisioning
│       ├── core/                 Briques transverses (shared)
│       │   ├── config.py         Chemins, constantes réseau/Netdata, settings par défaut
│       │   ├── store.py          Lecture/écriture JSON thread-safe (source de vérité disque)
│       │   ├── secrets.py        Isolation des secrets (seal/reveal) — point de branchement chiffrement
│       │   ├── ssh_client.py     Session SSH Paramiko (mot de passe + sudo), test de connexion
│       │   └── jobs.py           Registre de jobs + files d'événements pour logs live
│       ├── vms/                  Domaine VM (cœur métier)
│       │   ├── models.py         Schémas Pydantic VM, helpers ports/date
│       │   ├── repository.py     CRUD JSON des VMs (via secrets)
│       │   ├── routes.py         Endpoints HTTP du domaine VM
│       │   ├── provisioning.py   Flux de provisioning étape par étape (live)
│       │   ├── network.py        Bascule IP statique netplan + attente nouvelle IP
│       │   ├── sync.py           Vérifier & Synchroniser (idempotent : IP/MOTD/Netdata)
│       │   ├── updates.py        Vérif et application des MAJ APT
│       │   ├── updates_routes.py Endpoint de la page Mises à jour
│       │   └── status.py         Ping ICMP et rafraîchissement online/offline
│       ├── netdata/
│       │   └── streaming.py      Install Netdata + config/désactivation streaming enfant
│       ├── motd/
│       │   ├── render.py         Rendu du template à balises dynamiques
│       │   ├── apply.py          Écriture/lecture du MOTD sur la VM
│       │   └── routes.py         Endpoints template + aperçu live
│       ├── settings/
│       │   └── routes.py         Endpoints des paramètres globaux
│       └── schedule/
│           └── daily.py          Scheduler APScheduler (check quotidien)
└── frontend/
    ├── package.json              Dépendances React/Vite
    ├── vite.config.js            Proxy /api et /ws vers le backend
    ├── index.html
    └── src/
        ├── main.jsx              Bootstrap React + Router
        ├── App.jsx               Layout, sidebar, routes
        ├── api/client.js         Wrappers fetch + ouverture WebSocket de job
        ├── styles/global.css     Thème sombre, couleurs sémantiques bleu/orange
        ├── components/
        │   ├── Badges.jsx        Badges type (bleu/orange) et statut (online/offline)
        │   ├── TypeSelector.jsx  Sélecteur Standard/Essentielle visuel
        │   └── ProvisionConsole.jsx  Terminal live + barre de progression
        └── pages/
            ├── Dashboard.jsx     Compteurs + tableau des VMs
            ├── AddVM.jsx         Formulaire + test SSH + provisioning live
            ├── VMDetail.jsx      Fiche : édition, sync, suppression
            ├── Updates.jsx       Page Mises à jour
            ├── Motd.jsx          Éditeur MOTD + aperçu live
            └── Settings.jsx      Paramètres globaux
```
