"""Schémas Pydantic du domaine VM."""
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class VMType(str, Enum):
    STANDARD = "standard"      # MAJ appliquées automatiquement.
    ESSENTIELLE = "essentielle"  # MAJ notifiées seulement, jamais appliquées.


class VMBase(BaseModel):
    name: str
    static_ip: str
    ports: str = ""            # Champ libre, ex "22;80;5000". Modifiable après coup.
    vm_type: VMType = VMType.STANDARD
    ssh_user: str
    ssh_password: str


class VMCreate(VMBase):
    # IP DHCP temporaire. Vide => la VM est déjà en IP statique (saute le switch réseau).
    dhcp_ip: str = ""


class VMUpdate(BaseModel):
    name: str | None = None
    static_ip: str | None = None
    ports: str | None = None
    vm_type: VMType | None = None
    ssh_user: str | None = None
    ssh_password: str | None = None


class VM(VMBase):
    id: str
    dhcp_ip: str = ""
    provisioned: bool = False
    install_date: str | None = None
    last_seen_online: bool = False
    last_update_applied: str | None = None
    pending_updates: int = 0
    last_check: str | None = None


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
