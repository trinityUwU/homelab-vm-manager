"""Chemins et constantes globales du backend."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
VMS_FILE = DATA_DIR / "vms.json"
SETTINGS_FILE = DATA_DIR / "settings.json"
HISTORY_FILE = DATA_DIR / "history.json"

# Plafond du journal d'événements (scan / sync) — au-delà, on tronque le plus ancien.
HISTORY_MAX_EVENTS = 1000

# Interface réseau standard des VMs Proxmox.
NET_INTERFACE = "ens18"
# Parent Netdata central du homelab.
NETDATA_PARENT = "192.168.1.103:19999"
NETDATA_PORT = 19999

# Valeurs par défaut écrites au premier lancement si settings.json est absent.
DEFAULT_SETTINGS = {
    "ssh_user": "debian",
    "ssh_password": "",
    "netdata_parent_url": NETDATA_PARENT,
    "netdata_api_key": "",
    "daily_check_enabled": True,
    "daily_check_hour": 3,
    "daily_check_minute": 0,
    # Resynchronise automatiquement les VMs concernées quand un paramètre
    # resyncable (MOTD, nom/ligne du lab) change. Effet de bord SSH — désactivable.
    "auto_resync_on_config_change": True,
    # Notifications toast en bas à droite quand une machine est mise à jour / resync.
    "notifications_enabled": True,
    "lab_name": "HomeLab",
    "lab_line": "Géré par HomeLab VM Manager",
    "motd_template": (
        "===============================================\n"
        "  {{LAB_NAME}} — {{VM_NAME}}\n"
        "  {{LAB_LINE}}\n"
        "-----------------------------------------------\n"
        "  IP        : {{VM_IP}}\n"
        "  Installée : {{INSTALL_DATE}}\n"
        "  SSH       : port {{VM_PORT_22}}\n"
        "===============================================\n"
    ),
}
