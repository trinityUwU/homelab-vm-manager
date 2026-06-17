"""Rendu du template MOTD à balises dynamiques.

Balises gérées :
  {{VM_NAME}} {{VM_IP}} {{INSTALL_DATE}} {{LAB_NAME}} {{LAB_LINE}}
  {{VM_PORT_<N>}} : N'IMPORTE quel numéro de port. Vide si non configuré sur la VM.
"""
import re

from ..vms.models import VM, port_list

PORT_TAG = re.compile(r"\{\{VM_PORT_(\d+)\}\}")


def render(template: str, vm: VM, lab_name: str, lab_line: str) -> str:
    ports = set(port_list(vm.ports))
    # Balises de port : remplie si le port est configuré sur la VM, vide sinon.
    text = PORT_TAG.sub(lambda m: m.group(1) if m.group(1) in ports else "", template)
    replacements = {
        "{{VM_NAME}}": vm.name,
        "{{VM_IP}}": vm.static_ip,
        "{{INSTALL_DATE}}": vm.install_date or "—",
        "{{LAB_NAME}}": lab_name,
        "{{LAB_LINE}}": lab_line,
    }
    for tag, value in replacements.items():
        text = text.replace(tag, value)
    return text


def available_tags(vm: VM | None) -> list[str]:
    base = ["{{VM_NAME}}", "{{VM_IP}}", "{{INSTALL_DATE}}", "{{LAB_NAME}}", "{{LAB_LINE}}"]
    if vm is not None:
        base += [f"{{{{VM_PORT_{p}}}}}" for p in port_list(vm.ports)]
    else:
        base.append("{{VM_PORT_<N>}}")
    return base
