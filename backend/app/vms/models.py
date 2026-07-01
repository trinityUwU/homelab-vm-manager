"""Schémas Pydantic du domaine VM."""
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, model_validator


class VMType(str, Enum):
    STANDARD = "standard"      # MAJ appliquées automatiquement.
    ESSENTIELLE = "essentielle"  # MAJ notifiées seulement, jamais appliquées.


class MachineType(str, Enum):
    QEMU = "qemu"  # VM Debian pure : IP statique posée côté invité (/etc/network/interfaces).
    LXC = "lxc"    # Conteneur Proxmox : IP statique posée côté hôte (net0, pct set).
    AUTO = "auto"  # Choix à la création seulement ; résolu en qemu/lxc dès la 1re connexion.


class VMBase(BaseModel):
    name: str
    machine_type: MachineType = MachineType.LXC
    vmid: int | None = None    # ID Proxmox (pct/qm config <vmid>) — requis si machine_type=lxc.
    static_ip: str
    ports: str = ""            # Champ libre, ex "22;80;5000". Modifiable après coup.
    vm_type: VMType = VMType.STANDARD
    ssh_user: str
    ssh_password: str

    @model_validator(mode="after")
    def _vmid_required_for_lxc(self) -> "VMBase":
        if self.machine_type == MachineType.LXC and self.vmid is None:
            raise ValueError("vmid requis quand machine_type=lxc")
        return self


class VMCreate(VMBase):
    # IP DHCP temporaire. Vide => la VM est déjà en IP statique (saute le switch réseau).
    dhcp_ip: str = ""


class VMUpdate(BaseModel):
    name: str | None = None
    machine_type: MachineType | None = None
    vmid: int | None = None
    static_ip: str | None = None
    ports: str | None = None
    vm_type: VMType | None = None
    ssh_user: str | None = None
    ssh_password: str | None = None
    scan_excluded: bool | None = None


class VM(VMBase):
    id: str
    dhcp_ip: str = ""
    provisioned: bool = False
    install_date: str | None = None
    last_seen_online: bool = False
    last_update_applied: str | None = None
    pending_updates: int = 0
    last_check: str | None = None
    netdata_guid: str | None = None  # MACHINE_GUID de l'enfant, pour le purger du parent.
    scan_excluded: bool = False      # Exclue du scan/MAJ automatique planifié.
    # Informations système collectées en SSH (lecture seule), dernières connues.
    os_id: str | None = None         # debian / ubuntu / fedora / arch / raspberrypi…
    os_name: str | None = None       # PRETTY_NAME (ex « Debian GNU/Linux 12 (bookworm) »).
    os_version: str | None = None    # VERSION_ID.
    kernel: str | None = None        # uname -r.
    arch: str | None = None          # uname -m (x86_64, aarch64…).
    net_interface: str | None = None # Interface réseau réelle (eth0, ens18…).
    current_ip: str | None = None    # IP active détectée sur l'interface.
    sysinfo_at: str | None = None    # Horodatage de la dernière collecte.


class TestSSHRequest(BaseModel):
    host: str
    ssh_user: str
    ssh_password: str


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def port_list(ports: str) -> list[str]:
    """Découpe le champ ports libre en numéros nettoyés."""
    raw = ports.replace(",", ";").split(";")
    return [p.strip() for p in raw if p.strip()]
