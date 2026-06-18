# Architecture

Monolithe modulaire : un backend FastAPI et un frontend React, organisés par
**domaine métier**, pas par couche technique. La structure se lit comme ce que
le produit fait : gérer des VMs, leur réseau, leur monitoring, leur MOTD.

## Carte des domaines (backend)

| Dossier | Responsabilité unique | Ne fait PAS |
|---|---|---|
| `core/` | Briques transverses réellement partagées : config, accès disque JSON, secrets, SSH, registre de jobs, bus d'événements. | Aucune logique métier VM/MOTD/Netdata. |
| `vms/` | Cœur métier : modèle VM, persistance, provisioning, réseau, sync, infos système, MAJ multi-OS, maintenance, statut, routes. | N'écrit pas le streaming Netdata ni le rendu MOTD lui-même (délègue). |
| `history/` | Journal des opérations (scans, resync) avec cycle de vie « en cours -> terminé/échec ». Lecture filtrable + flux SSE temps réel. | N'exécute aucune action ; reçoit des faits à enregistrer. |
| `netdata/` | Tout ce qui touche au monitoring Netdata côté enfant (install, streaming on/off, état). | Ne connaît pas le modèle VM ; reçoit des paramètres bruts. |
| `motd/` | Template MOTD : rendu des balises, application/lecture sur VM, routes d'édition. | Ne décide pas quand appliquer (c'est provisioning/sync qui appellent). |
| `settings/` | Paramètres globaux : lecture/écriture + réarmement du scheduler + déclenchement resync auto. | Ne stocke rien d'autre que les settings. |
| `schedule/` | Planification du scan quotidien (APScheduler). | N'implémente pas la logique de MAJ (délègue à `vms/updates`). |

## Définitions non ambiguës (contrat anti-pourrissement)

- **repository** : accès CRUD persistant d'un domaine (ici `vms/repository.py`).
  Seul endroit qui traduit objet ↔ stockage JSON pour les VMs.
- **store** (`core/store.py`) : couche disque brute, sans connaissance métier.
  `repository` s'appuie dessus ; rien d'autre n'écrit les fichiers JSON.
- **routes** : adaptation HTTP d'un domaine. Aucune logique métier lourde dedans,
  elles délèguent à provisioning / sync / repository.
- **provisioning** : orchestration séquentielle d'une première mise en service.
- **sync** : réconciliation idempotente d'une VM existante (ne corrige que l'écart).
  `provisioning` ≠ `sync` : le premier installe, le second répare sans rien casser.
- **package_manager** : abstraction des commandes paquets par OS (apt/dnf/pacman/zypper/apk),
  détectée via le binaire présent. `updates` et `maintenance` ne connaissent jamais une commande en dur.
- **sysinfo** : collecte SSH **lecture seule** (OS, noyau, archi, réseau). N'écrit rien sur la VM distante.
- **maintenance** : action paquet à la demande avec sortie live (Job/SSE) — exécute, `updates` mesure.
- **history.record / update_event** : un événement naît « en cours » puis évolue vers son état final ;
  chaque écriture est rediffusée sur le bus pour le temps réel.

## Règles de frontière entre modules

- Un domaine n'accède jamais aux fichiers internes d'un autre par effet de bord :
  `vms` appelle les fonctions publiques de `netdata/streaming` et `motd/render`,
  jamais l'inverse.
- Les secrets (mots de passe SSH) ne transitent que par `core/secrets`. Aucun
  autre fichier ne lit/écrit un mot de passe en clair directement sur disque.
  C'est le point de branchement unique pour ajouter du chiffrement plus tard.
- `core/` ne dépend d'aucun domaine. Les domaines dépendent de `core/`.

## Frontend

Découpage par page (une page = une fonctionnalité du brief) sous `pages/`, avec
des composants réutilisables sous `components/`. Toute la logique réseau est
centralisée dans `api/client.js` (un seul endroit qui connaît les routes du
backend et le WebSocket de logs).

## Flux notables

- **Provisioning / maintenance** : `routes` crée un `Job` (core/jobs), lance la tâche
  dans un thread (Paramiko est bloquant), qui pousse ses étapes dans la file du job ;
  le frontend lit ces étapes via le flux SSE `/api/jobs/{id}/stream`.
- **Scan quotidien** : `schedule/daily` ping chaque VM non exclue, applique les MAJ pour
  les Standard, notifie seulement pour les Essentielles. Jamais de suppression auto.
- **Temps réel** : toute opération journalise un événement via `history` ; `core/events`
  (bus en mémoire) le rediffuse aux clients abonnés au flux SSE `/api/history/stream`.
  Le frontend (`LiveProvider`) rafraîchit les pages et déclenche les toasts en direct.
- **Resync auto** : modifier le MOTD / nom / ligne du lab déclenche, via `vms/auto_sync`,
  une resync en arrière-plan des VMs concernées (raison « modification config »), si activé.
