"""Chemins et constantes globales du backend."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
VMS_FILE = DATA_DIR / "vms.json"
SETTINGS_FILE = DATA_DIR / "settings.json"

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
